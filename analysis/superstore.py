"""Superstore sales and profit: KPI checks and the charts used in the README.

Recalculates every number shown on the Power BI dashboard from the raw CSV,
so the dashboard can be checked, then adds the profit view the first version
was missing.

    python analysis/superstore.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "SampleSuperstore.csv"
IMAGES = ROOT / "images"

INK, MUTED, GRID = "#1f2a37", "#5b6675", "#e3e7ee"
BLUE, RED, GREEN = "#1f5f8b", "#b4473c", "#2e7d5b"
DISCOUNT_BANDS = [-0.001, 0, 0.2, 0.4, 1]
DISCOUNT_LABELS = ["No discount", "1-20%", "21-40%", "Over 40%"]


def load(path: Path = DATA) -> pd.DataFrame:
    return pd.read_csv(path, encoding="latin1")


def kpis(df: pd.DataFrame) -> dict:
    sales, profit = df["Sales"].sum(), df["Profit"].sum()
    return {
        "total_sales": round(float(sales), 2),
        "total_profit": round(float(profit), 2),
        "profit_margin": round(float(profit / sales), 4),
        "units_sold": int(df["Quantity"].sum()),
        "orders_lines": len(df),
        "loss_making_lines_share": round(float((df["Profit"] < 0).mean()), 3),
        # The first dashboard had a "Profit plus Sales" card. Profit is already part of the
        # money from sales, so adding the two counts it twice. Kept here only to show the gap.
        "profit_plus_sales_card": round(float(sales + profit), 2),
    }


def by(df: pd.DataFrame, col: str) -> pd.DataFrame:
    g = df.groupby(col, observed=True)[["Sales", "Profit"]].sum()
    g["Margin"] = g["Profit"] / g["Sales"]
    return g


def discount_bands(df: pd.DataFrame) -> pd.DataFrame:
    band = pd.cut(df["Discount"], DISCOUNT_BANDS, labels=DISCOUNT_LABELS)
    g = by(df.assign(band=band), "band")
    g["Order lines"] = band.value_counts().reindex(g.index)
    return g


def style(ax, title):
    ax.set_title(title, loc="left", fontsize=11, color=INK, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8)


def money(x, _=None):
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1_000_000:
        return f"{sign}${x/1e6:.1f}M"
    return f"{sign}${x/1000:,.0f}k" if x >= 1000 else f"{sign}${x:,.0f}"


def dashboard_preview(df: pd.DataFrame, k: dict):
    """A static, Python-drawn version of the dashboard for the README."""
    fig = plt.figure(figsize=(13, 8.2))
    gs = fig.add_gridspec(3, 4, height_ratios=[0.5, 1.2, 1.3], hspace=0.55, wspace=0.35)
    cards = [("Total sales", money(k["total_sales"])), ("Total profit", money(k["total_profit"])),
             ("Profit margin", f"{k['profit_margin']:.1%}"), ("Units sold", f"{k['units_sold']:,}")]
    for i, (label, value) in enumerate(cards):
        ax = fig.add_subplot(gs[0, i])
        ax.axis("off")
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, color="#f2f5f9"))
        ax.text(0.06, 0.62, value, fontsize=20, color=INK, fontweight="bold", transform=ax.transAxes)
        ax.text(0.06, 0.2, label, fontsize=10, color=MUTED, transform=ax.transAxes)

    cat = by(df, "Category")
    ax = fig.add_subplot(gs[1, :2])
    x = range(len(cat))
    ax.bar([i - 0.2 for i in x], cat["Sales"], 0.4, color=BLUE, label="Sales")
    ax.bar([i + 0.2 for i in x], cat["Profit"], 0.4, color=GREEN, label="Profit")
    for i, m in zip(x, cat["Margin"]):
        ax.text(i + 0.2, cat["Profit"].iloc[i] + 15000, f"{m:.1%}", ha="center", fontsize=8, color=INK)
    ax.set_xticks(list(x), cat.index)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(money))
    ax.legend(frameon=False, fontsize=8)
    style(ax, "Sales and profit by category (margin above bars)")

    reg = by(df, "Region").sort_values("Sales")
    ax = fig.add_subplot(gs[1, 2:])
    ax.barh(reg.index, reg["Sales"], color="#b9cde0", label="Sales")
    ax.barh(reg.index, reg["Profit"], color=GREEN, label="Profit")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(money))
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    style(ax, "Sales and profit by region")

    sub = by(df, "Sub-Category").sort_values("Profit")
    ax = fig.add_subplot(gs[2, :2])
    ax.barh(sub.index, sub["Profit"], color=[RED if v < 0 else GREEN for v in sub["Profit"]])
    ax.axvline(0, color=MUTED, linewidth=0.8)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(money))
    style(ax, "Profit by sub-category")

    seg = df.groupby("Segment")["Sales"].sum()
    ax = fig.add_subplot(gs[2, 2])
    ax.pie(seg, labels=seg.index, autopct="%1.0f%%", colors=[BLUE, "#7fa7c9", "#c9d6e8"],
           wedgeprops={"width": 0.45}, textprops={"fontsize": 8})
    style(ax, "Sales by segment")

    ship = df.groupby("Ship Mode")["Sales"].sum().sort_values()
    ax = fig.add_subplot(gs[2, 3])
    ax.barh(ship.index, ship.values, color=BLUE)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(money))
    style(ax, "Sales by ship mode")

    fig.suptitle("Superstore sales & profit overview (recreated in Python from the dashboard data)",
                 x=0.02, ha="left", fontsize=13, color=INK, fontweight="bold")
    fig.savefig(IMAGES / "dashboard_preview.png", dpi=130, bbox_inches="tight")
    plt.close(fig)


def plot_discounts(df: pd.DataFrame):
    d = discount_bands(df)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(d.index.astype(str), d["Margin"], color=[GREEN if v >= 0 else RED for v in d["Margin"]])
    for i, (m, p) in enumerate(zip(d["Margin"], d["Profit"])):
        ax.text(i, m + 0.03 if m >= 0 else m - 0.03, f"{m:.0%}\n({money(p)})", ha="center",
                va="bottom" if m >= 0 else "top", fontsize=9, color=INK)
    ax.axhline(0, color=MUTED, linewidth=0.8)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.set_ylim(d["Margin"].min() - 0.22, d["Margin"].max() + 0.18)
    ax.set_ylabel("Profit margin")
    style(ax, "Profit margin by discount level: discounts over 20% lose money")
    fig.tight_layout()
    fig.savefig(IMAGES / "discount_vs_margin.png", dpi=150)
    plt.close(fig)


def plot_states(df: pd.DataFrame):
    st = by(df, "State").sort_values("Profit")
    picks = pd.concat([st.head(6), st.tail(6)])
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(picks.index, picks["Profit"], color=[RED if v < 0 else GREEN for v in picks["Profit"]])
    for y, (p, s) in enumerate(zip(picks["Profit"], picks["Sales"])):
        ax.text(p + (1500 if p >= 0 else -1500), y, f"sales {money(s)}", va="center",
                ha="left" if p >= 0 else "right", fontsize=8, color=MUTED)
    ax.axvline(0, color=MUTED, linewidth=0.8)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(money))
    ax.set_xlim(picks["Profit"].min() - 25000, picks["Profit"].max() + 25000)
    style(ax, "Most and least profitable states")
    fig.tight_layout()
    fig.savefig(IMAGES / "profit_by_state.png", dpi=150)
    plt.close(fig)


def main():
    df = load()
    IMAGES.mkdir(exist_ok=True)
    k = kpis(df)
    (ROOT / "analysis" / "kpis.json").write_text(json.dumps(k, indent=2))
    dashboard_preview(df, k)
    plot_discounts(df)
    plot_states(df)
    print(json.dumps(k, indent=2))
    print(discount_bands(df).round(3))
    print(by(df, "Category").round(3))


if __name__ == "__main__":
    main()
