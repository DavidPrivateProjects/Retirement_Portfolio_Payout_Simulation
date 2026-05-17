"""Dash interface for the retirement withdrawal simulation."""

import re

import numpy as np
import plotly.graph_objects as go

from dash import Dash, dcc, html, Input, Output, callback, dash_table, State
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

import stock_movements as sm


INDEX_OPTIONS = [
    {"label": "NASDAQ-100 (^NDX)", "value": "^NDX"},
    {"label": "S&P 500 (^GSPC)", "value": "^GSPC"},
]

FALLBACK_MARKET_STATS = {
    "^NDX": (0.00045, 0.0155),
    "^GSPC": (0.00032, 0.0118),
}
TRADING_DAYS_PER_YEAR = 252
MAX_DISPLAYED_PATHS = 60


app = Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])
load_figure_template("SANDSTONE")


def parse_number(value, default, minimum=None, maximum=None):
    """Parse user-entered values such as ``100,000 USD`` into numbers."""
    if value is None:
        parsed = default
    elif isinstance(value, (int, float)):
        parsed = float(value)
    else:
        cleaned = re.sub(r"[^0-9.\-]", "", str(value))
        parsed = float(cleaned) if cleaned else default

    if minimum is not None:
        parsed = max(parsed, minimum)
    if maximum is not None:
        parsed = min(parsed, maximum)
    return parsed


def parse_rate(value, default=0.04):
    """Parse a withdrawal rate entered as ``4%``, ``4``, or ``0.04``."""
    parsed = parse_number(value, default)
    if isinstance(value, str) and "%" in value:
        return parsed / 100
    return parsed / 100 if parsed > 1 else parsed


def get_market_stats(symbol):
    """Fetch live return assumptions, falling back to documented defaults."""
    try:
        mu, sigma = sm.get_index_data(symbol, period="10y")
        return mu, sigma, f"Using 10-year Yahoo Finance data for {symbol}."
    except Exception as exc:
        mu, sigma = FALLBACK_MARKET_STATS.get(symbol, FALLBACK_MARKET_STATS["^GSPC"])
        return mu, sigma, f"Using built-in fallback assumptions because live data failed: {exc}"


def format_currency(value):
    return f"${value:,.0f}"


def make_summary_table_data(prices, withdrawals, portfolio_is_lost, portfolio_loss_idx):
    ending_balances = prices[-1, :]
    failed_indices = [idx for idx in portfolio_loss_idx if idx != -1]
    avg_failure_year = np.nan
    if failed_indices:
        avg_failure_year = np.mean(failed_indices) / TRADING_DAYS_PER_YEAR

    total_withdrawn = np.abs(
        sm.total_withdrawels_before_loss(withdrawals, portfolio_loss_idx, len(portfolio_is_lost))
    )
    return [
        {"metric": "Portfolio survival rate", "value": f"{(1 - sm.loss_probability(portfolio_is_lost)):.1%}"},
        {"metric": "Failure rate", "value": f"{sm.loss_probability(portfolio_is_lost):.1%}"},
        {"metric": "Average failure year", "value": "N/A" if np.isnan(avg_failure_year) else f"{avg_failure_year:.1f}"},
        {"metric": "Median ending balance", "value": format_currency(float(np.median(ending_balances)))},
        {"metric": "10th percentile ending balance", "value": format_currency(float(np.percentile(ending_balances, 10)))},
        {"metric": "90th percentile ending balance", "value": format_currency(float(np.percentile(ending_balances, 90)))},
        {"metric": "Average withdrawn before end/failure", "value": format_currency(float(np.mean(total_withdrawn)))},
    ]


def make_simulation_figure(prices):
    x_years = np.arange(prices.shape[0]) / TRADING_DAYS_PER_YEAR
    fig = go.Figure()
    displayed_paths = min(prices.shape[1], MAX_DISPLAYED_PATHS)

    for path_idx in range(displayed_paths):
        fig.add_trace(
            go.Scatter(
                x=x_years,
                y=prices[:, path_idx],
                mode="lines",
                line={"width": 1},
                opacity=0.35,
                showlegend=False,
                hovertemplate="Year %{x:.1f}<br>Balance $%{y:,.0f}<extra></extra>",
            )
        )

    fig.add_hline(y=0, line_dash="dash", line_color="firebrick")
    fig.update_layout(
        title=f"Monte Carlo portfolio paths ({displayed_paths} displayed)",
        xaxis_title="Simulation year",
        yaxis_title="Portfolio balance",
        margin={"l": 40, "r": 20, "t": 60, "b": 40},
        height=560,
    )
    return fig


