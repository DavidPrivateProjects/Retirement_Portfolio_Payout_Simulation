"""Generate business-value scenario insights and a concise slide deck."""

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
SLIDE_DECK = ROOT / "docs" / "business_value_slides.md"
CSV_PATH = ASSET_DIR / "business_value_scenario_insights.csv"
DAYS_PER_YEAR = 252
SIMULATIONS = 3_000
START_BALANCE = 100_000
RETIREMENT_AGE = 62
LONGEVITY_PLANNING_PERCENTILE = 0.90

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

DEMOGRAPHIC_SEGMENTS = [
    {
        "country": "United States",
        "sex": "Male",
        "median_death_age": 82.7,
        "long_life_planning_age": 90,
        "business_context": "US male longevity-adjusted plan",
        "source_note": "SSA age-62 remaining life expectancy, rounded; long-life age approximates a prudent 90th-percentile planning horizon",
    },
    {
        "country": "United States",
        "sex": "Female",
        "median_death_age": 85.8,
        "long_life_planning_age": 93,
        "business_context": "US female longevity-adjusted plan",
        "source_note": "SSA age-62 remaining life expectancy, rounded; long-life age approximates a prudent 90th-percentile planning horizon",
    },
    {
        "country": "Switzerland",
        "sex": "Male",
        "median_death_age": 85.3,
        "long_life_planning_age": 93,
        "business_context": "Swiss male longevity-adjusted plan",
        "source_note": "Swiss/OECD age-65 life expectancy context, rounded to retirement-age planning assumptions",
    },
    {
        "country": "Switzerland",
        "sex": "Female",
        "median_death_age": 88.0,
        "long_life_planning_age": 95,
        "business_context": "Swiss female longevity-adjusted plan",
        "source_note": "Swiss/OECD age-65 life expectancy context, rounded to retirement-age planning assumptions",
    },
]

BENCHMARK_SCENARIOS = [
    {
        "scenario": "Guided 3.5% plan",
        "country": "General",
        "sex": "General",
        "market_regime": "Base market",
        "withdrawal_rate": 0.035,
        "sim_years": 30,
        "business_context": "Lower-risk recommendation for cautious retirees",
    },
    {
        "scenario": "Classic 4% rule",
        "country": "General",
        "sex": "General",
        "market_regime": "Base market",
        "withdrawal_rate": 0.040,
        "sim_years": 30,
        "business_context": "Simple default benchmark for client conversations",
    },
    {
        "scenario": "Lifestyle stretch 5%",
        "country": "General",
        "sex": "General",
        "market_regime": "Base market",
        "withdrawal_rate": 0.050,
        "sim_years": 30,
        "business_context": "Higher spending target with visible downside trade-off",
    },
    {
        "scenario": "Early retirement 4%",
        "country": "General",
        "sex": "General",
        "market_regime": "Base market",
        "withdrawal_rate": 0.040,
        "sim_years": 40,
        "business_context": "Longer planning horizon for younger retirees",
    },
    {
        "scenario": "Volatile 4% stress test",
        "country": "General",
        "sex": "General",
        "market_regime": "Volatile market",
        "withdrawal_rate": 0.040,
        "sim_years": 30,
        "business_context": "Stress-test view for risk and suitability conversations",
    },
    {
        "scenario": "Volatile 5% stretch",
        "country": "General",
        "sex": "General",
        "market_regime": "Volatile market",
        "withdrawal_rate": 0.050,
        "sim_years": 30,
        "business_context": "Demonstrates why explainable guardrails matter",
    },
]

SWEEP_WITHDRAWAL_RATES = np.array([0.030, 0.035, 0.040, 0.045, 0.050, 0.055, 0.060])
DEMOGRAPHIC_WITHDRAWAL_RATES = np.array([0.035, 0.040, 0.050])


def currency(value):
    return f"${value:,.0f}"


def pct(value):
    return f"{value:.1%}"


def planning_horizon(segment):
    """Convert a demographic long-life age into a portfolio planning horizon."""
    return int(np.ceil(segment["long_life_planning_age"] - RETIREMENT_AGE))


def market_paths(market_regime, sim_years, seed):
    regime = MARKET_REGIMES[market_regime]
    runtime = sim_years * DAYS_PER_YEAR - 1
    return sm.brown_motion_drift(
        START_BALANCE,
        regime["mu"],
        regime["sigma"],
        runtime,
        SIMULATIONS,
        rng=np.random.default_rng(seed),
    )


