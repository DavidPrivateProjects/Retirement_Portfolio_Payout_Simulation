"""Generate scenario insights and a 3-slide solution-engineer interview deck."""

from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import stock_movements as sm


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "assets"
SLIDE_DECK = ROOT / "docs" / "solution_engineer_interview_slides.md"
CSV_PATH = ASSET_DIR / "solution_engineer_scenario_insights.csv"
DAYS_PER_YEAR = 252
SIMULATIONS = 1_500
START_BALANCE = 100_000

MARKET_REGIMES = {
    "Base market": {
        "mu": 0.00032,
        "sigma": 0.0118,
        "description": "S&P 500-like long-run daily return and volatility assumptions",
    },
    "Volatile market": {
        "mu": 0.00020,
        "sigma": 0.0180,
        "description": "Lower expected return with materially higher volatility",
    },
}

SCENARIOS = [
    {
        "scenario": "Guided 3.5% plan",
        "market_regime": "Base market",
        "withdrawal_rate": 0.035,
        "sim_years": 30,
        "business_context": "Lower-risk recommendation for cautious retirees",
    },
    {
        "scenario": "Classic 4% rule",
        "market_regime": "Base market",
        "withdrawal_rate": 0.040,
        "sim_years": 30,
        "business_context": "Simple default benchmark for client conversations",
    },
    {
        "scenario": "Lifestyle stretch 5%",
        "market_regime": "Base market",
        "withdrawal_rate": 0.050,
        "sim_years": 30,
        "business_context": "Higher spending target with visible downside trade-off",
    },
    {
        "scenario": "Early retirement 4%",
        "market_regime": "Base market",
        "withdrawal_rate": 0.040,
        "sim_years": 40,
        "business_context": "Longer planning horizon for younger retirees",
    },
    {
        "scenario": "Volatile 4% stress test",
        "market_regime": "Volatile market",
        "withdrawal_rate": 0.040,
        "sim_years": 30,
        "business_context": "Stress-test view for risk and suitability conversations",
    },
    {
        "scenario": "Volatile 5% stretch",
        "market_regime": "Volatile market",
        "withdrawal_rate": 0.050,
        "sim_years": 30,
        "business_context": "Demonstrates why explainable guardrails matter",
    },
]

SWEEP_WITHDRAWAL_RATES = np.array([0.030, 0.035, 0.040, 0.045, 0.050, 0.055, 0.060])


def currency(value):
    return f"${value:,.0f}"


def pct(value):
    return f"{value:.1%}"


def simulate_scenario(withdrawal_rate, sim_years, market_regime, seed):
    regime = MARKET_REGIMES[market_regime]
    prices, withdrawals = sm.brown_motion_drift_plus_wd(
        START_BALANCE,
        regime["mu"],
        regime["sigma"],
        SIMULATIONS,
        sim_years,
        withdrawal_rate,
        yearly_withdrawels=True,
        withdraw_after_first_year=True,
        days_per_year=DAYS_PER_YEAR,
        rng=np.random.default_rng(seed),
    )
    is_lost, loss_idx = sm.find_zero_points(prices)
    failed_indices = [idx for idx in loss_idx if idx != -1]
    total_withdrawn = np.abs(sm.total_withdrawals_before_loss(withdrawals, loss_idx, SIMULATIONS))
    return {
        "failure_probability": sm.loss_probability(is_lost),
        "survival_probability": 1 - sm.loss_probability(is_lost),
        "average_failure_year": np.nan if not failed_indices else np.mean(failed_indices) / DAYS_PER_YEAR,
        "median_ending_balance": float(np.median(prices[-1, :])),
        "p10_ending_balance": float(np.percentile(prices[-1, :], 10)),
        "p90_ending_balance": float(np.percentile(prices[-1, :], 90)),
        "average_withdrawn_before_end_or_failure": float(np.mean(total_withdrawn)),
    }


def build_scenario_table():
    rows = []
    for scenario in SCENARIOS:
        if scenario["market_regime"] == "Base market" and scenario["sim_years"] == 30:
            seed = 1_000
        elif scenario["market_regime"] == "Base market":
            seed = 1_400
        else:
            seed = 2_000
        metrics = simulate_scenario(
            scenario["withdrawal_rate"],
            scenario["sim_years"],
            scenario["market_regime"],
            seed=seed,
        )
        rows.append({**scenario, **metrics})
    return pd.DataFrame(rows)


def build_rate_sweep():
    rows = []
    for market_regime in MARKET_REGIMES:
        seed = 3_000 if market_regime == "Base market" else 4_000
        for withdrawal_rate in SWEEP_WITHDRAWAL_RATES:
            metrics = simulate_scenario(
                withdrawal_rate,
                sim_years=30,
                market_regime=market_regime,
                seed=seed,
            )
            rows.append(
                {
                    "scenario": f"{market_regime} {withdrawal_rate:.1%}",
                    "market_regime": market_regime,
                    "withdrawal_rate": withdrawal_rate,
                    "sim_years": 30,
                    "business_context": "Withdrawal-rate sensitivity sweep",
                    **metrics,
                }
            )
    return pd.DataFrame(rows)


