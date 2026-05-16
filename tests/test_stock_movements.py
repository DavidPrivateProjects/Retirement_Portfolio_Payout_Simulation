import numpy as np

import stock_movements as sm


def test_brown_motion_drift_shape_and_zero_volatility():
    prices = sm.brown_motion_drift(
        start_balance=100,
        mu=0,
        sigma=0,
        runtime=4,
        n_simul=3,
        rng=np.random.default_rng(0),
    )

    assert prices.shape == (5, 3)
    np.testing.assert_allclose(prices, 100)


def test_withdrawal_schedule_yearly_from_start():
    schedule = sm.withdrawal_schedule(
        start_balance=100,
        sim_years=2,
        withdrawel_rate=0.1,
        yearly_withdrawels=True,
        withdraw_after_first_year=False,
        days_per_year=12,
    )

    assert schedule.shape == (24,)
    np.testing.assert_allclose(schedule[:12], -10)
    np.testing.assert_allclose(schedule[12:], -20)


def test_brown_motion_drift_plus_withdrawals_is_reproducible():
    prices, withdrawals = sm.brown_motion_drift_plus_wd(
        start_balance=100,
        mu=0,
        sigma=0,
        n_simul=2,
        sim_years=2,
        withdrawel_rate=0.1,
        yearly_withdrawels=True,
        withdraw_after_first_year=False,
        days_per_year=12,
        rng=np.random.default_rng(0),
    )

    assert prices.shape == (24, 2)
    assert withdrawals.shape == (24, 2)
    np.testing.assert_allclose(prices[:12, :], 90)
    np.testing.assert_allclose(prices[12:, :], 80)


def test_find_zero_points_and_loss_probability():
    prices = np.array(
        [
            [100, 100, 100],
            [50, 10, 100],
            [-1, 5, 100],
            [-5, -1, 100],
        ]
    )

    is_lost, loss_idx = sm.find_zero_points(prices)

    assert is_lost == [True, True, False]
    assert loss_idx == [2, 3, -1]
    assert sm.loss_probability(is_lost) == 2 / 3
    assert sm.average_loss_point(loss_idx) == 2.5


def test_total_withdrawals_before_loss_uses_final_day_for_survivors():
    withdrawals = np.array(
        [
            [0, 0],
            [-10, -10],
            [-20, -20],
        ]
    )

    result = sm.total_withdrawals_before_loss(withdrawals, [1, -1], 2)

    np.testing.assert_array_equal(result, np.array([-10, -20]))
