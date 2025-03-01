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

from dash import Dash, dcc, html, Input, Output, callback, dash_table, State
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

import life_expectancy as lf
import stock_movements as sm


#country_options = lf.get_countries()
country_options = ["America", "Switzerland"]
index_options = ['NDX', 'SPX']

# Precalculated Results
df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder2007.csv')


app = Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])
load_figure_template("SANDSTONE")

# SOURCE: https://community.plotly.com/t/holy-grail-layout-with-dash-bootstrap-components/40818/2
header_height, footer_height = "6rem", "5rem"
sidebar_width, ads_width = "12rem", "12rem"

HEADER_STYLE = {
    "position" : "fixed",
    "top" : 0,
    "left" : 0,
    "right" : 0,
    "height" : header_height,
    "padding" : "1rem 0rem",
    "background-color" : "#596e79",
    "text-color" : "white",
    "text-align" : "center",
}

SIDEBAR_STYLE = {
    "position" : "fixed",
    "padding" : "0.5rem 0rem",
    "top": header_height,
    "left": 0,
    "bottom": footer_height,
    "width": sidebar_width,
    "background-color": "#c7b198",
}

SIDEBAR_DROPDOWN_STYLE = {
    "width": "6.5rem",
    "text-align" : "center",
    "height" : "1.9rem",
    "display": "inline-block"
}

SIDEBAR_INPUT_STYLE = {
    "width": "6.5rem",
    "text-align" : "center",
    "height" : "1.8rem",
    "font-size" : "13px",
}

SIDEBAR_CONTENT_STYLE = {
    "width": "12rem",
    "text-align" : "center",
    "font-size" : "15px",}

FOOTER_STYLE = {
    "position" : "fixed",
    "bottom" : 0,
    "left" : 0,
    "right" : 0,
    "height" : footer_height,
    "text-align" : "center",
    "background-color" : "#dfd3c3",
} 

CONTENT_STYLE = {
    "margin-top" : header_height,
    "margin-left" : sidebar_width,
    "margin-right" : ads_width,
    "margin-bottom" : footer_height,
    "background-color" : "#f0ece2",
}

ADS_STYLE = {
    "position" : "fixed",
    "top" : header_height,
    "right" : 0,
    "bottom" : footer_height,
    "width" : ads_width,
    "padding" : "0.5rem 0rem",
    "background-color" : "#c7b198",
    "text-align" : "center",
}

header = html.Div([
    html.H1("Retirement Portfolio \nWithdrawal Simulation", style={"color" : "white", "font-size" : "40px"})
], style=HEADER_STYLE)

footer = html.Div([
    html.H2("Footer"),
    html.P("Footer Example Line!"),
], style=FOOTER_STYLE)

ads = html.Div([
    html.H2("Adds"),
    html.P("Example Add field"),
], style=ADS_STYLE)

content_list = [html.H2("Example Content")]
for i in range(100):
    content_list.append(html.P(f"LOOK AT THIS {i}"))

content = html.Div(
    content_list
, style=CONTENT_STYLE)


sidebar = html.Div([
    html.H2("Filters", style={"text-align": "center", "font-size" : "30px"}),

    html.Div([
        html.Label(["Portfolio Size:"]),
    ], style=SIDEBAR_CONTENT_STYLE),
    
    html.Div([
        dcc.Input(id='balance', value="100'000 USD",
                style=SIDEBAR_INPUT_STYLE),
    ], style=SIDEBAR_CONTENT_STYLE),
    
    html.Div([
        html.Label(["Yearly Withdrawal Rate:"]),   
    ], style=SIDEBAR_CONTENT_STYLE),
    
    html.Div([
        dcc.Input(id='wd_rate', value="10%",
                style=SIDEBAR_INPUT_STYLE),
    ], style=SIDEBAR_CONTENT_STYLE),

    html.Div([
        dbc.Button(
            "Further Filters",
            id="collapse-button",
            className="mb-3",
            color="primary",
            n_clicks=0,
        ),
        
        dbc.Collapse(
            html.Div([html.Div([
                html.Label(["Age:"]),   
            ], style=SIDEBAR_CONTENT_STYLE),

            html.Div([
                dcc.Dropdown(
                        id="age",
                        options=[x for x in range(1, 120)],
                        value=62,
                        clearable=False,
                        searchable=False,
                        style=SIDEBAR_DROPDOWN_STYLE),
            ], style=SIDEBAR_CONTENT_STYLE),

            html.Div([
                html.Label(["Country of Residence:"]),   
            ], style=SIDEBAR_CONTENT_STYLE),

            html.Div([
                dcc.Dropdown(
                        id="country",
                        options=country_options,
                        value="America",
                        clearable=False,
                        searchable=True,
                        style=SIDEBAR_DROPDOWN_STYLE),
            ], style=SIDEBAR_CONTENT_STYLE),

            html.Div([
                html.Label(["Sex:"]),   
            ], style=SIDEBAR_CONTENT_STYLE),

            html.Div([
                dcc.Dropdown(
                        id="sex",
                        options=["Male", "Female"],
                        value="Male",
                        clearable=False,
                        searchable=False,
                        style=SIDEBAR_DROPDOWN_STYLE),
            ], style=SIDEBAR_CONTENT_STYLE),

            html.Div([
                html.Label(["Index Choice:"]),   
            ], style=SIDEBAR_CONTENT_STYLE),

            html.Div([
                dcc.Dropdown(
                        id="index",
                        options=index_options,
                        value="NDX",
                        clearable=False,
                        searchable=True,
                        style=SIDEBAR_DROPDOWN_STYLE),
            ], style=SIDEBAR_CONTENT_STYLE),

            html.Div([
                html.Label(["Number of Simulations:"]),   
            ], style=SIDEBAR_CONTENT_STYLE),

            html.Div([
                dcc.Input(
                    id='sim_n', value="5",
                    style=SIDEBAR_INPUT_STYLE),
            ], style=SIDEBAR_CONTENT_STYLE),

            html.Div([
                html.Label(["Years to be Simulated:"]),   
            ], style=SIDEBAR_CONTENT_STYLE),

            html.Div([
                dcc.Input(
                    id='sim_years', value="5",
                    style=SIDEBAR_INPUT_STYLE),
            ], style=SIDEBAR_CONTENT_STYLE),]),
            id="collapse",
            is_open=False,
        ),
    ], style=SIDEBAR_CONTENT_STYLE),

], style=SIDEBAR_STYLE)


app.layout = html.Div([header, content, sidebar, ads, footer], style={"font-family" : "Verdana"})

@app.callback(
    Output("collapse", "is_open"),
    [Input("collapse-button", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

"""@callback(
    Output('displayed_text', 'children'),
    Input('age', component_property='value'),
    Input('sex', component_property='value'),
    Input('country', component_property='value'),
    Input('balance', component_property='value'),
    Input("wd_rate", component_property='value')
)

def update_text(age, sex, country, balance, wd_rate):
    return f"The values chosen by the user are: age: {age}, sex: {sex}, country: {country}, balance: {balance}, withdrawal_rate: {wd_rate}"
"""

# Update the graph!
"""@callback(
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

    return graph"""

if __name__ == "__main__":
    app.run_server(debug=True)