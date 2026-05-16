import random

import numpy as np
import pandas as pd

import life_expectancy as lf


def test_survival_prob_next_month_is_bounded():
    prob, next_age = lf.surv_prob_next_month(
        age=62,
        life_slope=-0.5,
        life_intercept=84,
        life_std=5.6,
    )

    assert 0 <= prob <= 1
    assert next_age == 62 + (1 / 12)


def test_get_life_reg_vals_reads_matching_row(tmp_path):
    regression_file = tmp_path / "life_regression_calculations.pkl"
    pd.DataFrame(
        [
            ["Exampleland", "Female", -0.45, 85.0, 3.6],
            ["Exampleland", "Male", -0.50, 82.0, 5.6],
        ],
        columns=["Country", "Sex", "Slope", "Intercept", "Life_std"],
    ).to_pickle(regression_file)

    assert lf.get_life_reg_vals(str(regression_file), "Exampleland", "Female") == (-0.45, 85.0, 3.6)


def test_survival_sim_uses_configurable_regression_file(tmp_path):
    regression_file = tmp_path / "life_regression_calculations.pkl"
    pd.DataFrame(
        [["Exampleland", "Male", -0.40, 110.0, 8.0]],
        columns=["Country", "Sex", "Slope", "Intercept", "Life_std"],
    ).to_pickle(regression_file)

    result = lf.survival_sim(
        sim_years=2,
        country="Exampleland",
        age=60,
        sex="Male",
        sim_n=3,
        regression_file=str(regression_file),
        rng=random.Random(0),
    )

    assert result.shape == (24, 3)
    assert result.dtype == np.bool_
