import csv
from collections import Counter
from pathlib import Path

import pytest

from download_topotijdreis import (
    Location,
    build_page_url,
    cli,
    download_topotijdreis,
    output_path_for,
    read_locations,
    sanitize_tag,
    satellite_base_url,
)


def test_sanitize_tag_removes_path_and_control_characters() -> None:
    assert sanitize_tag('  river/point<>:"A\n  ') == "river_point____A"


def test_read_locations_parses_coordinates_and_tags(tmp_path: Path) -> None:
    csv_path = tmp_path / "locations.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["X", "Y", "MODELKM"])
        writer.writeheader()
        writer.writerow({"X": "136794.5", "Y": "455874", "MODELKM": "KM 1"})

    locations = read_locations(csv_path, "X", "Y", "MODELKM")

    assert locations == [Location(2, 136794.5, 455874.0, "KM 1")]


def test_read_locations_reports_missing_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "locations.csv"
    csv_path.write_text("X,Y\n1,2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required column"):
        read_locations(csv_path, "X", "Y", "MODELKM")


def test_satellite_url_is_normalized_and_rebuilt() -> None:
    parts = satellite_base_url(
        "https://www.topotijdreis.nl/satelliet/2020/@1,2,10"
    )

    assert build_page_url(parts, 2012, 136794.12345, 455874.5, 10) == (
        "https://www.topotijdreis.nl/satelliet/2012/@136794.1235,455874.5000,10"
    )


def test_output_path_adds_suffix_for_duplicate_tags(tmp_path: Path) -> None:
    location = Location(4, 1.0, 2.0, "A")
    counts = Counter({"a": 2})

    assert output_path_for(tmp_path, location, 2020, counts) == (
        tmp_path / "A_row4_2020.png"
    )


def test_python_downloader_validates_options_before_starting_browser(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="zoom"):
        download_topotijdreis(
            csv_path=tmp_path / "locations.csv",
            years=[2020],
            output_dir=tmp_path / "images",
            zoom=-1,
        )


def test_cli_parses_arguments_without_using_process_argv(tmp_path: Path) -> None:
    from download_topotijdreis import parse_args

    args = parse_args(
        [
            "--csv",
            str(tmp_path / "locations.csv"),
            "--years",
            "2012",
            "2020",
            "--output-dir",
            str(tmp_path / "images"),
        ]
    )

    assert args.csv == tmp_path / "locations.csv"
    assert args.years == [2012, 2020]
    assert args.output_dir == tmp_path / "images"


def test_cli_delegates_to_python_downloader(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, object] = {}

    def fake_download(
        csv_path: Path,
        years: list[int],
        output_dir: Path,
        **kwargs: object,
    ) -> list[Path]:
        calls.update(
            csv_path=csv_path,
            years=years,
            output_dir=output_dir,
            **kwargs,
        )
        return []

    monkeypatch.setattr(cli, "download_topotijdreis", fake_download)

    result = cli.main(
        [
            "--csv",
            str(tmp_path / "locations.csv"),
            "--years",
            "2020",
            "--output-dir",
            str(tmp_path / "images"),
        ]
    )

    assert result == 0
    assert calls["csv_path"] == tmp_path / "locations.csv"
    assert calls["years"] == [2020]
    assert calls["output_dir"] == tmp_path / "images"
