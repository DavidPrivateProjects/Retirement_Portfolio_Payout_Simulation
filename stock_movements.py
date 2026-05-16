"""Portfolio return and withdrawal simulation utilities.

The model intentionally stays lightweight: it estimates daily log-return mean
and volatility from a Yahoo Finance index series, then simulates independent
Gaussian daily returns and subtracts a fixed withdrawal schedule.
"""

import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf


def _as_scalar(value, name):
    """Normalize pandas/numpy scalar-like values returned by data libraries."""
    scalar = float(np.asarray(value).squeeze())
    if not np.isfinite(scalar):
        raise ValueError(f"{name} must be a finite number")
    return scalar


def _normal_returns(mu, sigma, size, rng=None):
    if rng is None:
        return np.random.normal(mu, sigma, size=size)
    return rng.normal(mu, sigma, size=size)


def get_index_data(index_of_choice, period="max"):
    """Return the historical daily log-return mean and std for a Yahoo symbol."""
    index_df = yf.download(
        index_of_choice,
        auto_adjust=False,
        period=period,
        progress=False,
    )
    if index_df.empty:
        raise ValueError(f"No market data returned for symbol {index_of_choice!r}")

    adjusted_close = index_df["Adj Close"].squeeze()
    index_returns = np.log1p(adjusted_close.pct_change()).dropna()
    if index_returns.empty:
        raise ValueError(f"Not enough market data to estimate returns for {index_of_choice!r}")

    return _as_scalar(index_returns.mean(), "mean return"), _as_scalar(index_returns.std(), "return std")


def brown_motion_drift(start_balance, mu, sigma, runtime, n_simul, rng=None):
    """Simulate portfolio paths without withdrawals.

    Parameters use trading days for ``runtime`` and return an array with the
    starting balance prepended, so the output shape is ``(runtime + 1, n_simul)``.
    """
    sim_returns = _normal_returns(mu, sigma, size=(int(runtime), int(n_simul)), rng=rng)
    stacked_returns = np.vstack([np.zeros(int(n_simul)), sim_returns])
    return float(start_balance) * (stacked_returns + 1).cumprod(axis=0)


def find_zero_points(stock_prices, n_simul=None):
    """Find the first day each simulation path drops below zero.

    Returns a pair of lists: whether the portfolio is lost, and the loss index.
    ``-1`` means that path never crossed below zero during the simulation.
    """
    stock_prices = np.asarray(stock_prices)
    if stock_prices.ndim != 2:
        raise ValueError("stock_prices must be a 2D array shaped as days x simulations")

    n_simul = stock_prices.shape[1] if n_simul is None else int(n_simul)
    portfolio_is_lost = []
    portfolio_loss_idx = []

    for i in range(n_simul):
        zero_points = np.where(stock_prices[:, i] < 0)[0]
        if len(zero_points) == 0:
            portfolio_is_lost.append(False)
            portfolio_loss_idx.append(-1)
        else:
            portfolio_is_lost.append(True)
            portfolio_loss_idx.append(int(zero_points[0]))

    return portfolio_is_lost, portfolio_loss_idx


def loss_probability(portfolio_is_lost):
    """Return the share of simulations that depleted the portfolio."""
    return float(np.mean(portfolio_is_lost))


def average_loss_point(portfolio_loss_idx):
    """Return the average loss index across failed simulations, or NaN if none fail."""
    loss_points = [value for value in portfolio_loss_idx if value != -1]
    if not loss_points:
        return np.nan
    return float(np.mean(loss_points))


