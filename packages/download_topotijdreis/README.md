# download-topotijdreis

This package downloads square satellite-image crops from
[Topotijdreis](https://www.topotijdreis.nl/) for coordinates in EPSG:28992
(RD New). It reads locations from a CSV, waits for the map tiles to settle,
adds the map attribution, and writes one PNG per location and year.

## Install

Install directly from the GitHub repository:

```powershell
python -m pip install "git+https://github.com/V-Chavarrias/vtools.git@main#subdirectory=packages/download_topotijdreis"
python -m playwright install chromium
```

Or clone the repository and install from the checkout:

```powershell
git clone https://github.com/V-Chavarrias/vtools.git
Set-Location vtools
python -m pip install .\packages\download_topotijdreis
python -m playwright install chromium
```

Replace `main` with a package release tag such as
`download-topotijdreis-v0.1.0` when a reproducible version is required.

## Use

### Command line

```powershell
download-topotijdreis `
  --csv .\locations.csv `
  --years 2012 2020 `
  --zoom 10 `
  --size 512 `
  --output-dir .\images
```

The CSV must contain `X`, `Y`, and `MODELKM` columns by default. Use
`--x-column`, `--y-column`, and `--tag-column` to select different names.
The default input file is `rkm_maas.csv` in the current directory and the
default output directory is `images`.

The module form is equivalent:

```powershell
python -m download_topotijdreis `
  --csv .\locations.csv `
  --years 2012 2020 `
  --output-dir .\images
```

### Python

The complete downloader is also available as the
`download_topotijdreis()` Python function. It uses the same headless
Playwright workflow as the command-line command:

```python
from pathlib import Path

from download_topotijdreis import download_topotijdreis

saved_files = download_topotijdreis(
    csv_path=Path("locations.csv"),
    years=[2012, 2020],
    output_dir=Path("images"),
    zoom=10,
    size=512,
)

for path in saved_files:
    print(f"Available: {path}")
```

The CSV must contain `X`, `Y`, and `MODELKM` columns by default, with
coordinates in EPSG:28992 (RD New). Customize column names with
`x_column`, `y_column`, and `tag_column`. The function also accepts
`site_url`, `tile_timeout`, `retries`, and `retry_delay` options matching the
CLI options. It returns a list of output `Path` objects; existing files are
skipped and included in that list.

The first call requires the Chromium browser used by Playwright:

```powershell
python -m playwright install chromium
```
