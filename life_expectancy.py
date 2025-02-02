# Data Sources: 
# World Health Organization (WHO) Global Health Observatory Data 
# http://pophealthmetrics.biomedcentral.com/articles/10.1186/s12963-016-0094-0#Sec7

# All imports
import pandas as pd
from scipy import stats



def get_life_expectancy(country, input_age, sex,
                        STD_MALES=5.6, STD_FEMALES=3.6):
    """
    

    """
    
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

    life_mean = slope * input_age + intercept


    life_std = STD_MALES if sex == 'Male' else STD_FEMALES
    return life_mean, life_std


if __name__ == "__main__":
    country = 'United States of America'
    sex = 'Male'
    age = 50.0
    print(get_life_expectancy(country, age, sex))