from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from .downloader import download_era5_data


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download ERA5 single-level reanalysis data from the CDS API."
    )
    parser.add_argument(
        "--variables",
        nargs="+",
        required=True,
        help="One or more CDS variable names.",
    )
    parser.add_argument(
        "--years",
        nargs="+",
        required=True,
        type=int,
        help="One or more four-digit years.",
    )
    parser.add_argument(
        "--area",
        nargs=4,
        required=True,
        type=float,
        metavar=("NORTH", "WEST", "SOUTH", "EAST"),
        help="Bounding box in CDS order: North West South East.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Root directory for downloaded NetCDF files.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    download_era5_data(
        variables=args.variables,
        years=args.years,
        area=args.area,
        output_root=args.output_root,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
