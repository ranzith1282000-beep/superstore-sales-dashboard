import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import superstore as s  # noqa: E402


def test_data():
    df = s.load()
    assert len(df) == 9994 and df.isna().sum().sum() == 0


def test_kpis_match_the_dashboard():
    k = s.kpis(s.load())
    assert round(k["total_sales"]) == 2297201
    assert round(k["total_profit"]) == 286397
    assert k["units_sold"] == 37873
    assert abs(k["profit_margin"] - 0.1247) < 0.0001


def test_category_totals_add_up():
    df = s.load()
    cat = s.by(df, "Category")
    assert abs(cat["Sales"].sum() - df["Sales"].sum()) < 0.01
    assert abs(cat["Profit"].sum() - df["Profit"].sum()) < 0.01


def test_every_row_lands_in_one_discount_band():
    d = s.discount_bands(s.load())
    assert d["Order lines"].sum() == 9994


def test_heavy_discounts_lose_money():
    d = s.discount_bands(s.load())
    assert d.loc["21-40%", "Profit"] < 0 and d.loc["Over 40%", "Profit"] < 0
