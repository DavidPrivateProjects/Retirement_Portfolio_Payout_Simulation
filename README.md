# Retirement Portfolio Payout Simulation

A Python portfolio project that explores a practical retirement question:

> Given an initial portfolio, a withdrawal rate, historical market volatility,
> and a simulated investment horizon, how often does the portfolio survive?

The repository combines a small simulation core, a Dash dashboard, and a WHO
life expectancy data pipeline. It is intentionally transparent enough to discuss
in interviews: every assumption is visible, testable, and documented.

## What this project demonstrates

- Monte Carlo simulation of portfolio paths using historical index log returns.
- Fixed withdrawal modeling with yearly or monthly withdrawal schedules.
- Portfolio ruin metrics such as failure probability and average depletion year.
- A Dash dashboard for interactively exploring withdrawal assumptions.
- A WHO-based longevity module that can regenerate country/sex regression inputs.
- Unit tests for core math and data-loading behavior without relying on network calls.

## Architecture

```mermaid
flowchart LR
    A[Yahoo Finance index data] --> B[get_index_data]
    B --> C[Daily return mean and volatility]
    C --> D[Monte Carlo market paths]
    E[User withdrawal assumptions] --> F[Withdrawal schedule]
    D --> G[Portfolio balance paths]
    F --> G
    G --> H[Failure probability and summary stats]
    H --> I[Dash dashboard]

    J[WHO life expectancy CSV] --> K[WHO_data.pkl]
    K --> L[Life expectancy regression]
    L --> M[life_regression_calculations.pkl]
    M --> N[Monthly survival simulations]
```

For a deeper component view, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
python dash_interface.py
```

Then open the local Dash URL printed in the terminal.

## Running the simulation modules directly

```bash
python stock_movements.py
```

The script downloads historical index data, simulates withdrawal paths, and
plots the simulated paths. The dashboard is the recommended demo entry point
because it provides reproducible controls and a summary table.

## Regenerating longevity data

The WHO data files are generated artifacts and are ignored by git. To rebuild
them locally:

```bash
python - <<'PY'
import life_expectancy as lf

lf.get_WHO_data()
lf.gen_life_reg_file(lf.DEFAULT_WHO_DATA_FILE)
PY
```

This creates:

- `WHO_data.pkl`
- `life_regression_calculations.pkl`

The longevity module can then run:

```python
import life_expectancy as lf

survival_paths = lf.survival_sim(
    sim_years=30,
    country="United States of America",
    age=62,
    sex="Male",
    sim_n=1000,
)
```

## Model assumptions and limitations

- A year is modeled as 252 trading days.
- Market returns are sampled from a normal distribution estimated from historical
  daily log returns.
- Withdrawals are fixed percentages of the initial balance.
- The default dashboard intentionally uses a fixed random seed so results are
  reproducible during a demo.
- Taxes, fees, inflation, asset allocation drift, fat-tail risk, and changing
  volatility regimes are not modeled yet.
- This is an educational simulation, not financial advice.

## Repository layout

```text
.
├── dash_interface.py       # Interactive Plotly Dash app
├── life_expectancy.py      # WHO data ingestion and survival simulation helpers
├── stock_movements.py      # Portfolio path and withdrawal simulation helpers
├── docs/
│   └── ARCHITECTURE.md     # Architecture notes and diagrams
├── tests/                  # Pytest tests for core behavior
└── *.ipynb                 # Exploratory notebooks and end-to-end story drafts
```

## Interview talking points

- Why the simulation separates market paths from withdrawal schedules.
- Why the dashboard falls back to documented assumptions if Yahoo Finance is not
  available during a live demo.
- How deterministic random seeds make tests and presentations reproducible.
- How the WHO data pipeline is separated from the dashboard so generated files
  do not need to be committed.
- What model assumptions would need to change for production-grade planning.

## Future improvements

- Add inflation-adjusted withdrawals.
- Add asset allocation and rebalancing assumptions.
- Integrate longevity-adjusted success metrics directly into the dashboard.
- Add screenshots or a short demo GIF after deploying the Dash app.