from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from pathlib import Path
import subprocess

import cdsapi


def _git_revision() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(Path(__file__).resolve().parent), "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def download_era5_data(
    variables: Iterable[str],
    years: Iterable[int | str],
    area: Sequence[float],
    output_root: str | Path,
) -> None:
    """Download ERA5 single-level reanalysis data from the CDS API.

    ``area`` uses the CDS order ``[North, West, South, East]``. Existing
    files are skipped, so a partially completed download can be resumed.
    """
    source_path = Path(__file__).resolve()
    print(
        f"Running {source_path.name} "
        f"(last modified: {datetime.fromtimestamp(source_path.stat().st_mtime)})"
    )
    git_hash = _git_revision()
    print(f"Git commit hash: {git_hash or 'unavailable'}")

    client = cdsapi.Client()
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    years = tuple(years)

    for variable in variables:
        variable_folder = output_root / variable
        variable_folder.mkdir(parents=True, exist_ok=True)

        for year in years:
            year_text = str(year)
            if len(year_text) != 4:
                raise ValueError(
                    f"Year {year} is not in the correct format (YYYY)."
                )

            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
                f": get variable {variable} from {year_text}"
            )
            output_file = variable_folder / f"{year_text}_{variable}.nc"

            if output_file.exists():
                print(f"File {output_file} already exists, skipping download.")
                continue

            print(f"Downloading {variable} data for {year_text} to {output_file}")
            client.retrieve(
                "reanalysis-era5-single-levels",
                {
                    "product_type": "reanalysis",
                    "variable": variable,
                    "year": year_text,
                    "month": [f"{month:02d}" for month in range(1, 13)],
                    "day": [f"{day:02d}" for day in range(1, 32)],
                    "time": [f"{hour:02d}:00" for hour in range(24)],
                    "format": "netcdf",
                    "area": area,
                },
                str(output_file),
            )
