# vtools

This repository contains small, independently installable Python packages.
Each package has its own build metadata, dependencies, tests, and README under
`packages/`.

Every package supports both a reusable Python API and a command-line
interface. The package READMEs show direct Python usage, the installed console
command, and the equivalent `python -m <package>` invocation.

## Packages

| Package | Install directory | Purpose |
| --- | --- | --- |
| `change-cover` | [`packages/change_cover`](packages/change_cover) | Update PowerPoint cover slides |
| `download-topotijdreis` | [`packages/download_topotijdreis`](packages/download_topotijdreis) | Download Topotijdreis satellite-image crops |
| `era5-downloader` | [`packages/era5_downloader`](packages/era5_downloader) | Download ERA5 data through the CDS API |

## Install a package from GitHub

The packages are not published to PyPI. Users can clone the repository and
install only the package they need:

```powershell
git clone https://github.com/V-Chavarrias/vtools.git
Set-Location vtools

python -m pip install .\packages\change_cover
python -m pip install .\packages\download_topotijdreis
python -m pip install .\packages\era5_downloader
```

Alternatively, install a package directly from the `main` branch without
cloning the repository:

```powershell
python -m pip install "git+https://github.com/V-Chavarrias/vtools.git@main#subdirectory=packages/change_cover"
python -m pip install "git+https://github.com/V-Chavarrias/vtools.git@main#subdirectory=packages/download_topotijdreis"
python -m pip install "git+https://github.com/V-Chavarrias/vtools.git@main#subdirectory=packages/era5_downloader"
```

For a reproducible version, replace `main` with the package-specific release
tag shown below. See each package's README for its command-line or Python API
usage.

## Development

Create a virtual environment and install all packages with their test
dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".\packages\change_cover[test]"
.\.venv\Scripts\python.exe -m pip install -e ".\packages\download_topotijdreis[test]"
.\.venv\Scripts\python.exe -m pip install -e ".\packages\era5_downloader[test]"
.\.venv\Scripts\python.exe -m pip install build
.\.venv\Scripts\python.exe -m pytest packages
```

The test workflow runs the tests and builds each package independently.
The Topotijdreis tests only exercise offline parsing and image helpers; a
local browser is required for an actual download:

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
```

## Delivery

Package versions are maintained in the individual `pyproject.toml` files.
Pushing a package-specific tag starts the release workflow:

```text
change-cover-v0.1.0
download-topotijdreis-v0.1.0
era5-downloader-v0.1.0
```

The workflow builds only the package selected by the tag and creates a GitHub
Release containing its wheel and source archive. Users can install a
downloaded wheel with:

```powershell
python -m pip install .\change_cover-0.1.0-py3-none-any.whl
```

No PyPI account or configuration is required.