def metrics_from_paths(paths, withdrawal_rate, sim_years):
    withdrawals = sm.withdrawal_schedule(
        START_BALANCE,
        sim_years,
        withdrawal_rate,
        yearly_withdrawels=True,
        withdraw_after_first_year=True,
        days_per_year=DAYS_PER_YEAR,
    )
    withdrawals = np.repeat(withdrawals[:, np.newaxis], SIMULATIONS, axis=1)
    prices = paths + withdrawals
    is_lost, loss_idx = sm.find_zero_points(prices)
    failed_indices = [idx for idx in loss_idx if idx != -1]
    total_withdrawn = np.abs(sm.total_withdrawals_before_loss(withdrawals, loss_idx, SIMULATIONS))
    failure_probability = sm.loss_probability(is_lost)
    return {
        "failure_probability": failure_probability,
        "survival_probability": 1 - failure_probability,
        "average_failure_year": np.nan if not failed_indices else np.mean(failed_indices) / DAYS_PER_YEAR,
        "median_ending_balance": float(np.median(prices[-1, :])),
        "p10_ending_balance": float(np.percentile(prices[-1, :], 10)),
        "p90_ending_balance": float(np.percentile(prices[-1, :], 90)),
        "average_withdrawn_before_end_or_failure": float(np.mean(total_withdrawn)),
    }


def build_benchmark_table():
    rows = []
    path_cache = {}
    for scenario in BENCHMARK_SCENARIOS:
        key = (scenario["market_regime"], scenario["sim_years"])
        if key not in path_cache:
            seed = 1_000 if scenario["market_regime"] == "Base market" else 2_000
            if scenario["sim_years"] != 30:
                seed += scenario["sim_years"]
            path_cache[key] = market_paths(scenario["market_regime"], scenario["sim_years"], seed)
        metrics = metrics_from_paths(path_cache[key], scenario["withdrawal_rate"], scenario["sim_years"])
        rows.append({"analysis_type": "benchmark", "planning_horizon_source": "fixed", **scenario, **metrics})
    return pd.DataFrame(rows)


def build_rate_sweep():
    rows = []
    for market_regime in MARKET_REGIMES:
        paths = market_paths(market_regime, 30, seed=3_000 if market_regime == "Base market" else 4_000)
        for withdrawal_rate in SWEEP_WITHDRAWAL_RATES:
            metrics = metrics_from_paths(paths, withdrawal_rate, 30)
            rows.append(
                {
                    "analysis_type": "rate_sweep",
                    "scenario": f"{market_regime} {withdrawal_rate:.1%}",
                    "country": "General",
                    "sex": "General",
                    "market_regime": market_regime,
                    "withdrawal_rate": withdrawal_rate,
                    "sim_years": 30,
                    "planning_horizon_source": "fixed",
                    "business_context": "Withdrawal-rate sensitivity sweep",
                    **metrics,
                }
            )
    return pd.DataFrame(rows)


def build_demographic_table():
    rows = []
    for segment_idx, segment in enumerate(DEMOGRAPHIC_SEGMENTS):
        sim_years = planning_horizon(segment)
        segment_label = f"{segment['country']} {segment['sex']}"
        for market_regime in MARKET_REGIMES:
            seed = 5_000 + (segment_idx * 100) + (0 if market_regime == "Base market" else 50)
            paths = market_paths(market_regime, sim_years, seed=seed)
            for withdrawal_rate in DEMOGRAPHIC_WITHDRAWAL_RATES:
                metrics = metrics_from_paths(paths, withdrawal_rate, sim_years)
                rows.append(
                    {
                        "analysis_type": "demographic",
                        "scenario": f"{segment_label} {market_regime} {withdrawal_rate:.1%}",
                        "country": segment["country"],
                        "sex": segment["sex"],
                        "market_regime": market_regime,
                        "withdrawal_rate": withdrawal_rate,
                        "sim_years": sim_years,
                        "planning_horizon_source": f"{LONGEVITY_PLANNING_PERCENTILE:.0%} long-life age from demographic assumption",
                        "business_context": segment["business_context"],
                        "median_death_age": segment["median_death_age"],
                        "long_life_planning_age": segment["long_life_planning_age"],
                        "source_note": segment["source_note"],
                        **metrics,
                    }
                )
    return pd.DataFrame(rows)


def recommended_withdrawal_by_segment(demographic_df, risk_budget=0.12):
    """Find the highest tested withdrawal rate that stays within a failure-risk budget."""
    base = demographic_df[demographic_df["market_regime"] == "Base market"].copy()
    recommendations = []
    for (country, sex), group in base.groupby(["country", "sex"]):
        eligible = group[group["failure_probability"] <= risk_budget].sort_values("withdrawal_rate")
        if eligible.empty:
            chosen = group.sort_values("failure_probability").iloc[0]
        else:
            chosen = eligible.iloc[-1]
        recommendations.append(
            {
                "country": country,
                "sex": sex,
                "recommended_withdrawal_rate": chosen["withdrawal_rate"],
                "failure_probability": chosen["failure_probability"],
                "sim_years": int(chosen["sim_years"]),
            }
        )
    return pd.DataFrame(recommendations)


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
    ax.set_title("Business insight: portfolio risk is highly sensitive to withdrawal rate")
    ax.set_xlabel("Annual withdrawal rate (% of starting portfolio)")
    ax.set_ylabel("30-year portfolio failure probability")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.25)
    ax.legend(title="Market assumption")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "business_value_failure_sensitivity.png", dpi=160)
    plt.close(fig)


