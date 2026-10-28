# era5-downloader

`era5-downloader` downloads ERA5 single-level reanalysis data from the
Copernicus Climate Data Store (CDS) API. Downloads are organized by variable
and year, and existing NetCDF files are skipped so interrupted jobs can be
resumed.

## Install

Install directly from the GitHub repository:

```powershell
python -m pip install "git+https://github.com/V-Chavarrias/vtools.git@main#subdirectory=packages/era5_downloader"
```

Or clone the repository and install from the checkout:

```powershell
git clone https://github.com/V-Chavarrias/vtools.git
Set-Location vtools
python -m pip install .\packages\era5_downloader
```

Replace `main` with a package release tag such as
`era5-downloader-v0.1.0` when a reproducible version is required.

Configure the CDS API credentials expected by `cdsapi` before calling the
function or command.

## Use from Python

```python
from era5_downloader import download_era5_data

download_era5_data(
    variables=["10m_u_component_of_wind", "10m_v_component_of_wind"],
    years=range(1975, 1976),
    area=[13.5, -81.5, 13.2, -81.2],  # North, West, South, East
    output_root=r"P:\01\05_data\05_ERA5",
)
```

`area` is always ordered as `[North, West, South, East]`. Existing files are
skipped, so the function can be called again to resume an interrupted
download.

## Use from the command line

The `era5-downloader` command accepts the same inputs as the Python function:

```powershell
era5-downloader `
  --variables 10m_u_component_of_wind 10m_v_component_of_wind `
  --years 1975 `
  --area 13.5 -81.5 13.2 -81.2 `
  --output-root P:\01\05_data\05_ERA5
```

The module form is equivalent:

```powershell
python -m era5_downloader `
  --variables 10m_u_component_of_wind 10m_v_component_of_wind `
  --years 1975 `
  --area 13.5 -81.5 13.2 -81.2 `
  --output-root P:\01\05_data\05_ERA5
```
