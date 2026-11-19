"""Command line entry: python -m lifecycle FILE.csv --year 2026 --horizon 10."""

from __future__ import annotations

import argparse
import sys

from .forecast import forecast, format_table, overdue, read_assets


def main(argv: list[str] | None = None) -> int:
    """Run the CLI. Returns 0 on success, 1 on bad input."""
    parser = argparse.ArgumentParser(prog="lifecycle", description="Asset replacement forecast")
    parser.add_argument("file")
    parser.add_argument("--year", type=int, required=True, help="current year")
    parser.add_argument("--horizon", type=int, default=10, help="years after the current year")
    args = parser.parse_args(argv)
    try:
        assets = read_assets(args.file)
        buckets = forecast(assets, args.year, args.horizon)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(format_table(buckets))
    late = overdue(assets, args.year)
    print(f"\nOverdue ({len(late)}), counted in {args.year}:")
    for a in late:
        print(f"  {a.asset_id}  {a.name}  end of life {a.end_of_life_year}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
