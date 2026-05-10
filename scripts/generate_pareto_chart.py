#!/usr/bin/env python3
"""
Generate wiki/assets/pareto.png — publication chart for the multi-objective
view of the strategy leaderboard.

Two panels:
  Left:  Bull return (y) vs Bear MDD (x).  Upper-left is best.
         Pareto frontier traced.  Bubbles sized by trade count, coloured by
         strategy family.  Marker shape distinguishes single-coin from
         multi-coin runs.
  Right: Calmar (y) vs Trade density per year (x).  Frontier traced.

Data is inlined — all five strategies have result cards in wiki/results/.
Edit STRATEGIES below when adding a new datapoint.

Usage:
    ./freqtrade/.venv/bin/python scripts/generate_pareto_chart.py
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "wiki" / "assets" / "pareto.png"

# Family palette
FAMILY_COLOR = {
    "SMA": "#1f77b4",        # blue
    "HMM": "#2ca02c",        # green
    "Carry": "#ff7f0e",      # orange
    "Conjunction": "#9467bd",  # purple
}


@dataclass
class Strategy:
    name: str            # short label for plot
    family: str          # SMA / HMM / Carry / Conjunction
    universe: str        # "BTC only" or "6 coins"
    bull_return: float   # %
    bear_return: float   # %
    bull_mdd: float      # %
    bear_mdd: float      # %
    bull_trades: int
    bull_years: float    # years covered by bull window(s)
    bull_calmar: float | None = None


# All five datapoints currently in the project.
# Sma/HMM-BTC bull metrics are compounded across 2020-21 + 2023-24 sub-windows
# from 2026-05-10-sma-regime-180-cex-bull-validation.md / -hmm-regime-4-rolling-cex-validation.md.
# Multi-asset bull metrics are direct from the 2026-05-10 bull-window CEX runs;
# bear metrics from the 2025-11→2026-05 7-HL-majors runs.
STRATEGIES = [
    Strategy(
        name="SmaRegime180", family="SMA", universe="BTC only",
        bull_return=19.96, bear_return=1.32,
        bull_mdd=1.83, bear_mdd=1.74,
        bull_trades=65, bull_years=4.0,
        bull_calmar=17.5,  # avg of 14.04 (2020-21) and 21.13 (2023-24)
    ),
    Strategy(
        name="HmmRegime4Rolling-BTC", family="HMM", universe="BTC only",
        bull_return=17.03, bear_return=-4.07,
        bull_mdd=3.90, bear_mdd=4.02,
        bull_trades=174, bull_years=4.0,
        bull_calmar=7.4,  # avg of 6.86 and 7.94
    ),
    Strategy(
        name="HmmRegime4Rolling-multi", family="HMM", universe="6 coins",
        bull_return=65.36, bear_return=-5.62,
        bull_mdd=5.69, bear_mdd=14.7,
        bull_trades=477, bull_years=2.0,
        bull_calmar=27.73,
    ),
    Strategy(
        name="FundingCarry", family="Carry", universe="6 coins",
        bull_return=12.47, bear_return=-30.16,
        bull_mdd=10.65, bear_mdd=42.14,
        bull_trades=252, bull_years=2.0,
        bull_calmar=3.06,
    ),
    Strategy(
        name="HmmCarry", family="Conjunction", universe="6 coins",
        bull_return=25.77, bear_return=-19.59,
        bull_mdd=4.54, bear_mdd=23.86,
        bull_trades=158, bull_years=2.0,
        bull_calmar=13.68,
    ),
]


def pareto_frontier(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """
    Upper-left frontier for (x=bear_mdd, y=bull_return).  A point is
    non-dominated if no other point has y >= and x <= with at least one strict.
    Returns the frontier sorted by x ascending.
    """
    frontier: list[tuple[float, float]] = []
    for i, (x, y) in enumerate(points):
        dominated = False
        for j, (xj, yj) in enumerate(points):
            if i == j:
                continue
            if yj >= y and xj <= x and (yj > y or xj < x):
                dominated = True
                break
        if not dominated:
            frontier.append((x, y))
    return sorted(frontier)


def calmar_density_frontier(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Upper-right frontier for (x=density, y=calmar).  High-high is best."""
    frontier: list[tuple[float, float]] = []
    for i, (x, y) in enumerate(points):
        dominated = False
        for j, (xj, yj) in enumerate(points):
            if i == j:
                continue
            if yj >= y and xj >= x and (yj > y or xj > x):
                dominated = True
                break
        if not dominated:
            frontier.append((x, y))
    return sorted(frontier)


def _bubble_size(trades: int) -> float:
    # Square-root area scaling so a 477-trade bubble isn't 7× the area of 65.
    return 60 + (trades ** 0.5) * 18


def _marker_for_universe(u: str) -> str:
    return "o" if u == "6 coins" else "^"