def withdrawal_schedule(
    start_balance,
    sim_years,
    withdrawel_rate,
    yearly_withdrawels,
    withdraw_after_first_year,
    days_per_year=252,
):
    """Build the cumulative withdrawal amount for each simulated trading day.

    The historical spelling of ``withdrawel`` is kept in public parameters so
    notebooks that already import this module continue to run.
    """
    sim_years = int(sim_years)
    days_per_year = int(days_per_year)
    if sim_years <= 0 or days_per_year <= 0:
        raise ValueError("sim_years and days_per_year must be positive")

    total_days = sim_years * days_per_year
    if yearly_withdrawels:
        period_index = np.arange(0, sim_years) if withdraw_after_first_year else np.arange(1, sim_years + 1)
        period_index = np.repeat(period_index, days_per_year)
        withdrawal_unit = float(start_balance) * float(withdrawel_rate)
    else:
        if days_per_year % 12 != 0:
            raise ValueError("days_per_year must be divisible by 12 for monthly withdrawals")
        months = sim_years * 12
        if withdraw_after_first_year:
            active_months = max(months - 12, 0)
            period_index = np.concatenate([np.zeros(12), np.arange(1, active_months + 1)])
        else:
            period_index = np.arange(1, months + 1)
        period_index = np.repeat(period_index, days_per_year // 12)
        withdrawal_unit = float(start_balance) * float(withdrawel_rate) / 12

    if len(period_index) != total_days:
        raise ValueError("withdrawal schedule length does not match simulation length")
    return -period_index * withdrawal_unit


def brown_motion_drift_plus_wd(
    start_balance,
    mu,
    sigma,
    n_simul,
    sim_years,
    withdrawel_rate,
    yearly_withdrawels,
    withdraw_after_first_year,
    days_per_year=252,
    rng=None,
):
    """Simulate portfolio paths and subtract a fixed cumulative withdrawal schedule."""
    runtime = int(sim_years) * int(days_per_year) - 1
    sim_prices = brown_motion_drift(start_balance, mu, sigma, runtime, n_simul, rng=rng)
    withdrawal_returns = withdrawal_schedule(
        start_balance,
        sim_years,
        withdrawel_rate,
        yearly_withdrawels,
        withdraw_after_first_year,
        days_per_year=days_per_year,
    )
    withdrawal_returns = np.repeat(withdrawal_returns[:, np.newaxis], int(n_simul), axis=1)
    return sim_prices + withdrawal_returns, withdrawal_returns


def total_withdrawels_before_loss(withdrawal_returns, portfolio_loss_idx, n_simul):
    """Return cumulative withdrawals at each path's failure day or final day."""
    withdrawal_returns = np.asarray(withdrawal_returns)
    result = []

    for i in range(int(n_simul)):
        result.append(withdrawal_returns[int(portfolio_loss_idx[i]), i])

    return np.array(result)


def total_withdrawals_before_loss(withdrawal_returns, portfolio_loss_idx, n_simul):
    """Correctly spelled alias for ``total_withdrawels_before_loss``."""
    return total_withdrawels_before_loss(withdrawal_returns, portfolio_loss_idx, n_simul)


def average_total_withdrawels(tot_withdrawels_before_loss):
    """Return the average cumulative amount withdrawn."""
    return float(np.mean(tot_withdrawels_before_loss))


def average_total_withdrawals(tot_withdrawals_before_loss):
    """Correctly spelled alias for ``average_total_withdrawels``."""
    return average_total_withdrawels(tot_withdrawals_before_loss)


def plot_stock_with_loss_point(stock_prices, n_simul, portfolio_loss_idx):
    """Plot each path until depletion, or the full path when it survives."""
    for i in range(int(n_simul)):
        loss_idx = portfolio_loss_idx[i]
        end_idx = None if loss_idx == -1 else loss_idx
        plt.plot(stock_prices[:end_idx, i], linewidth=0.4)

    plt.show()

if __name__ == "__main__":

    # Start price of the simulation!
    start_balance = 100


    # Stockdays per year
    days_per_year = 252


    # Total number of simulations
    n_simul = 500

    # Simulation years
    sim_years = 30

    # Runtime in days
    runtime = days_per_year * sim_years - 1

    # Withdrawal rate is yearly and after the first year!
    yearly_withdrawels = True # If false, then monthly withdrawals
    withdraw_after_first_year = True # If false, withdrawal starts with the simulation


    # Money is taken out of the account after one year
    withdrawel_rate = 0.08


    index_of_choice = "NDX"


    ndx_mu, ndx_sigma = get_index_data(index_of_choice)

    sim_prices = brown_motion_drift(start_balance, ndx_mu, ndx_sigma, runtime, n_simul)

    # plt.plot(sim_prices, linewidth=0.25)
    # plt.show()

    stock_prices, withdrawal_returns = brown_motion_drift_plus_wd(start_balance, ndx_mu, ndx_sigma, 
                                                                  n_simul,
                                                                  sim_years, withdrawel_rate,
                                                                  yearly_withdrawels=True,
                                                                  withdraw_after_first_year=False,
                                                                  days_per_year=252)
    

    # plt.plot(stock_prices)
    # plt.show()

    portfolio_is_lost, portfolio_loss_idx = find_zero_points(stock_prices, n_simul)
    tot_w_before_loss = total_withdrawels_before_loss(withdrawal_returns, portfolio_loss_idx, n_simul)

    # print(loss_probability(portfolio_is_lost))
    # print(average_loss_point(portfolio_loss_idx) / 252)
        

    plot_stock_with_loss_point(stock_prices, n_simul,
                               portfolio_loss_idx)

