from pathlib import Path

import pytest

from lifecycle.__main__ import main
from lifecycle.forecast import Asset, forecast, format_table, overdue, read_assets, remaining_life

EX = Path(__file__).resolve().parent.parent / "examples" / "assets.csv"


def asset(asset_id="A-1", install=2010, life=20, cost=1000.0):
    return Asset(asset_id, "Unit", "HVAC", install, life, cost)


def test_end_of_life_year():
    assert asset(install=2010, life=20).end_of_life_year == 2030


def test_remaining_life_positive_and_negative():
    assert remaining_life(asset(install=2010, life=20), 2026) == 4
    assert remaining_life(asset(install=2000, life=20), 2026) == -6


def test_overdue_sorted_oldest_first():
    items = [asset("B", 2000, 20), asset("A", 1990, 20), asset("C", 2020, 20)]
    assert [a.asset_id for a in overdue(items, 2026)] == ["A", "B"]


def test_asset_ending_this_year_is_not_overdue():
    assert overdue([asset(install=2006, life=20)], 2026) == []


def test_forecast_places_overdue_in_current_year():
    buckets = forecast([asset(install=2000, life=20, cost=500.0)], 2026, 3)
    assert buckets[0].year == 2026
    assert buckets[0].cost == 500.0


def test_forecast_year_range_and_horizon_zero():
    assert [b.year for b in forecast([], 2026, 5)] == list(range(2026, 2032))
    assert [b.year for b in forecast([], 2026, 0)] == [2026]


def test_forecast_excludes_beyond_horizon():
    buckets = forecast([asset(install=2040, life=20)], 2026, 10)
    assert sum(b.count for b in buckets) == 0


def test_forecast_future_year_bucket():
    buckets = forecast([asset(install=2020, life=10, cost=250.0)], 2026, 10)
    by_year = {b.year: b for b in buckets}
    assert by_year[2030].count == 1
    assert by_year[2030].cost == 250.0


def test_negative_horizon_rejected():
    with pytest.raises(ValueError):
        forecast([], 2026, -1)


def test_read_example_assets():
    assets = read_assets(EX)
    assert len(assets) == 12
    assert assets[0].asset_id == "HVAC-0001"


def test_read_assets_bad_number(tmp_path):
    path = tmp_path / "a.csv"
    path.write_text(
        "asset_id,name,category,install_year,expected_life_years,replacement_cost\nX-1,n,c,abc,10,5\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="row 1"):
        read_assets(path)


def test_read_assets_rejects_zero_life(tmp_path):
    path = tmp_path / "a.csv"
    path.write_text(
        "asset_id,name,category,install_year,expected_life_years,replacement_cost\nX-1,n,c,2000,0,5\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        read_assets(path)


def test_table_total_matches_asset_costs():
    assets = read_assets(EX)
    buckets = forecast(assets, 2026, 30)
    assert f"{sum(a.replacement_cost for a in assets):,.0f}" in format_table(buckets).splitlines()[-1]


def test_cli(capsys, tmp_path):
    assert main([str(EX), "--year", "2026", "--horizon", "10"]) == 0
    assert "Overdue" in capsys.readouterr().out
    assert main([str(tmp_path / "none.csv"), "--year", "2026"]) == 1