def plot(out_path: Path) -> None:
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(16, 8))
    fig.patch.set_facecolor("white")

    # ---- LEFT PANEL: Bull return vs Bear MDD ----
    points_lr = [(s.bear_mdd, s.bull_return) for s in STRATEGIES]
    frontier_lr = pareto_frontier(points_lr)

    # Shaded "kill zone" — bear MDD > 5.5% is the SmaRegime180 kill criterion.
    ax_left.axvspan(5.5, 50, color="#ffcccc", alpha=0.3, zorder=0)
    ax_left.text(28, 78, "Kill zone\n(bear MDD > 5.5%)",
                 fontsize=9, color="#aa3333", ha="center", style="italic")

    # Pareto frontier line
    if len(frontier_lr) >= 2:
        fx, fy = zip(*frontier_lr)
        ax_left.plot(fx, fy, "k--", lw=1.5, alpha=0.4, label="Pareto frontier", zorder=1)

    # Bubbles
    for s in STRATEGIES:
        ax_left.scatter(
            s.bear_mdd, s.bull_return,
            s=_bubble_size(s.bull_trades),
            c=FAMILY_COLOR[s.family],
            marker=_marker_for_universe(s.universe),
            edgecolors="black", linewidths=0.8,
            alpha=0.85, zorder=3,
        )
        # Label with smart offset for overlap avoidance
        dx, dy = 1.5, 2
        ha = "left"
        if s.name == "SmaRegime180":
            dx, dy = 1.8, 3.5
        elif s.name == "HmmRegime4Rolling-BTC":
            dx, dy = 1.8, -4
        elif s.name == "HmmCarry":
            dx, dy = 1.8, 3
        elif s.name == "FundingCarry":
            dx, dy = -1.5, 4
            ha = "right"
        elif s.name == "HmmRegime4Rolling-multi":
            dx, dy = -1.5, 3.5
            ha = "right"
        ax_left.annotate(
            s.name, (s.bear_mdd, s.bull_return),
            xytext=(s.bear_mdd + dx, s.bull_return + dy),
            fontsize=9, fontweight="bold", ha=ha,
        )

    ax_left.axhline(0, color="grey", lw=0.5, alpha=0.5)
    ax_left.set_xlabel("Bear-cycle MDD (%) — lower is better →", fontsize=11)
    ax_left.set_ylabel("Bull-cycle return (%) — higher is better ↑", fontsize=11)
    ax_left.set_title("Bull capture vs bear drawdown\nFrontier is one segment wide",
                      fontsize=12, fontweight="bold", loc="left")
    ax_left.set_xlim(-2, 50)
    ax_left.set_ylim(-5, 85)
    ax_left.grid(True, alpha=0.3)

    # ---- RIGHT PANEL: Calmar vs Trade Density ----
    points_rt = [
        (s.bull_trades / s.bull_years, s.bull_calmar)
        for s in STRATEGIES if s.bull_calmar is not None
    ]
    frontier_rt = calmar_density_frontier(points_rt)

    if len(frontier_rt) >= 2:
        fx, fy = zip(*frontier_rt)
        ax_right.plot(fx, fy, "k--", lw=1.5, alpha=0.4, label="Pareto frontier", zorder=1)

    for s in STRATEGIES:
        if s.bull_calmar is None:
            continue
        density = s.bull_trades / s.bull_years
        ax_right.scatter(
            density, s.bull_calmar,
            s=_bubble_size(s.bull_trades),
            c=FAMILY_COLOR[s.family],
            marker=_marker_for_universe(s.universe),
            edgecolors="black", linewidths=0.8,
            alpha=0.85, zorder=3,
        )
        dx, dy = 6, 0.4
        ha = "left"
        if s.name == "HmmRegime4Rolling-multi":
            dx, dy = -8, 1.8
            ha = "right"
        elif s.name == "SmaRegime180":
            dx, dy = 6, -0.8
        ax_right.annotate(
            s.name, (density, s.bull_calmar),
            xytext=(density + dx, s.bull_calmar + dy),
            fontsize=9, fontweight="bold", ha=ha,
        )

    ax_right.set_xlim(-5, 290)
    ax_right.set_ylim(0, 33)

    ax_right.set_xlabel("Bull-window trade density (trades/year) →", fontsize=11)
    ax_right.set_ylabel("Bull-window Calmar ↑", fontsize=11)
    ax_right.set_title("Risk-adjusted return vs signal density\nBoth axes positive — high-high is best",
                       fontsize=12, fontweight="bold", loc="left")
    ax_right.grid(True, alpha=0.3)

    # ---- Shared legend ----
    family_handles = [
        mpatches.Patch(color=FAMILY_COLOR[f], label=f)
        for f in ["SMA", "HMM", "Carry", "Conjunction"]
    ]
    universe_handles = [
        Line2D([0], [0], marker="^", color="w", markerfacecolor="grey",
               markeredgecolor="black", markersize=10, label="BTC only"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="grey",
               markeredgecolor="black", markersize=10, label="6-coin basket"),
    ]
    fig.suptitle("Strategy Pareto view — 2026-05-10",
                 fontsize=15, fontweight="bold", y=0.985)
    fig.legend(handles=family_handles + universe_handles,
               loc="upper center", ncol=6,
               bbox_to_anchor=(0.5, 0.945), frameon=False, fontsize=10)
    fig.text(0.5, 0.015,
             "Bull windows: SMA/HMM-BTC compounded 2020-21 + 2023-24 on Binance BTC; multi-coin runs 2023-01 → 2025-01 on Binance 6-majors. "
             "Bear windows: SMA/HMM-BTC compounded 2022 + 2025; multi-coin runs 2025-11 → 2026-05 on Hyperliquid 7-majors (HYPE absent from bull universe).",
             ha="center", fontsize=8, style="italic", color="#555")

    plt.tight_layout(rect=[0, 0.04, 1, 0.91])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    plot(OUT_PATH)
