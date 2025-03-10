import pandas as pd
from scipy import stats
import random
import numpy as np

def get_WHO_data():
    """
    Downloads the WHO longevity data and saves the data as a pandas dataframe in the repository.
    Source : World Health Organization (WHO) Global Health Observatory Data / http://pophealthmetrics.biomedcentral.com/articles/10.1186/s12963-016-0094-0#Sec7
    """
    
    life_exp_data = pd.read_csv("https://apps.who.int/gho/athena/data/GHO/WHOSIS_000001,WHOSIS_000015?filter=COUNTRY:*&x-sideaxis=COUNTRY;YEAR&x-topaxis=GHO;SEX&profile=verbose&format=csv")

    life_exp_data = life_exp_data[["GHO (DISPLAY)", "YEAR (CODE)", "COUNTRY (DISPLAY)", 
                                   "SEX (DISPLAY)", "Numeric"]]
    
    life_exp_data.to_pickle("WHO_data.pkl")
    
# get_WHO_data()

def calc_life_regression(life_exp_data, country, sex,
                         STD_MALES=5.6, STD_FEMALES=3.6):
    """
    Estimates the expected death time as well as life expectancy decrease depending on age, country and sex by using WHO data 
    and estimating a linear regression through the data points.
    """

    sub_data = life_exp_data[life_exp_data["COUNTRY (DISPLAY)"] == country]
    sub_data = sub_data[sub_data['SEX (DISPLAY)'] == sex]

    sub_data.sort_values(by='YEAR (CODE)', ascending=False, inplace=True)
    birth_expectancy = sub_data[sub_data['GHO (DISPLAY)'] == "Life expectancy at birth (years)"].values[0][-1]
    sixty_year_expectancy = sub_data[sub_data['GHO (DISPLAY)'] == "Life expectancy at age 60 (years)"].values[0][-1]
    
    ages = [0,60]
    life_expectancies = [birth_expectancy, sixty_year_expectancy]
    slope, intercept, _, _, _ = stats.linregress(ages, life_expectancies)

    life_std = STD_MALES if sex == 'Male' else STD_FEMALES
    return slope, intercept, life_std


def gen_life_reg_file(data_file_name, STD_MALES=5.6, STD_FEMALES=3.6):
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
            
            except:
                pass

    life_reg_calc_pd = pd.DataFrame(regression_results, columns=["Country", "Sex", "Slope", "Intercept", "Life_std"])
    life_reg_calc_pd.to_pickle("life_regression_calculations.pkl")

# get_life_reg_file("WHO_data.pkl")

def get_life_reg_vals(file_name, country, sex):
    """
    Returns the slope, intercept and std of the life_regression_calculations for the respective country and sex.
    """
    life_reg_df = pd.read_pickle(file_name)

    sub_set = life_reg_df[life_reg_df["Country"] == country]
    sub_set = sub_set[sub_set["Sex"] == sex]
    
    return float(sub_set["Slope"]), float(sub_set["Intercept"]), float(sub_set["Life_std"])

def surv_prob_next_year(age, life_slope, life_intercept, life_std):
    """
    Returns the probability of surviving next year.
    """
    life_mean = life_slope * age + life_intercept + age

    prob_survival_till_now = 1 - stats.norm.cdf(age, loc=life_mean, scale=life_std)
    prob_survival_next_year = 1 - stats.norm.cdf(age + 1, loc=life_mean, scale=life_std)

    return prob_survival_next_year / prob_survival_till_now, age + 1

def surv_prob_next_month(age, life_slope, life_intercept, life_std):
    """
    Returns the probability of surviving the next month.
    """
    life_mean = life_slope * age + life_intercept + age

    prob_survival_till_now = 1 - stats.norm.cdf(age, loc=life_mean, scale=life_std)
    prob_survival_next_month = 1 - stats.norm.cdf(age + (1 / 12), loc=life_mean, scale=life_std)

    return prob_survival_next_month / prob_survival_till_now, age + (1 / 12)


def surv_decision(prob):
    """
    Returns True if a person survives and False otherwise.
    """
    return random.random() < prob


def survival_arr(sim_years, age, life_slope, life_intercept, life_std):
    """
    Returns an survival array containing True and False values for the simulation period depending on the time of death.
    """
    res_arr = []

    year = 0
    while year < sim_years:
        for month in range(0, 12):

            prob, age = surv_prob_next_month(age, life_slope, life_intercept, life_std)
            res = surv_decision(prob)
            
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


def survival_sim(sim_years, country, age, sex, sim_n):
    """
    Runs the survival simulation and returns a collection of survival arrays.
    """
    res_array = []
    life_slope, life_intercept, life_std = get_life_reg_vals(country, sex)

    for _ in range(sim_n):
        curr_res = survival_arr(sim_years, age, life_slope, life_intercept, life_std)
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