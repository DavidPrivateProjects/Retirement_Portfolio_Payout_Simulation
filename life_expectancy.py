# Data Sources: 
# World Health Organization (WHO) Global Health Observatory Data 
# http://pophealthmetrics.biomedcentral.com/articles/10.1186/s12963-016-0094-0#Sec7

# All imports
import pandas as pd
from scipy import stats
import random


def get_life_exp_vals(country, sex,
                        STD_MALES=5.6, STD_FEMALES=3.6):
    # load WHO longevity data
    life_exp_data = pd.read_csv('https://apps.who.int/gho/athena/data/GHO/WHOSIS_000001,WHOSIS_000015?filter=COUNTRY:*&x-sideaxis=COUNTRY;YEAR&x-topaxis=GHO;SEX&profile=verbose&format=csv')
    # Keep only useful features fix case display of country text
    life_exp_data = life_exp_data[["GHO (DISPLAY)", "YEAR (CODE)", "COUNTRY (DISPLAY)", 
                                   "SEX (DISPLAY)", "Numeric"]]

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

def surv_prob_next_year(age, life_slope, life_intercept, life_std):
    life_mean = life_slope * age + life_intercept + age
    prob_survival_till_now = 1 - stats.norm.cdf(age, loc=life_mean, scale=life_std)
    prob_survival_next_year = 1 - stats.norm.cdf(age + 1, loc=life_mean, scale=life_std)
    return prob_survival_next_year / prob_survival_till_now, age + 1

def surv_prob_next_month(age, life_slope, life_intercept, life_std):
    life_mean = life_slope * age + life_intercept + age
    prob_survival_till_now = 1 - stats.norm.cdf(age, loc=life_mean, scale=life_std)
    prob_survival_next_month = 1 - stats.norm.cdf(age + (1 / 12), loc=life_mean, scale=life_std)
    return prob_survival_next_month / prob_survival_till_now, age + (1 / 12)


def surv_decision(prob):
    return random.random() < prob

def survival_arr_years(sim_years, country, age, sex):
    year = 0
    res_array = []
    life_slope, life_intercept, life_std = get_life_exp_vals(country, sex)
    
    while year < sim_years:
        prob, age = surv_prob_next_year(age, life_slope, life_intercept, life_std)    
        res = surv_decision(prob)
        if res == False:
            res_array.extend([False] * (sim_years - year))
            return res_array
        else:
            res_array.append(True)
            year += 1

    return res_array

def survival_arr_months(sim_years, country, age, sex):
    year = 0
    res_array = []
    life_slope, life_intercept, life_std = get_life_exp_vals(country, sex)

    while year < sim_years:
        for month in range(0, 12): # Iterate through all the months!
            prob, age = surv_prob_next_month(age, life_slope, life_intercept, life_std)
            res = surv_decision(prob)
            if res == False:
                res_array.extend([False] * (12 - month))
                res_array.extend([False] * (sim_years - year - 1) * (12))
                return res_array
            else:
                res_array.append(True)
        
        if res_array[-1] == False:
            res_array.extend([False] * (sim_years - year) * 12)
            return res_array
        
        year += 1

    return res_array 
            
if __name__ == "__main__":
    country = 'United States of America'
    sex = 'Male'
    age = 50.0
    life_slope, life_intercept, life_std = get_life_exp_vals(country, sex)
    print("success")

