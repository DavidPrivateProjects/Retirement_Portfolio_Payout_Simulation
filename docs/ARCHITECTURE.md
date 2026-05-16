# Architecture

This project is split into three small, interview-friendly layers:

1. **Simulation core**: deterministic and testable portfolio math in
   `stock_movements.py`.
2. **Longevity data pipeline**: WHO ingestion, regression, and monthly survival
   simulation in `life_expectancy.py`.
3. **Presentation layer**: an interactive Plotly Dash dashboard in
   `dash_interface.py`.

## Component diagram

```mermaid
flowchart TB
    subgraph Core["Simulation core"]
        SM1[get_index_data]
        SM2[brown_motion_drift]
        SM3[withdrawal_schedule]
        SM4[brown_motion_drift_plus_wd]
        SM5[find_zero_points and summary metrics]
        SM1 --> SM2
        SM2 --> SM4
        SM3 --> SM4
        SM4 --> SM5
    end

    subgraph Longevity["Longevity pipeline"]
        LE1[get_WHO_data]
        LE2[calc_life_regression]
        LE3[gen_life_reg_file]
        LE4[survival_sim]
        LE1 --> LE3
        LE2 --> LE3
        LE3 --> LE4
    end

    subgraph UI["Dash app"]
        UI1[Controls]
        UI2[Simulation callback]
        UI3[Path chart]
        UI4[Summary table]
        UI1 --> UI2
        UI2 --> UI3
        UI2 --> UI4
    end

    Core --> UI
    Longevity -. documented extension .-> UI
```

## Data flow

```mermaid
sequenceDiagram
    participant User
    participant Dash
    participant Stock as stock_movements.py
    participant Yahoo as Yahoo Finance

    User->>Dash: Enter portfolio assumptions
    Dash->>Stock: Request index mean and volatility
    Stock->>Yahoo: Download historical adjusted close data
    Yahoo-->>Stock: Price history
    Stock-->>Dash: Daily mean and standard deviation
    Dash->>Stock: Simulate market paths plus withdrawals
    Stock-->>Dash: Balance paths and withdrawal arrays
    Dash->>Dash: Calculate ruin metrics
    Dash-->>User: Chart, status, and summary table
```

If Yahoo Finance is unavailable during a live demo, the dashboard uses documented
fallback assumptions for the selected index so the app can still be presented.

## Generated data

WHO source data and regression pickles are generated locally:

```mermaid
flowchart LR
    A[WHO CSV endpoint] --> B[get_WHO_data]
    B --> C[WHO_data.pkl]
    C --> D[gen_life_reg_file]
    D --> E[life_regression_calculations.pkl]
    E --> F[survival_sim]
```

The generated `.pkl` files are ignored by git because they can be rebuilt from
the public WHO endpoint.

## Testing strategy

- Tests avoid network calls.
- Random simulations accept seeded random generators for reproducibility.
- Portfolio tests cover shape, withdrawal schedule behavior, depletion
  detection, and summary metric calculations.
- Longevity tests cover probability bounds, regression-file lookup, and survival
  simulation output shape.

Run all tests with:

```bash
pytest
```
