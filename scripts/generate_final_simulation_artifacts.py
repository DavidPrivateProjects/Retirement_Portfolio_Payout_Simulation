"""Generate reproducible final simulation images for the documentation."""

from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import stock_movements as sm


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "assets"
START_BALANCE = 100_000
SIM_YEARS = 30
SIMULATIONS = 2_000
DISPLAYED_PATHS = 120
DAYS_PER_YEAR = 252
MARKET_MU = 0.00032
MARKET_SIGMA = 0.0118
WITHDRAWAL_RATE = 0.04
WITHDRAWAL_RATES = np.array([0.03, 0.035, 0.04, 0.045, 0.05, 0.055, 0.06])


def simulate(withdrawal_rate, seed):
    """Run a seeded portfolio simulation with documented S&P 500-like defaults."""
    return sm.brown_motion_drift_plus_wd(
        START_BALANCE,
        MARKET_MU,
        MARKET_SIGMA,
        SIMULATIONS,
        SIM_YEARS,
        withdrawal_rate,
        yearly_withdrawels=True,
        withdraw_after_first_year=True,
        days_per_year=DAYS_PER_YEAR,
        rng=np.random.default_rng(seed),
    )


def save_portfolio_paths():
    prices, _ = simulate(WITHDRAWAL_RATE, seed=42)
    years = np.arange(prices.shape[0]) / DAYS_PER_YEAR
    percentiles = np.percentile(prices, [10, 50, 90], axis=1)

    fig, ax = plt.subplots(figsize=(12, 7))
    for idx in range(min(DISPLAYED_PATHS, prices.shape[1])):
        ax.plot(years, prices[:, idx], color="#4f81bd", alpha=0.12, linewidth=0.8)

    ax.plot(years, percentiles[1], color="#1f4e79", linewidth=2.5, label="Median path")
    ax.fill_between(
        years,
        percentiles[0],
        percentiles[2],
        color="#9dc3e6",
        alpha=0.35,
        label="10th-90th percentile range",
    )
    ax.axhline(0, color="#c00000", linestyle="--", linewidth=1.5, label="Depletion threshold")
    ax.set_title("Final retirement portfolio simulation: 4% annual withdrawal")
    ax.set_xlabel("Simulation year")
    ax.set_ylabel("Portfolio balance")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.25)
    ax.yaxis.set_major_formatter(lambda value, _: f"${value:,.0f}")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "final_simulation_portfolio_paths.png", dpi=160)
    plt.close(fig)


def save_withdrawal_sweep():
    failure_rates = []
    median_end_balances = []

    for idx, withdrawal_rate in enumerate(WITHDRAWAL_RATES):
        prices, _ = simulate(withdrawal_rate, seed=100 + idx)
        is_lost, _ = sm.find_zero_points(prices)
        failure_rates.append(sm.loss_probability(is_lost))
        median_end_balances.append(np.median(prices[-1, :]))

    fig, ax1 = plt.subplots(figsize=(12, 7))
    ax2 = ax1.twinx()
    rate_labels = WITHDRAWAL_RATES * 100

    ax1.plot(rate_labels, failure_rates, marker="o", color="#c00000", linewidth=2.5)
    ax2.bar(rate_labels, median_end_balances, width=0.32, alpha=0.35, color="#70ad47")

    ax1.set_title("Final simulation sensitivity: withdrawal rate vs. portfolio risk")
    ax1.set_xlabel("Annual withdrawal rate (% of starting balance)")
    ax1.set_ylabel("Portfolio failure probability", color="#c00000")
    ax2.set_ylabel("Median ending balance", color="#548235")
    ax1.set_ylim(0, 1)
    ax1.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax2.yaxis.set_major_formatter(lambda value, _: f"${value:,.0f}")
    ax1.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "final_simulation_withdrawal_sweep.png", dpi=160)
    plt.close(fig)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_portfolio_paths()
    save_withdrawal_sweep()
    print(f"Saved final simulation artifacts to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
