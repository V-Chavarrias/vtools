from pathlib import Path

import pytest

from era5_downloader import cli
from era5_downloader import downloader


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict, str]] = []

    def retrieve(self, dataset: str, request: dict, target: str) -> None:
        self.calls.append((dataset, request, target))
        Path(target).touch()


def test_download_skips_existing_files_and_reuses_year_iterable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FakeClient()
    monkeypatch.setattr(downloader.cdsapi, "Client", lambda: client)
    existing = tmp_path / "u10" / "2020_u10.nc"
    existing.parent.mkdir()
    existing.touch()

    downloader.download_era5_data(
        variables=["u10", "v10"],
        years=(year for year in (2020, 2021)),
        area=[13.5, -81.5, 13.2, -81.2],
        output_root=tmp_path,
    )

    assert len(client.calls) == 3
    assert all(call[0] == "reanalysis-era5-single-levels" for call in client.calls)
    assert {call[1]["year"] for call in client.calls} == {"2020", "2021"}
    assert (tmp_path / "u10" / "2021_u10.nc").exists()
    assert (tmp_path / "v10" / "2020_v10.nc").exists()
    assert (tmp_path / "v10" / "2021_v10.nc").exists()


def test_download_rejects_non_four_digit_year(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(downloader.cdsapi, "Client", FakeClient)

    with pytest.raises(ValueError, match="YYYY"):
        downloader.download_era5_data(
            variables=["u10"],
            years=[99],
            area=[1, 2, 3, 4],
            output_root=tmp_path,
        )


def test_cli_delegates_to_python_api(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, object] = {}

    def fake_download(**kwargs: object) -> None:
        calls.update(kwargs)

    monkeypatch.setattr(cli, "download_era5_data", fake_download)

    result = cli.main(
        [
            "--variables",
            "u10",
            "v10",
            "--years",
            "2020",
            "2021",
            "--area",
            "13.5",
            "-81.5",
            "13.2",
            "-81.2",
            "--output-root",
            str(tmp_path),
        ]
    )

    assert result == 0
    assert calls == {
        "variables": ["u10", "v10"],
        "years": [2020, 2021],
        "area": [13.5, -81.5, 13.2, -81.2],
        "output_root": tmp_path,
    }
