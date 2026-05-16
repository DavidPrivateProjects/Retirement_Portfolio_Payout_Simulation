import pandas as pd
from scipy import stats
import random
import numpy as np


DEFAULT_WHO_DATA_FILE = "WHO_data.pkl"
DEFAULT_REGRESSION_FILE = "life_regression_calculations.pkl"


def get_WHO_data():
    """
    Downloads the WHO longevity data and saves the data as a pandas dataframe in the repository.
    Source : World Health Organization (WHO) Global Health Observatory Data / http://pophealthmetrics.biomedcentral.com/articles/10.1186/s12963-016-0094-0#Sec7
    """
    
    life_exp_data = pd.read_csv("https://apps.who.int/gho/athena/data/GHO/WHOSIS_000001,WHOSIS_000015?filter=COUNTRY:*&x-sideaxis=COUNTRY;YEAR&x-topaxis=GHO;SEX&profile=verbose&format=csv")

    life_exp_data = life_exp_data[["GHO (DISPLAY)", "YEAR (CODE)", "COUNTRY (DISPLAY)", 
                                   "SEX (DISPLAY)", "Numeric"]]
    
    life_exp_data.to_pickle(DEFAULT_WHO_DATA_FILE)
    
# get_WHO_data()

def calc_life_regression(life_exp_data, country, sex,
                         STD_MALES=5.6, STD_FEMALES=3.6):
    """
    Estimates the expected death time as well as life expectancy decrease depending on age, country and sex by using WHO data 
    and estimating a linear regression through the data points.
    """

    sub_data = life_exp_data[life_exp_data["COUNTRY (DISPLAY)"] == country]
    sub_data = sub_data[sub_data['SEX (DISPLAY)'] == sex]
    if sub_data.empty:
        raise ValueError(f"No WHO life expectancy rows found for {country!r}, {sex!r}")

    sub_data.sort_values(by='YEAR (CODE)', ascending=False, inplace=True)
    birth_expectancy_data = sub_data[sub_data['GHO (DISPLAY)'] == "Life expectancy at birth (years)"]
    sixty_year_expectancy_data = sub_data[sub_data['GHO (DISPLAY)'] == "Life expectancy at age 60 (years)"]
    if birth_expectancy_data.empty or sixty_year_expectancy_data.empty:
        raise ValueError(f"Missing birth or age-60 expectancy rows for {country!r}, {sex!r}")

    birth_expectancy = float(birth_expectancy_data.iloc[0]["Numeric"])
    sixty_year_expectancy = float(sixty_year_expectancy_data.iloc[0]["Numeric"])
    
    ages = [0,60]
    life_expectancies = [birth_expectancy, sixty_year_expectancy]
    slope, intercept, _, _, _ = stats.linregress(ages, life_expectancies)

    life_std = STD_MALES if sex == 'Male' else STD_FEMALES
    return slope, intercept, life_std


def gen_life_reg_file(data_file_name, STD_MALES=5.6, STD_FEMALES=3.6,
                      output_file=DEFAULT_REGRESSION_FILE, strict=False):
    """
    Estimates the expected death time as well as life expectancy decrease depending on age, country and sex by using the 
    calc_life_regression function on all available rows in the WHO dataset. Saves a copy of the calculated values in the repository.
    """
    life_exp_data = pd.read_pickle(data_file_name)
    
    regression_results = []

    for country in life_exp_data['COUNTRY (DISPLAY)'].unique():
        for sex in ["Male", "Female"]:
            try:
                slope, intercept, life_std = calc_life_regression(life_exp_data, country, 
                                                                  sex, STD_MALES, STD_FEMALES)
                regression_results.append([country, sex, slope, intercept, life_std])
            
            except (KeyError, IndexError, ValueError):
                if strict:
                    raise

    life_reg_calc_pd = pd.DataFrame(regression_results, columns=["Country", "Sex", "Slope", "Intercept", "Life_std"])
    if life_reg_calc_pd.empty:
        raise ValueError("No life regression values were generated from the WHO data")
    life_reg_calc_pd.to_pickle(output_file)
    return life_reg_calc_pd