def save_business_value_matrix(benchmark_df):
    fig, ax = plt.subplots(figsize=(12, 7))
    colors = np.where(benchmark_df["market_regime"].eq("Base market"), "#1f77b4", "#c00000")
    ax.scatter(
        benchmark_df["failure_probability"],
        benchmark_df["median_ending_balance"],
        s=230,
        c=colors,
        alpha=0.78,
        edgecolor="white",
        linewidth=1.5,
    )
    for _, row in benchmark_df.iterrows():
        ax.annotate(
            row["scenario"],
            (row["failure_probability"], row["median_ending_balance"]),
            xytext=(9, 4),
            textcoords="offset points",
            fontsize=9,
        )
    ax.set_title("Business insight: make risk and outcomes visible before decisions are made")
    ax.set_xlabel("Portfolio failure probability")
    ax.set_ylabel("Median ending balance")
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.yaxis.set_major_formatter(lambda value, _: f"${value:,.0f}")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "business_value_matrix.png", dpi=160)
    plt.close(fig)


def save_demographic_risk_chart(demographic_df):
    selected = demographic_df[
        (demographic_df["withdrawal_rate"] == 0.040)
        & demographic_df["market_regime"].isin(["Base market", "Volatile market"])
    ].copy()
    selected["segment"] = (
        selected["country"]
        + "\n"
        + selected["sex"]
        + "\nmedian "
        + selected["median_death_age"].map(lambda value: f"{value:.1f}")
        + " / plan "
        + selected["long_life_planning_age"].astype(int).astype(str)
    )
    pivot = selected.pivot(index="segment", columns="market_regime", values="failure_probability")
    pivot = pivot[["Base market", "Volatile market"]]

    fig, ax = plt.subplots(figsize=(12, 7))
    pivot.plot(kind="bar", ax=ax, color=["#1f77b4", "#c00000"], width=0.78)
    ax.set_title("Business insight: gender longevity changes the planning horizon")
    ax.set_xlabel("Country, sex, median death age, and long-life planning age")
    ax.set_ylabel("Portfolio failure probability at 4% withdrawal")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_ylim(0, 1)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(title="Market assumption")
    ax.tick_params(axis="x", rotation=0)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "business_value_demographic_risk.png", dpi=160)
    plt.close(fig)