def save_failure_sensitivity_chart(sweep_df):
    fig, ax = plt.subplots(figsize=(12, 7))
    for market_regime, group in sweep_df.groupby("market_regime"):
        ax.plot(
            group["withdrawal_rate"] * 100,
            group["failure_probability"],
            marker="o",
            linewidth=2.5,
            label=market_regime,
        )
    ax.set_title("Scenario insight: portfolio risk is highly sensitive to withdrawal rate")
    ax.set_xlabel("Annual withdrawal rate (% of starting portfolio)")
    ax.set_ylabel("30-year portfolio failure probability")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "solution_engineer_failure_sensitivity.png", dpi=160)
    plt.close(fig)


def save_business_value_matrix(scenario_df):
    fig, ax = plt.subplots(figsize=(12, 7))
    colors = np.where(scenario_df["market_regime"].eq("Base market"), "#1f77b4", "#c00000")
    ax.scatter(
        scenario_df["failure_probability"],
        scenario_df["median_ending_balance"],
        s=230,
        c=colors,
        alpha=0.78,
        edgecolor="white",
        linewidth=1.5,
    )
    for _, row in scenario_df.iterrows():
        ax.annotate(
            row["scenario"],
            (row["failure_probability"], row["median_ending_balance"]),
            xytext=(9, 4),
            textcoords="offset points",
            fontsize=9,
        )
    ax.set_title("Scenario insight: make trade-offs visible before the client commits")
    ax.set_xlabel("Portfolio failure probability")
    ax.set_ylabel("Median ending balance")
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.yaxis.set_major_formatter(lambda value, _: f"${value:,.0f}")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "solution_engineer_business_value_matrix.png", dpi=160)
    plt.close(fig)


def write_slide_deck(scenario_df, sweep_df):
    classic = scenario_df.loc[scenario_df["scenario"].eq("Classic 4% rule")].iloc[0]
    guided = scenario_df.loc[scenario_df["scenario"].eq("Guided 3.5% plan")].iloc[0]
    volatile = scenario_df.loc[scenario_df["scenario"].eq("Volatile 4% stress test")].iloc[0]
    stretch = scenario_df.loc[scenario_df["scenario"].eq("Lifestyle stretch 5%")].iloc[0]

    base_3 = sweep_df[(sweep_df["market_regime"] == "Base market") & (sweep_df["withdrawal_rate"] == 0.030)].iloc[0]
    base_6 = sweep_df[(sweep_df["market_regime"] == "Base market") & (sweep_df["withdrawal_rate"] == 0.060)].iloc[0]

    deck = f"""---
marp: true
title: Retirement Portfolio Simulator - Solution Engineering Story
paginate: true
---

# Retirement Portfolio Simulator
## Turning financial uncertainty into explainable decisions

**Business problem:** retirees and advisors need to understand how spending choices, market risk, and planning horizon affect portfolio sustainability.

**Solution:** an interactive Python + Dash simulator that converts assumptions into repeatable scenarios, visual risk metrics, and stakeholder-ready recommendations.

**Solution-engineering angle:** discovery questions become configurable inputs; outputs become a clear business conversation rather than a black-box model.

---

# Insight 1: small input changes create large business trade-offs

![Failure sensitivity](assets/solution_engineer_failure_sensitivity.png)

- In the base market sweep, moving from a **3.0%** to **6.0%** withdrawal rate changed simulated failure risk from **{pct(base_3['failure_probability'])}** to **{pct(base_6['failure_probability'])}**.
- A guided **3.5%** plan produced **{pct(guided['survival_probability'])}** survival vs. **{pct(classic['survival_probability'])}** for the classic **4%** benchmark.
- Business value: helps advisors frame suitability, set expectations, and show clients why guardrails matter.

---

# Insight 2: the same product demo supports discovery, stress testing, and executive value

![Business value matrix](assets/solution_engineer_business_value_matrix.png)

- A **4% volatile-market stress test** showed **{pct(volatile['failure_probability'])}** failure risk, compared with **{pct(classic['failure_probability'])}** for the base-market 4% benchmark.
- A **5% lifestyle stretch** increased failure risk to **{pct(stretch['failure_probability'])}** while changing the median ending-balance story to **{currency(stretch['median_ending_balance'])}**.
- Why this fits a Solution Engineer role: I can connect technical implementation, customer discovery, risk storytelling, and measurable business outcomes in one demo.
"""
    SLIDE_DECK.write_text(deck)


def main():
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    scenario_df = build_scenario_table()
    sweep_df = build_rate_sweep()
    combined_df = pd.concat([scenario_df, sweep_df], ignore_index=True)
    combined_df.to_csv(CSV_PATH, index=False)
    save_failure_sensitivity_chart(sweep_df)
    save_business_value_matrix(scenario_df)
    write_slide_deck(scenario_df, sweep_df)

    print(f"Saved scenario metrics to {CSV_PATH}")
    print(f"Saved slide deck to {SLIDE_DECK}")
    print(scenario_df[["scenario", "failure_probability", "median_ending_balance"]].to_string(index=False))


if __name__ == "__main__":
    main()
