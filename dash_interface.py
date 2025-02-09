# Next step, watch and understand this video: https://www.youtube.com/watch?v=pNMWbY0AUJ0&t=284s


# Source Link for further steps: https://github.com/Coding-with-Adam/Dash-by-Plotly/blob/master/Other/Dash_Introduction/intro.py

# Notes, include a FAQ at the end of the page where you answer questions such as: 1.) Why does the year only include 252 days?


import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, dcc, html, Input, Output, callback

import life_expectancy as lf
import stock_movements as sm

country_options = lf.get_countries()
index_options = ['NDX', 'SPX']


app = Dash(__name__)



# App layout
app.layout = html.Div([



    html.H1("Retirement Portfolio Withdrawal Rate Simulation", style={'text-align' : 'center'}),

    html.Div(children=[
        
        # Age choice
        html.Label(["Age:"], style={'font-weight' : 'bold', 'text-align' : 'center'}),
        dcc.Dropdown(
                    id="age",
                    options=[x for x in range(1, 120)],
                    value=62,
                    clearable=False,
                    searchable=False,
                    ),
        html.Br(),

        # Sex choice
        html.Label(["Sex:"], style={'font-weight' : 'bold', 'text-align' : 'center'}),
        dcc.Dropdown(
                    id="sex",
                    options=["Male", "Female"],
                    value="Male",
                    clearable=False,
                    searchable=False,
                    ),
        html.Br(),

        # Country choice
        html.Label(["Country:"], style={'font-weight' : 'bold', 'text-align' : 'center'}),
        dcc.Dropdown(
                    id="country",
                    options=country_options,
                    value="Switzerland",
                    clearable=False,
                    searchable=True,
                    ),
        html.Br(),
        
    ],style={'padding' : 10, 'flex' : 1}), 


    html.Div(children=[
        
        # Balance choice
        html.Label(['Start Balance'], style={'font-weight' : 'bold', 'text-align' : 'center'}),
        dcc.Input(id='balance', type='number', placeholder=100000,
                  min=0),
        html.Br(),

        # Index choice
        html.Label(['Index:'], style={'font-weight' : 'bold', 'text-align' : 'center'}),
        dcc.Dropdown(
                    id="index",
                    options=index_options,
                    value="NDX",
                    clearable=False,
                    searchable=True,
                    ),
        html.Br(),

        # Withdrawal rate choice
        html.Label(['Withdrawal rate'], style={'font-weight' : 'bold', 'text-align' : 'center'}),
        dcc.Input(id='wd_rate', type='number', placeholder=0.1,
                  min=0, max=1, step=0.1),
        html.Br(),


    ]),

    

    
    dcc.Markdown(children='', id='displayed_text'),


    html.Br(),
    dcc.Graph(id='simulation', figure={})


])

@callback(
    Output('displayed_text', 'children'),
    Input('age', component_property='value'),
    Input('sex', component_property='value'),
    Input('country', component_property='value')
)

def update_text(age, sex, country):
    print(type(age))
    print(type(sex))
    print(type(country))
    return f"The values chosen by the user are: age: {age}, sex: {sex}, country: {country}"




if __name__ == "__main__":
    app.run_server(debug=True)