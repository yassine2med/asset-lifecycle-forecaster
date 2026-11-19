"""Replacement forecast from install year and expected life."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Asset:
    """One asset with the fields the forecast needs."""

    asset_id: str
    name: str
    category: str
    install_year: int
    expected_life_years: int
    replacement_cost: float

    @property
    def end_of_life_year(self) -> int:
        """Year the asset reaches its expected life."""
        return self.install_year + self.expected_life_years


@dataclass(frozen=True)
class YearBucket:
    """Replacements planned in one year."""

    year: int
    assets: tuple[Asset, ...]

    @property
    def count(self) -> int:
        return len(self.assets)

    @property
    def cost(self) -> float:
        return sum(a.replacement_cost for a in self.assets)


def read_assets(path: str | Path) -> list[Asset]:
    """Read assets from a CSV. Raises ValueError with the row number for bad values."""
    assets = []
    with open(path, newline="", encoding="utf-8") as handle:
        for number, row in enumerate(csv.DictReader(handle), start=1):
            try:
                asset = Asset(
                    asset_id=row["asset_id"].strip(),
                    name=row["name"].strip(),
                    category=row["category"].strip(),
                    install_year=int(row["install_year"]),
                    expected_life_years=int(row["expected_life_years"]),
                    replacement_cost=float(row["replacement_cost"]),
                )
            except (KeyError, ValueError, AttributeError) as error:
                raise ValueError(f"row {number}: {error!r}") from error
            if asset.expected_life_years <= 0 or asset.replacement_cost < 0:
                raise ValueError(f"row {number}: life must be positive and cost cannot be negative")
            assets.append(asset)
    return assets


def remaining_life(asset: Asset, current_year: int) -> int:
    """Years left before end of life. Negative means the asset is past its life."""
    return asset.end_of_life_year - current_year


def overdue(assets: list[Asset], current_year: int) -> list[Asset]:
    """Assets whose end of life year is before the current year, oldest first."""
    late = [a for a in assets if a.end_of_life_year < current_year]
    return sorted(late, key=lambda a: (a.end_of_life_year, a.asset_id))


def forecast(assets: list[Asset], current_year: int, horizon: int = 10) -> list[YearBucket]:
    """Group replacements by year for the current year plus the horizon.

    Overdue assets are placed in the current year because they need action now.
    Assets that reach end of life after the horizon are not included.
    """
    if horizon < 0:
        raise ValueError("horizon cannot be negative")
    last_year = current_year + horizon
    buckets: dict[int, list[Asset]] = {y: [] for y in range(current_year, last_year + 1)}
    for asset in assets:
        year = max(asset.end_of_life_year, current_year)
        if year <= last_year:
            buckets[year].append(asset)
    return [YearBucket(y, tuple(sorted(items, key=lambda a: a.asset_id))) for y, items in buckets.items()]


def format_table(buckets: list[YearBucket]) -> str:
    """Render the forecast as a fixed-width text table with a total line."""
    lines = [f"{'Year':<6}{'Assets':>7}{'Cost':>14}"]
    for b in buckets:
        lines.append(f"{b.year:<6}{b.count:>7}{b.cost:>14,.0f}")
    lines.append(f"{'Total':<6}{sum(b.count for b in buckets):>7}{sum(b.cost for b in buckets):>14,.0f}")
    return "\n".join(lines)