# get_life_reg_file("WHO_data.pkl")

def get_life_reg_vals(file_name, country=None, sex=None):
    """
    Returns the slope, intercept and std of the life_regression_calculations for the respective country and sex.
    """
    if sex is None:
        file_name, country, sex = DEFAULT_REGRESSION_FILE, file_name, country

    life_reg_df = pd.read_pickle(file_name)

    sub_set = life_reg_df[life_reg_df["Country"] == country]
    sub_set = sub_set[sub_set["Sex"] == sex]
    if sub_set.empty:
        raise ValueError(f"No life regression values found for {country!r}, {sex!r}")
    
    first_match = sub_set.iloc[0]
    return float(first_match["Slope"]), float(first_match["Intercept"]), float(first_match["Life_std"])

def surv_prob_next_year(age, life_slope, life_intercept, life_std):
    """
    Returns the probability of surviving next year.
    """
    life_mean = life_slope * age + life_intercept + age

    prob_survival_till_now = 1 - stats.norm.cdf(age, loc=life_mean, scale=life_std)
    prob_survival_next_year = 1 - stats.norm.cdf(age + 1, loc=life_mean, scale=life_std)

    if prob_survival_till_now <= 0:
        return 0.0, age + 1

    return float(np.clip(prob_survival_next_year / prob_survival_till_now, 0.0, 1.0)), age + 1

def surv_prob_next_month(age, life_slope, life_intercept, life_std):
    """
    Returns the probability of surviving the next month.
    """
    life_mean = life_slope * age + life_intercept + age

    prob_survival_till_now = 1 - stats.norm.cdf(age, loc=life_mean, scale=life_std)
    prob_survival_next_month = 1 - stats.norm.cdf(age + (1 / 12), loc=life_mean, scale=life_std)

    if prob_survival_till_now <= 0:
        return 0.0, age + (1 / 12)

    return float(np.clip(prob_survival_next_month / prob_survival_till_now, 0.0, 1.0)), age + (1 / 12)


def surv_decision(prob, rng=None):
    """
    Returns True if a person survives and False otherwise.
    """
    rng = random if rng is None else rng
    return rng.random() < prob


def survival_arr(sim_years, age, life_slope, life_intercept, life_std, rng=None):
    """
    Returns an survival array containing True and False values for the simulation period depending on the time of death.
    """
    res_arr = []

    year = 0
    while year < sim_years:
        for month in range(0, 12):

            prob, age = surv_prob_next_month(age, life_slope, life_intercept, life_std)
            res = surv_decision(prob, rng=rng)
            
            if res == False:
                res_arr.extend([False] * (12 - month))
                res_arr.extend([False] * (sim_years - year - 1) * (12))
                return res_arr
            
            else:
                res_arr.append(True)
        
        if res_arr[-1] == False:
            res_arr.extend([False] * (sim_years - year) * 12)
            return res_arr
        
        year += 1
    
    return res_arr 


def survival_sim(sim_years, country, age, sex, sim_n,
                 regression_file=DEFAULT_REGRESSION_FILE, rng=None):
    """
    Runs the survival simulation and returns a collection of survival arrays.
    """
    res_array = []
    life_slope, life_intercept, life_std = get_life_reg_vals(regression_file, country, sex)

    for _ in range(sim_n):
        curr_res = survival_arr(sim_years, age, life_slope, life_intercept, life_std, rng=rng)
        res_array.append(curr_res)

    res_array = np.array(res_array)
    return  np.transpose(res_array)

def death_ind(surr_arr):
    """
    Returns the point of death on the survival array.
    """
    res = np.where(surr_arr == False)[0]
    
    if len(res) == 0:
        return -1
    
    return res[0]