# All imports
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

def brown_motion_drift(start_price, mu, sigma, runtime, n_simul):
    sim_returns = np.random.normal(mu, sigma, 
                                size=(runtime, n_simul))

    stacked_returns = np.vstack([np.zeros(n_simul), sim_returns]) # prepends 1 infront of all returns
    sim_prices = start_price * (stacked_returns + 1).cumprod(axis=0)
    return sim_prices
    

def find_zero_points(stock_prices, n_simul):
    portfolio_is_lost = []
    portfolio_loss_idx = []
    for i in range(0, n_simul):
        zero_points = np.where(stock_prices[:, i] < 0)[0]
        if len(zero_points) == 0:
            portfolio_is_lost.append(False)
            portfolio_loss_idx.append(-1)
        else:
            portfolio_is_lost.append(True)
            portfolio_loss_idx.append(zero_points[0])

    
    return portfolio_is_lost, portfolio_loss_idx


def loss_probability(portfolio_is_lost):
    return np.mean(portfolio_is_lost)


def average_loss_point(portfolio_loss_idx):
    result = []
    for value in portfolio_loss_idx:
        if value != -1:
            result.append(value)

    return np.mean(result) 


def total_withdrawels_before_loss(withdrawal_returns, portfolio_loss_idx, n_simul):
    result = []

    for i in range(n_simul):
        result.append(withdrawal_returns[portfolio_loss_idx[i], i])

    return np.array(result)


def average_total_withdrawels(tot_withdrawels_before_loss):
    return np.mean(tot_withdrawels_before_loss)


def brown_motion_drift_plus_wd(start_price, mu, sigma, 
                               runtime, n_simul, days_per_year,
                               sim_years, withdrawel_rate, 
                               yearly_withdrawels,
                               withdraw_after_first_year):
    
    sim_returns = np.random.normal(mu, sigma, 
                                size=(runtime, n_simul))

    stacked_returns = np.vstack([np.zeros(n_simul), sim_returns]) # prepends 1 infront of all returns
    
    sim_prices = start_price * (stacked_returns + 1).cumprod(axis=0)
    

    if withdraw_after_first_year:
        if yearly_withdrawels:
            index_arr = np.arange(0, sim_years)
            index_arr = np.repeat(index_arr, days_per_year)
        else:
            index_arr = np.arange(1, (sim_years-1)*12+1)
            index_arr = np.repeat(index_arr, days_per_year/12)
            index_arr = np.concatenate([np.zeros(days_per_year), index_arr], axis=0)
    else:
        if yearly_withdrawels:
            index_arr = np.arange(1, sim_years+1)
            index_arr = np.repeat(index_arr, days_per_year)
        else:
            index_arr = np.arange(1, (sim_years) * 12 + 1)
            index_arr = np.repeat(index_arr, days_per_year/12)

    
    if yearly_withdrawels:
        withdrawal_returns = - index_arr * start_price * withdrawel_rate
    else:
        withdrawal_returns = - index_arr * start_price * (withdrawel_rate / 12)


    # Same for all simulations
    withdrawal_returns = np.expand_dims(withdrawal_returns, axis=1)
    withdrawal_returns = np.repeat(withdrawal_returns, axis=1, repeats=n_simul)

    
    sim_prices += withdrawal_returns

    return sim_prices


def brown_motion_drift_plus_wd(start_price, mu, sigma, 
                               runtime, n_simul, days_per_year,
                               sim_years, withdrawel_rate,
                               yearly_withdrawels,
                               withdraw_after_first_year):
    
    sim_returns = np.random.normal(mu, sigma, 
                                size=(runtime, n_simul))

    stacked_returns = np.vstack([np.zeros(n_simul), sim_returns]) # prepends 1 infront of all returns
    
    sim_prices = start_price * (stacked_returns + 1).cumprod(axis=0)
    

    if withdraw_after_first_year:
        if yearly_withdrawels:
            index_arr = np.arange(0, sim_years)
            index_arr = np.repeat(index_arr, days_per_year)
        else:
            index_arr = np.arange(1, (sim_years-1)*12+1)
            index_arr = np.repeat(index_arr, days_per_year/12)
            index_arr = np.concatenate([np.zeros(days_per_year), index_arr], axis=0)
    else:
        if yearly_withdrawels:
            index_arr = np.arange(1, sim_years+1)
            index_arr = np.repeat(index_arr, days_per_year)
        else:
            index_arr = np.arange(1, (sim_years) * 12 + 1)
            index_arr = np.repeat(index_arr, days_per_year/12)

    
    if yearly_withdrawels:
        withdrawal_returns = - index_arr * start_price * withdrawel_rate
    else:
        withdrawal_returns = - index_arr * start_price * (withdrawel_rate / 12)


    # Same for all simulations
    withdrawal_returns = np.expand_dims(withdrawal_returns, axis=1)
    withdrawal_returns = np.repeat(withdrawal_returns, axis=1, repeats=n_simul)

    
    sim_prices += withdrawal_returns

    return sim_prices, withdrawal_returns



def plot_stock_with_loss_point(stock_prices, n_simul,
                               portfolio_loss_idx):
    for i in range(0, n_simul):
        loss_idx = portfolio_loss_idx[i]
        plt.plot(stock_prices[:loss_idx, i], 
                 linewidth=0.4)

    plt.show()


if __name__ == "__main__":

    # Start price of the simulation!
    start_price = 100


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

    # Find the mean daily Return of NDX and it's standard deviation
    ndx_df = yf.download("NDX", auto_adjust=False)

    # Log is used to normalize the daily returns
    ndx_returns = np.log(1 + ndx_df['Adj Close'].pct_change())

    ndx_mu, ndx_sigma = ndx_returns.mean(), ndx_returns.std()

    sim_prices = brown_motion_drift(start_price, ndx_mu, ndx_sigma, runtime, n_simul)

    # plt.plot(sim_prices, linewidth=0.25)
    # plt.show()


    stock_prices, withdrawal_returns = brown_motion_drift_plus_wd(start_price, ndx_mu, ndx_sigma, 
                                                                runtime, n_simul, days_per_year,
                                                                sim_years, withdrawel_rate,
                                                                yearly_withdrawels=True,
                                                                withdraw_after_first_year=False)

    # plt.plot(stock_prices)
    # plt.show()

    #stock_prices[1800:1900, 7]

    portfolio_is_lost, portfolio_loss_idx = find_zero_points(stock_prices, n_simul)

    def total_withdrawels_before_loss(withdrawal_returns, portfolio_loss_idx, n_simul):
        result = []

        for i in range(n_simul):
            result.append(withdrawal_returns[portfolio_loss_idx[i], i])

        return np.array(result)

    tot_w_before_loss = total_withdrawels_before_loss(withdrawal_returns, portfolio_loss_idx, n_simul)

    tot_w_before_loss

    # print(loss_probability(portfolio_is_lost))
    # print(average_loss_point(portfolio_loss_idx) / 252)

    plot_stock_with_loss_point(stock_prices, n_simul,
                            portfolio_loss_idx)

    # Notes David:
    # Make the inflation fixed
    # Calculate total withdrawals made during the time!
    # Start working on dinamic plot




