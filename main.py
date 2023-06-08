import base64
import datetime
import io

from dash import Dash, html, dcc, callback, Output, Input, State
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import flask

import fitter


instructions = [
    "1. Prepare a CSV file (comma separated) the first column being the water succion (Psi) and the second the water content (Theta).",
    "2. Drag and drop or upload this file. The experimental water retention curve should be plotted on the below graph.",
    "3. Select the model to be fitted (default = Van Geunchten)",
    "4. Click on the button optimize to search for the best model parameters (best means with the lowest Root Mean Squared Error - RMSE).",
    "5. Your results appear !",
]

layout = [
    html.H1('Water Retention Curve Fitter', style={'textAlign':'center'}),
    html.H2('Instructions', style={'textAlign':'center'}),
] + [
    html.P(instruction, style={'textAlign':'center'}) for instruction in instructions
] + [
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select a file')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
    ),
    html.Hr(),  # horizontal line
    dcc.Graph(id='graph-content'),
    html.Hr(),  # horizontal line
    html.Div([
        html.P("Select model: ", id="model-text"),
        dcc.Dropdown(["Brooks and Corey", "Fredlund and Xing", "Van Genuchten"], "Van Genuchten", id="dropdown-model-selector"),
        html.Button('Optimize', id='optimize_button', n_clicks=0),
    ]),
    html.Hr(),  # horizontal line
    html.H2('Results', style={'textAlign':'center'}),
    html.Div(id='result-data'),
]



#TODO: download the csv and put it on /tmp
def parse_contents(contents, filename):
    if contents is None: return
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')),
            )
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        #clean data
        mask_nan = df.isna().sum(axis=1) == 0
        df = df[mask_nan]
    except Exception as e:
        print(e)

    return df


server = flask.Flask(__name__)
app = Dash(__name__, title="WRC-Fitter", server=server)
app.layout = html.Div(layout)

@app.callback(
    Output('graph-content', 'figure', allow_duplicate=True),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def update_graph(contents,filename):
    data = parse_contents(contents, filename)
    header = data.columns.tolist()
    xdata = np.array(data.iloc[:,0])
    ydata = np.array(data.iloc[:,1])
    fig = go.Figure(data=go.Scatter(x=xdata, y=ydata, mode='markers'))
    return fig


@app.callback(
    Output('graph-content', 'figure'),
    Output('result-data', 'children'),
    Input('optimize_button', 'n_clicks'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('dropdown-model-selector', 'value'),
)
def optimize(btn, contents, filename, model):
    if contents is None: return go.Figure(), html.Div()
    print('optimize')
    data = parse_contents(contents, filename)
    header = data.columns.tolist()
    xdata = np.array(data.iloc[:,0])
    ydata = np.array(data.iloc[:,1])
    res, func = fitter.fit(xdata, ydata, model)
    res95, func = fitter.fit(xdata, ydata, model, 0.95)
    res05, func = fitter.fit(xdata, ydata, model, 0.05)
    x_th = np.linspace(np.min(xdata), np.max(xdata), 100)
    x_th = np.append(x_th, xdata)
    x_th.sort()
    RMSE = np.sqrt(res.fun)
    # print results
    children = [
        html.P(f"RMSE (the lower the better): {RMSE:.3e}", style={'textAlign':'center'}),
        html.P(f"95th quantile loss (the lower the better): {res95.fun:.3e}", style={'textAlign':'center'}),
        html.P(f"5th quantile loss (the lower the better): {res05.fun:.3e}", style={'textAlign':'center'}),
    ]
    out_param_str = ""
    for i,name in enumerate(fitter.model_output_name[model]):
        out_param_str += f"{name}: {res.x[i]:.3e} ({res05.x[i]:.3e},{res95.x[i]:.3e}) ; "
    children += [html.P(out_param_str, style={'textAlign':'center'})]
    
    #plot
    y_opt = func(x_th, res.x)
    y_95 = func(x_th, res95.x)
    y_05 = func(x_th, res05.x)
    #size_stat = 100
    #random_gen = np.random.default_rng()
    #params_random = np.transpose([
    #    random_gen.normal(res.x[i],perr[i],size=size_stat) for i in range(len(res.x))
    #])
    #y_stats = [
    #    func(x_th, params) for params in params_random
    #]
    fig = go.Figure(
        data=[
            go.Scatter(x=x_th, y=y_05, line={"dash":"solid", "color":"silver"}, marker=None, name="5th quantile"),
            go.Scatter(x=x_th, y=y_95, line={"dash":"solid", "color":"gold"}, marker=None, name="95th quantile"),
        ] + [
            go.Scatter(x=x_th, y=y_opt, line={"dash":"solid", "color":"red"}, marker=None, name=f"Fitted {model}"),
        ] + [
            go.Scatter(x=xdata, y=ydata, mode='markers', marker={"color":"blue"}, name="Data"),
        ]
    )
    return fig, children

if __name__ == '__main__':
    app.run_server(debug=True)