controls = dbc.Card(
    dbc.CardBody(
        [
            html.H4("Simulation controls", className="card-title"),
            dbc.Label("Starting portfolio"),
            dbc.Input(id="balance", value="100,000", type="text"),
            dbc.Label("Annual withdrawal rate", className="mt-3"),
            dbc.Input(id="wd_rate", value="4%", type="text"),
            dbc.Label("Market index", className="mt-3"),
            dcc.Dropdown(id="index", options=INDEX_OPTIONS, value="^GSPC", clearable=False),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Years", className="mt-3"),
                            dbc.Input(id="sim_years", value=30, type="number", min=1, max=80),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Simulations", className="mt-3"),
                            dbc.Input(id="sim_n", value=500, type="number", min=10, max=5000),
                        ],
                        md=6,
                    ),
                ]
            ),
            dbc.Button("Run simulation", id="run-simulation", color="primary", className="mt-4 w-100"),
            html.Small(
                "The graph uses a fixed random seed so stakeholders can reproduce the same demo output.",
                className="text-muted d-block mt-3",
            ),
        ]
    ),
    className="shadow-sm",
)


summary_table = dash_table.DataTable(
    id="summary-table",
    columns=[
        {"name": "Metric", "id": "metric"},
        {"name": "Value", "id": "value"},
    ],
    data=[],
    style_cell={"fontFamily": "Verdana", "fontSize": 14, "padding": "0.6rem"},
    style_header={"fontWeight": "bold", "backgroundColor": "#dfd3c3"},
    style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#f8f4ee"}],
)


model_notes = dbc.Accordion(
    [
        dbc.AccordionItem(
            [
                html.P(
                    "The simulation uses 252 trading days per year, a common approximation for US equity markets. "
                    "Withdrawals are modeled as fixed percentages of the initial balance, not inflation-adjusted cash flows."
                )
            ],
            title="Why 252 days per year?",
        ),
        dbc.AccordionItem(
            [
                html.P(
                    "Daily returns are sampled from a normal distribution estimated from historical index log returns. "
                    "That makes the model easy to explain, but it does not capture fat tails, changing volatility, fees, taxes, or sequence-risk regimes."
                )
            ],
            title="What are the limitations?",
        ),
        dbc.AccordionItem(
            [
                html.P(
                    "The life expectancy module can be regenerated from WHO data with the commands in the README. "
                    "The dashboard focuses on the portfolio path so the app runs even when local WHO pickle files are absent."
                )
            ],
            title="Where does longevity fit?",
        ),
    ],
    start_collapsed=True,
)


app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                [
                    html.H1("Retirement Portfolio Withdrawal Simulation", className="display-5"),
                    html.P(
                        "A compact Monte Carlo dashboard for exploring how withdrawals and market volatility can deplete a retirement portfolio.",
                        className="lead",
                    ),
                ],
                className="py-4 text-center",
            )
        ),
        dbc.Row(
            [
                dbc.Col(controls, lg=3, className="mb-4"),
                dbc.Col(
                    [
                        dbc.Alert(id="model-status", color="secondary"),
                        dcc.Graph(id="simulation", config={"displayModeBar": False}),
                    ],
                    lg=6,
                    className="mb-4",
                ),
                dbc.Col(
                    [
                        html.H4("Results"),
                        summary_table,
                        html.H4("Model notes", className="mt-4"),
                        model_notes,
                    ],
                    lg=3,
                    className="mb-4",
                ),
            ]
        ),
        html.Footer(
            "Built with Python, NumPy, Yahoo Finance data, Plotly Dash, and a small testable simulation core.",
            className="text-center text-muted py-4",
        ),
    ],
    fluid=True,
    style={"fontFamily": "Verdana", "backgroundColor": "#f0ece2", "minHeight": "100vh"},
)

@app.callback(
    Output("simulation", "figure"),
    Output("summary-table", "data"),
    Output("model-status", "children"),
    Input("run-simulation", "n_clicks"),
    State("balance", "value"),
    State("wd_rate", "value"),
    State("index", "value"),
    State("sim_years", "value"),
    State("sim_n", "value"),
)
def update_simulation(_, balance, wd_rate, index, sim_years, sim_n):
    start_balance = parse_number(balance, 100000, minimum=1000)
    withdrawal_rate = parse_rate(wd_rate, default=0.04)
    sim_years = int(parse_number(sim_years, 30, minimum=1, maximum=80))
    sim_n = int(parse_number(sim_n, 500, minimum=10, maximum=5000))
    mu, sigma, status = get_market_stats(index)

    prices, withdrawals = sm.brown_motion_drift_plus_wd(
        start_balance,
        mu,
        sigma,
        sim_n,
        sim_years,
        withdrawal_rate,
        yearly_withdrawels=True,
        withdraw_after_first_year=False,
        days_per_year=TRADING_DAYS_PER_YEAR,
        rng=np.random.default_rng(42),
    )
    portfolio_is_lost, portfolio_loss_idx = sm.find_zero_points(prices, sim_n)
    return (
        make_simulation_figure(prices),
        make_summary_table_data(prices, withdrawals, portfolio_is_lost, portfolio_loss_idx),
        status,
    )

if __name__ == "__main__":
    app.run(debug=True)