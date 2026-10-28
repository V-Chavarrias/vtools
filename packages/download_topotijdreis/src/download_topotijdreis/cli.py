#!/usr/bin/env python3
"""Download square Topotijdreis aerial-image crops for points in a CSV.

From a checkout of this repository, install the package and browser:

    python -m pip install .\\packages\\download_topotijdreis
    python -m playwright install chromium

Example:
    python -m download_topotijdreis --csv rkm_maas.csv \
        --years 2012 2020 --zoom 10 --size 512

The CSV coordinates must be in EPSG:28992 (RD New), which Topotijdreis accepts
directly in its satellite-view URL.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import time
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import (
    Browser,
    Page,
    Request,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


DEFAULT_SITE_URL = (
    "https://www.topotijdreis.nl/satelliet/2006/@136794,455874,3"
)
TILE_QUIET_SECONDS = 0.75
ATTRIBUTION_BAND_HEIGHT = 20


@dataclass(frozen=True)
class Location:
    row_number: int
    x: float
    y: float
    tag: str


class TileRequestTracker:
    def __init__(self) -> None:
        self.pending: Counter[str] = Counter()
        self.total_started = 0
        self.last_activity: float | None = None

    @staticmethod
    def _is_map_tile(request: Request) -> bool:
        return "/MapServer/tile/" in request.url

    def request_started(self, request: Request) -> None:
        if self._is_map_tile(request):
            self.pending[request.url] += 1
            self.total_started += 1
            self.last_activity = time.monotonic()

    def request_finished(self, request: Request) -> None:
        if not self._is_map_tile(request):
            return
        if self.pending[request.url] > 1:
            self.pending[request.url] -= 1
        elif self.pending[request.url] == 1:
            del self.pending[request.url]
        self.last_activity = time.monotonic()

    def wait_until_idle(
        self,
        page: Page,
        previous_count: int,
        page_url: str,
        timeout_seconds: float,
    ) -> None:
        deadline = time.monotonic() + timeout_seconds
        while True:
            now = time.monotonic()
            started_this_page = self.total_started > previous_count
            no_pending_tiles = not self.pending
            quiet = (
                self.last_activity is not None
                and now - self.last_activity >= TILE_QUIET_SECONDS
            )
            if started_this_page and no_pending_tiles and quiet:
                return
            if now >= deadline:
                pending_count = sum(self.pending.values())
                if not started_this_page:
                    detail = "no imagery tile requests were made"
                elif pending_count:
                    pending_urls = ", ".join(list(self.pending)[:2])
                    detail = (
                        f"{pending_count} imagery tile requests are still pending"
                        f" ({pending_urls})"
                    )
                else:
                    detail = "imagery tile requests did not settle"
                raise TimeoutError(
                    f"Timed out waiting for map imagery at {page_url}: {detail}."
                )
            page.wait_for_timeout(100)


def sanitize_tag(value: str) -> str:
    tag = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value.strip())
    return tag.strip(" .")


def read_locations(
    csv_path: Path,
    x_column: str,
    y_column: str,
    tag_column: str,
) -> list[Location]:
    required_columns = (x_column, y_column, tag_column)
    with csv_path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file, skipinitialspace=True)
        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header row: {csv_path}")
        reader.fieldnames = [name.strip() for name in reader.fieldnames]
        missing_columns = [
            name for name in required_columns if name not in reader.fieldnames
        ]
        if missing_columns:
            raise ValueError(
                f"CSV is missing required column(s): {', '.join(missing_columns)}"
            )

        locations: list[Location] = []
        for row_number, row in enumerate(reader, start=2):
            x_text = (row.get(x_column) or "").strip()
            y_text = (row.get(y_column) or "").strip()
            raw_tag = (row.get(tag_column) or "").strip()
            if not x_text or not y_text or not raw_tag:
                raise ValueError(
                    f"CSV row {row_number} has a blank coordinate or tag."
                )
            try:
                x = float(x_text)
                y = float(y_text)
            except ValueError as error:
                raise ValueError(
                    f"CSV row {row_number} has invalid coordinates: "
                    f"X={x_text!r}, Y={y_text!r}."
                ) from error
            if not math.isfinite(x) or not math.isfinite(y):
                raise ValueError(
                    f"CSV row {row_number} coordinates must be finite numbers."
                )

            tag = sanitize_tag(raw_tag)
            if not tag:
                raise ValueError(f"CSV row {row_number} has an unusable tag.")
            locations.append(Location(row_number, x, y, tag))

    if not locations:
        raise ValueError(f"CSV contains no data rows: {csv_path}")
    return locations


def satellite_base_url(site_url: str) -> tuple[str, str, str]:
    parsed = urlsplit(site_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("--site-url must be an absolute HTTP(S) URL.")

    path = parsed.path.rstrip("/")
    match = re.fullmatch(
        r"(?P<prefix>.*/satelliet)(?:/\d+/@[^/]+)?",
        path,
    )
    if match is None:
        raise ValueError(
            "--site-url must end in '/satelliet' or use the Topotijdreis "
            "satellite URL format '/satelliet/YEAR/@X,Y,ZOOM'."
        )
    return parsed.scheme, parsed.netloc, match.group("prefix")


def build_page_url(
    site_parts: tuple[str, str, str],
    year: int,
    x: float,
    y: float,
    zoom: int,
) -> str:
    scheme, netloc, prefix = site_parts
    path = f"{prefix}/{year}/@{x:.4f},{y:.4f},{zoom}"
    return urlunsplit((scheme, netloc, path, "", ""))


def save_square_image(
    screenshot_bytes: bytes,
    output_path: Path,
    size: int,
    attribution: str,
) -> None:
    with Image.open(BytesIO(screenshot_bytes)) as source:
        map_image = source.convert("RGB")
    if map_image.width < size or map_image.height < size:
        raise RuntimeError(
            f"Map viewport is only {map_image.width}x{map_image.height}; "
            f"cannot crop a {size}x{size} image."
        )

    left = (map_image.width - size) // 2
    top = (map_image.height - size) // 2
    square = map_image.crop((left, top, left + size, top + size))

    draw = ImageDraw.Draw(square)
    font = ImageFont.load_default()
    text_bounds = draw.textbbox((0, 0), attribution, font=font)
    text_width = text_bounds[2] - text_bounds[0]
    if text_width > size - 8:
        raise ValueError(
            f"Attribution does not fit in a {size}px image; increase --size."
        )

    band_top = size - ATTRIBUTION_BAND_HEIGHT
    draw.rectangle((0, band_top, size, size), fill="white")
    text_height = text_bounds[3] - text_bounds[1]
    text_y = band_top + (ATTRIBUTION_BAND_HEIGHT - text_height) // 2
    draw.text(
        (4, text_y - text_bounds[1]),
        attribution,
        fill="black",
        font=font,
    )
    square.save(output_path, format="PNG", optimize=True)


def output_path_for(
    output_dir: Path,
    location: Location,
    year: int,
    tag_counts: Counter[str],
) -> Path:
    duplicate_suffix = (
        f"_row{location.row_number}"
        if tag_counts[location.tag.casefold()] > 1
        else ""
    )
    return output_dir / f"{location.tag}{duplicate_suffix}_{year}.png"


def create_map_page(
    browser: Browser,
    viewport_size: int,
    navigation_timeout: float,
) -> tuple[Page, TileRequestTracker]:
    page = browser.new_page(
        viewport={"width": viewport_size, "height": viewport_size},
        device_scale_factor=1,
    )
    page.set_default_navigation_timeout(navigation_timeout * 1000)
    tracker = TileRequestTracker()
    page.on("request", tracker.request_started)
    page.on("requestfinished", tracker.request_finished)
    page.on("requestfailed", tracker.request_finished)
    return page, tracker


def download_topotijdreis(
    csv_path: str | Path,
    years: Iterable[int],
    output_dir: str | Path,
    *,
    site_url: str = DEFAULT_SITE_URL,
    zoom: int = 10,
    size: int = 512,
    x_column: str = "X",
    y_column: str = "Y",
    tag_column: str = "MODELKM",
    tile_timeout: float = 60,
    retries: int = 3,
    retry_delay: float = 5,
) -> list[Path]:
    """Download Topotijdreis image crops from a CSV.

    The CSV coordinates must be in EPSG:28992 (RD New). Existing output files
    are skipped. The returned paths contain one entry for every requested
    location/year output, including files that already existed.
    """
    if zoom < 0:
        raise ValueError("zoom must be zero or greater.")
    if size <= ATTRIBUTION_BAND_HEIGHT:
        raise ValueError(
            f"size must be greater than {ATTRIBUTION_BAND_HEIGHT} pixels."
        )
    if tile_timeout <= 0:
        raise ValueError("tile_timeout must be greater than zero.")
    if retries < 1:
        raise ValueError("retries must be at least one.")
    if retry_delay < 0:
        raise ValueError("retry_delay cannot be negative.")

    years = list(dict.fromkeys(years))
    if not years:
        raise ValueError("Provide at least one year with years.")

    csv_path = Path(csv_path)
    output_dir = Path(output_dir)
    locations = read_locations(csv_path, x_column, y_column, tag_column)
    site_parts = satellite_base_url(site_url)
    tag_counts = Counter(location.tag.casefold() for location in locations)
    output_dir.mkdir(parents=True, exist_ok=True)

    viewport_size = max(size + 512, 1024)
    completed: list[Path] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page: Page | None = None
        try:
            page, tracker = create_map_page(
                browser,
                viewport_size,
                tile_timeout,
            )
            map_surface = page.locator('[role="application"]')
            total = len(locations) * len(years)
            processed = 0
            failed: list[str] = []

            for location in locations:
                for year in years:
                    processed += 1
                    destination = output_path_for(
                        output_dir,
                        location,
                        year,
                        tag_counts,
                    )
                    if destination.exists():
                        print(f"[{processed}/{total}] Exists, skipping {destination}")
                        completed.append(destination)
                        continue

                    page_url = build_page_url(
                        site_parts,
                        year,
                        location.x,
                        location.y,
                        zoom,
                    )
                    for attempt in range(1, retries + 1):
                        tile_count_before = tracker.total_started
                        try:
                            page.goto(page_url, wait_until="domcontentloaded")
                            map_surface.wait_for(state="visible")
                            tracker.wait_until_idle(
                                page,
                                tile_count_before,
                                page_url,
                                tile_timeout,
                            )
                            page.wait_for_timeout(250)

                            selected_year = page.get_by_role(
                                "combobox",
                                name="Kies een jaar",
                            ).input_value()
                            if selected_year != str(year):
                                raise RuntimeError(
                                    f"Topotijdreis selected year {selected_year!r} "
                                    f"instead of {year} at {page_url}."
                                )

                            source_credit = page.locator(
                                ".esri-attribution__sources"
                            ).inner_text().strip()
                            powered_by = page.locator(
                                ".esri-attribution__powered-by"
                            ).inner_text().strip()
                            if not source_credit or not powered_by:
                                raise RuntimeError(
                                    f"Could not read map attribution at {page_url}."
                                )

                            save_square_image(
                                map_surface.screenshot(animations="disabled"),
                                destination,
                                size,
                                f"{source_credit} | {powered_by}",
                            )
                        except (PlaywrightTimeoutError, TimeoutError) as error:
                            page.close()
                            if attempt == retries:
                                message = f"{destination}: {error}"
                                failed.append(message)
                                print(f"[{processed}/{total}] Failed {message}")
                                page, tracker = create_map_page(
                                    browser,
                                    viewport_size,
                                    tile_timeout,
                                )
                                map_surface = page.locator('[role="application"]')
                                break

                            delay = retry_delay * attempt
                            print(
                                f"[{processed}/{total}] Retry "
                                f"{attempt + 1}/{retries} in {delay:g}s "
                                f"for {destination}: {error}"
                            )
                            time.sleep(delay)
                            page, tracker = create_map_page(
                                browser,
                                viewport_size,
                                tile_timeout,
                            )
                            map_surface = page.locator('[role="application"]')
                        else:
                            print(f"[{processed}/{total}] Saved {destination}")
                            completed.append(destination)
                            break
            if failed:
                details = "\n".join(f"  - {message}" for message in failed)
                raise RuntimeError(
                    f"Failed to download {len(failed)} image(s):\n{details}"
                )
        finally:
            if page is not None and not page.is_closed():
                page.close()
            browser.close()
    return completed


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download square Topotijdreis aerial-image crops centered on "
            "EPSG:28992 coordinates from a CSV."
        )
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path.cwd() / "rkm_maas.csv",
        help="Input CSV (default: ./rkm_maas.csv).",
    )
    parser.add_argument(
        "--site-url",
        default=DEFAULT_SITE_URL,
        help="Topotijdreis satellite URL, including the example URL's route.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd() / "images",
        help="Directory for PNG images (default: ./images).",
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2012, 2020],
        help="Years to download (default: 2012 2020).",
    )
    parser.add_argument(
        "--zoom",
        type=int,
        default=10,
        help="Topotijdreis zoom level (default: 10).",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=512,
        help="Output image width and height in pixels (default: 512).",
    )
    parser.add_argument("--x-column", default="X", help="CSV X column.")
    parser.add_argument("--y-column", default="Y", help="CSV Y column.")
    parser.add_argument(
        "--tag-column",
        default="MODELKM",
        help="CSV river-kilometer tag column.",
    )
    parser.add_argument(
        "--tile-timeout",
        type=float,
        default=60,
        help="Seconds to wait for each map's image tiles (default: 60).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Attempts for a map whose imagery times out (default: 3).",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=5,
        help="Base delay in seconds between map retries (default: 5).",
    )
    args = parser.parse_args(argv)
    if args.zoom < 0:
        parser.error("--zoom must be zero or greater.")
    if args.size <= ATTRIBUTION_BAND_HEIGHT:
        parser.error(
            f"--size must be greater than {ATTRIBUTION_BAND_HEIGHT} pixels."
        )
    if args.tile_timeout <= 0:
        parser.error("--tile-timeout must be greater than zero.")
    if args.retries < 1:
        parser.error("--retries must be at least one.")
    if args.retry_delay < 0:
        parser.error("--retry-delay cannot be negative.")
    if not args.years:
        parser.error("Provide at least one year with --years.")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    download_topotijdreis(
        args.csv,
        args.years,
        args.output_dir,
        site_url=args.site_url,
        zoom=args.zoom,
        size=args.size,
        x_column=args.x_column,
        y_column=args.y_column,
        tag_column=args.tag_column,
        tile_timeout=args.tile_timeout,
        retries=args.retries,
        retry_delay=args.retry_delay,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
