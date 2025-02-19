# Next step, watch and understand this video: https://www.youtube.com/watch?v=pNMWbY0AUJ0&t=284s


# Source Link for further steps: https://github.com/Coding-with-Adam/Dash-by-Plotly/blob/master/Other/Dash_Introduction/intro.py

# Notes, include a FAQ at the end of the page where you answer questions such as: 1.) Why does the year only include 252 days?

# Next steps: include a callback function for the table!
# Adjust the layout, so it works for all screen sizes not just extra large!
# Include a Collabse to hide Country & Gender info, but the user can change them!
# Make the design very beautiful!

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc

import life_expectancy as lf
import stock_movements as sm

country_options = lf.get_countries()
index_options = ['NDX', 'SPX']

# Precalculated Results
df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder2007.csv')


app = Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])

# App layout
app.layout = html.Div([
    dbc.Row(dbc.Col(html.H1("Retirement Portfolio \nWithdrawal Simulation"),
                    width={'size' : "auto", 'offset' : 3})),

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
                  min=0, value=100000),
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
                  min=0, max=1, step=0.1, value=0.1),
        html.Br(),

        # Simulation years choice
        html.Label(['Simulation Years'], style={'font-weight' : 'bold', 'text-align' : 'center'}),
        dcc.Input(id='sim_years', type='number', 
                  placeholder=5, min=1, max=100, step=1, value=5),
        html.Br(),

        # Number of simulations choice
        html.Label(['Number of Simulations'], style={'font-weight' : 'bold', 'text-align' : 'center'}),
        dcc.Input(id='sim_n', type='number',
                  placeholder=5, min=1, max=10000, step=1, value=5),
        html.Br(),


    ]),

    
    dcc.Markdown(children='', id='displayed_text'),
    html.Br(),


    # Table showing the aggregated results
    dash_table.DataTable(id="res_table", data=df.to_dict('records')),
    html.Br(),
    
    # Graph showing the advanced Simulations for further analysis
    dcc.Graph(id='simulation', figure={}),
    html.Br(),

])

@callback(
    Output('displayed_text', 'children'),
    Input('age', component_property='value'),
    Input('sex', component_property='value'),
    Input('country', component_property='value'),
    Input('balance', component_property='value'),
    Input("wd_rate", component_property='value')
)

def update_text(age, sex, country, balance, wd_rate):
    return f"The values chosen by the user are: age: {age}, sex: {sex}, country: {country}, balance: {balance}, withdrawal_rate: {wd_rate}"


# Update the graph!
@callback(
    Output('simulation', 'figure'),
    Input('age', 'value'),
    Input('sex', 'value'),
    Input('country', 'value'),
    Input('balance', 'value'),
    Input("wd_rate", 'value'),
    Input("index", "value"),
    Input("sim_years", "value"),
    Input("sim_n", "value")
)
def update_graph(age, sex, country, balance, wd_rate, index, sim_years, sim_n):
    index_mu, index_sigma = sm.get_index_data(index)

    balances, withdrawal_returns = sm.brown_motion_drift_plus_wd(balance, index_mu, index_sigma, 
                                                                sim_n,
                                                                sim_years, wd_rate,
                                                                yearly_withdrawels=True,
                                                                withdraw_after_first_year=False)
    portfolio_is_lost, portfolio_loss_idx = sm.find_zero_points(balances, sim_n)
    tot_w_before_loss = sm.total_withdrawels_before_loss(withdrawal_returns, portfolio_loss_idx, sim_n)

    # survival_arr = lf.survival_sim(sim_years, country, age, sex, sim_n)

    graph = None

    return graph

if __name__ == "__main__":
    app.run_server(debug=True)