def write_slide_deck(benchmark_df, sweep_df, demographic_df):
    classic = benchmark_df.loc[benchmark_df["scenario"].eq("Classic 4% rule")].iloc[0]
    guided = benchmark_df.loc[benchmark_df["scenario"].eq("Guided 3.5% plan")].iloc[0]
    volatile = benchmark_df.loc[benchmark_df["scenario"].eq("Volatile 4% stress test")].iloc[0]
    stretch = benchmark_df.loc[benchmark_df["scenario"].eq("Lifestyle stretch 5%")].iloc[0]

    base_3 = sweep_df[(sweep_df["market_regime"] == "Base market") & (sweep_df["withdrawal_rate"] == 0.030)].iloc[0]
    base_6 = sweep_df[(sweep_df["market_regime"] == "Base market") & (sweep_df["withdrawal_rate"] == 0.060)].iloc[0]

    demographic_4 = demographic_df[
        (demographic_df["withdrawal_rate"] == 0.040)
        & (demographic_df["market_regime"] == "Base market")
    ].copy()
    lowest_risk = demographic_4.loc[demographic_4["failure_probability"].idxmin()]
    highest_risk = demographic_4.loc[demographic_4["failure_probability"].idxmax()]
    recommendations = recommended_withdrawal_by_segment(demographic_df)
    rec_lookup = {
        (row["country"], row["sex"]): row
        for _, row in recommendations.iterrows()
    }
    us_male_rec = rec_lookup[("United States", "Male")]
    us_female_rec = rec_lookup[("United States", "Female")]
    swiss_female_rec = rec_lookup[("Switzerland", "Female")]

    deck = f"""---
marp: true
title: Retirement Portfolio Simulator - Business Value Story
paginate: true
---

# Retirement Portfolio Simulator
## Turning financial uncertainty into explainable planning conversations

**Business problem:** retirees and advisors need a clear way to compare spending goals, market risk, and longevity assumptions before committing to a plan--especially because women often need assets to last longer and face elevated senior-poverty risk.

**Solution:** a Python + Dash simulator that converts customer assumptions into repeatable scenarios, visual risk metrics, and stakeholder-ready recommendations.

**Why it matters commercially:** the same model can support discovery, suitability conversations, stress testing, and executive-level value storytelling without relying on a black-box answer. It also shows why one-size-fits-all retirement guidance can under-serve women.

---

# Insight 1: withdrawal choices create visible risk trade-offs

![Failure sensitivity](assets/business_value_failure_sensitivity.png)

**What the visualization shows:** each line is a market assumption, each point is a withdrawal rate, and the y-axis is the share of simulated portfolios that ran out of money within 30 years. Lower points are safer; steeper lines mean customers are more sensitive to spending changes.

- In the base market sweep, moving from a **3.0%** to **6.0%** withdrawal rate changed simulated failure risk from **{pct(base_3['failure_probability'])}** to **{pct(base_6['failure_probability'])}**.
- A guided **3.5%** plan produced **{pct(guided['survival_probability'])}** survival vs. **{pct(classic['survival_probability'])}** for the classic **4%** benchmark.
- Business value: the tool turns an abstract percentage into a transparent trade-off that advisors and clients can discuss together.

---

# Insight 2: gender and country change the recommendation conversation

![Demographic risk](assets/business_value_demographic_risk.png)

**What the visualization shows:** each group represents a country/sex segment. The label shows both the median/expected death age and the long-life planning age used for the simulation. Women are tested over longer horizons because outliving a median plan is a key driver of senior poverty. The two bars compare the same 4% withdrawal under base and volatile market assumptions.

- At 4% in the base market, the lowest-risk segment was **{lowest_risk['country']} {lowest_risk['sex']}** at **{pct(lowest_risk['failure_probability'])}** simulated failure risk over **{int(lowest_risk['sim_years'])} years**.
- The highest-risk base-market segment was **{highest_risk['country']} {highest_risk['sex']}** at **{pct(highest_risk['failure_probability'])}** over **{int(highest_risk['sim_years'])} years**.
- Strategy implication: with a **12% failure-risk budget**, the tested US male segment supports **{pct(us_male_rec['recommended_withdrawal_rate'])}**, while the US female segment shifts to **{pct(us_female_rec['recommended_withdrawal_rate'])}** and Swiss female segment shifts to **{pct(swiss_female_rec['recommended_withdrawal_rate'])}**.
- Business value: the solution can personalize guidance by market, country, sex, spending level, and planning horizon instead of presenting one generic rule. This makes the gender gap in longevity visible before it becomes a poverty-risk problem.

---

# Insight 3: the demo connects technical modeling to business outcomes

![Business value matrix](assets/business_value_matrix.png)

**What the visualization shows:** each dot is a planning scenario. Moving right means higher failure risk; moving up means a higher median ending balance. The chart helps separate conservative, benchmark, stretch, and stress-test scenarios in one executive-friendly view.

- A **4% volatile-market stress test** showed **{pct(volatile['failure_probability'])}** failure risk, compared with **{pct(classic['failure_probability'])}** for the base-market 4% benchmark.
- A **5% lifestyle stretch** raised failure risk to **{pct(stretch['failure_probability'])}** while producing a median ending balance of **{currency(stretch['median_ending_balance'])}**.
- Business value: this is a consultative workflow--capture assumptions, configure scenarios, explain risk, and align stakeholders around the next best action.
"""
    SLIDE_DECK.write_text(deck)


def main():
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    benchmark_df = build_benchmark_table()
    sweep_df = build_rate_sweep()
    demographic_df = build_demographic_table()
    combined_df = pd.concat([benchmark_df, sweep_df, demographic_df], ignore_index=True)
    combined_df.to_csv(CSV_PATH, index=False)
    save_failure_sensitivity_chart(sweep_df)
    save_business_value_matrix(benchmark_df)
    save_demographic_risk_chart(demographic_df)
    write_slide_deck(benchmark_df, sweep_df, demographic_df)

    print(f"Saved scenario metrics to {CSV_PATH}")
    print(f"Saved slide deck to {SLIDE_DECK}")
    print("\nBenchmark scenarios:")
    print(benchmark_df[["scenario", "failure_probability", "median_ending_balance"]].to_string(index=False))
    print("\nDemographic 4% base-market scenarios:")
    demographic_summary = demographic_df[
        (demographic_df["withdrawal_rate"] == 0.040)
        & (demographic_df["market_regime"] == "Base market")
    ]
    print(
        demographic_summary[
            [
                "country",
                "sex",
                "median_death_age",
                "long_life_planning_age",
                "sim_years",
                "failure_probability",
                "median_ending_balance",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
