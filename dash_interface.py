# Source Link for further steps: https://github.com/Coding-with-Adam/Dash-by-Plotly/blob/master/Other/Dash_Introduction/intro.py



import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output


app = Dash(__name__)



# App layout
app.layout = html.Div([



    html.H1("Retirement Portfolio Withdrawal Rate Simulation", style={'text-align' : 'center'}),

    html.Div(className='row', children=[

        html.Div(children=[
            html.Label(["Age:"], style={'font-weight' : 'bold', 'text-align' : 'center'}),
                    dcc.Dropdown(
                        id="age",
                        options=[x for x in range(1, 120)],
                        value=62,
                        clearable=False,
                        searchable=False,
                    ),
        ], style=dict(width='33.33%')),

        html.Div(children=[
            html.Label(["Sex:"], style={'font-weight' : 'bold', 'text-align' : 'center'}),
                    dcc.Dropdown(
                        id="sex",
                        options=["Male", "Female"],
                        value="Male",
                        clearable=False,
                        searchable=False,
                    ),
        ], style=dict(width='33.33%')),

        html.Div(children=[
            html.Label(["Country:"], style={'font-weight' : 'bold', 'text-align' : 'center'}),
                    dcc.Dropdown(
                        id="country",
                        options=[x for x in range(1, 120)],
                        value=62,
                        clearable=False,
                        searchable=False,
                    ),
        ], style=dict(width='33.33%')),
        




    ],style=dict(display='flex')), 


    


    html.Div(id='output_container', children=[]),

    html.Br(),
    dcc.Graph(id='simulation', figure={})


])





if __name__ == "__main__":
    app.run_server(debug=True)