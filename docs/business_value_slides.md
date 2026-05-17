---
marp: true
title: Retirement Portfolio Simulator - Business Value Story
paginate: true
---

# Retirement Portfolio Simulator
## Turning financial uncertainty into explainable planning conversations

**Business problem:** retirees and advisors need a clear way to compare spending goals, market risk, and longevity assumptions before committing to a plan.

**Solution:** a Python + Dash simulator that converts customer assumptions into repeatable scenarios, visual risk metrics, and stakeholder-ready recommendations.

**Why it matters commercially:** the same model can support discovery, suitability conversations, stress testing, and executive-level value storytelling without relying on a black-box answer.

---

# Insight 1: withdrawal choices create visible risk trade-offs

![Failure sensitivity](assets/business_value_failure_sensitivity.png)

**What the visualization shows:** each line is a market assumption, each point is a withdrawal rate, and the y-axis is the share of simulated portfolios that ran out of money within 30 years. Lower points are safer; steeper lines mean customers are more sensitive to spending changes.

- In the base market sweep, moving from a **3.0%** to **6.0%** withdrawal rate changed simulated failure risk from **6.3%** to **24.0%**.
- A guided **3.5%** plan produced **91.4%** survival vs. **88.1%** for the classic **4%** benchmark.
- Business value: the tool turns an abstract percentage into a transparent trade-off that advisors and clients can discuss together.

---

# Insight 2: demographics change the recommendation conversation

![Demographic risk](assets/business_value_demographic_risk.png)

**What the visualization shows:** each group represents a country/sex segment. The horizon in parentheses is based on a 90th-percentile longevity planning age, so longer-lived segments are tested over more years. The two bars compare the same 4% withdrawal under base and volatile market assumptions.

- At 4% in the base market, the lowest-risk segment was **United States Male** at **10.4%** simulated failure risk over **27 years**.
- The highest-risk base-market segment was **Switzerland Female** at **12.3%** over **29 years**.
- Business value: the solution can personalize guidance by market, country, sex, spending level, and planning horizon instead of presenting one generic rule.

---

# Insight 3: the demo connects technical modeling to business outcomes

![Business value matrix](assets/business_value_matrix.png)

**What the visualization shows:** each dot is a planning scenario. Moving right means higher failure risk; moving up means a higher median ending balance. The chart helps separate conservative, benchmark, stretch, and stress-test scenarios in one executive-friendly view.

- A **4% volatile-market stress test** showed **65.9%** failure risk, compared with **11.9%** for the base-market 4% benchmark.
- A **5% lifestyle stretch** raised failure risk to **18.5%** while producing a median ending balance of **$503,306**.
- Business value: this is a consultative workflow--capture assumptions, configure scenarios, explain risk, and align stakeholders around the next best action.
