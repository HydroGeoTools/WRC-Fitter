import base64
import datetime
import io

from dash import Dash, html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np

import fitter
from main_ui import WRCFitterUI



app = Dash(__name__, title="WRC-Fitter", external_stylesheets=[dbc.themes.BOOTSTRAP])
main_ui = WRCFitterUI()
app.layout = main_ui.packLayout()


#Some global variables
ABBREV_MODEL = {
    "Brooks and Corey (1964)": "BC",
    "Fredlund and Xing (1994)": "FX",
    "Van Genuchten (1980)": "VG",
}
ABBREV_TO_MODEL = {
    val:key for key,val in ABBREV_MODEL.items()
}


def parse_contents(contents, filename):
    if contents is None: return
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')),
                sep=None,
                engine="python",
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
    fig.update_xaxes(type="log")
    fig.update_layout(xaxis_title=header[0], yaxis_title=header[1])
    return fig


@app.callback(
    Output('graph-content', 'figure'),
    Output('result-data', 'children'),
    Input('optimize_button', 'n_clicks'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('radio-fit-selector', 'value'),
    State('radio-model-selector', 'value'),
    #State('btn-download-res', 'hidden'),
    prevent_initial_call=True,
)
def optimize(btn, contents, filename, fit_type, model):
    if contents is None: 
        return go.Figure(), html.Div()
    
    #parse inputs
    data = parse_contents(contents, filename)
    header = data.columns.tolist()
    xdata = np.array(data.iloc[:,0])
    ydata = np.array(data.iloc[:,1])
    #prepare output
    if np.min(xdata) == 0:
        min_x_th_log = np.log10(np.min(xdata[xdata != 0]))-1
    else:
        min_x_th_log = np.log10(np.min(xdata))
    x_th = np.logspace(min_x_th_log, np.log10(np.max(xdata)), 200)
    x_th = np.append(x_th, xdata)
    x_th.sort()
    
    #fit
    if fit_type == "Best fit with RMSE (deterministic)":
        res, func = fitter.fit(xdata, ydata, model)
        loss = np.sqrt(res.fun)
        graph_data = [
            {
                "x" : x_th,
                "y" : func(x_th, res.x),
                "line" : {"dash":"solid", "color":"red"}, 
                "marker" : None,
                "name" : f"Fitted {model} (Best fit - RMSE)",
            }
        ]
        
    elif fit_type == "Quantile regression (statistical)":
        resmax, func = fitter.fit(xdata, ydata, model, 0.95)
        res50, func = fitter.fit(xdata, ydata, model, 0.50)
        resmin, func = fitter.fit(xdata, ydata, model, 0.05)
        loss = np.sqrt(resmax.fun**2 + res50.fun**2 + resmin.fun**2)
        graph_data = [
            {
                "x" : x_th,
                "y" : func(x_th, resmin.x),
                "line" : {"dash":"solid", "color":"silver"}, 
                "marker" : None,
                "name" : f"5th Quantile {model}",
            },
            {
                "x" : x_th,
                "y" : func(x_th, res50.x),
                "line" : {"dash":"solid", "color":"red"}, 
                "marker" : None,
                "name" : f"50th Quantile {model}",
            },
            {
                "x" : x_th,
                "y" : func(x_th, resmax.x),
                "line" : {"dash":"solid", "color":"gold"}, 
                "marker" : None,
                "name" : f"95th Quantile {model}",
            }
        ]
    
    # print text results
    if fit_type == "Best fit with RMSE (deterministic)":
        table_header = html.Thead(
            html.Tr([
                html.Th(ABBREV_MODEL[model] + " Parameters"),
                html.Th("Best fit (RMSE)")
            ])
        )
        table_body = html.Tbody([
            html.Tr(
                [html.Td(name), html.Td(f"{res.x[i]:.6e}")]) for i,name in enumerate(fitter.model_output_name[model]
            )
        ])
    
    elif fit_type == "Quantile regression (statistical)":
        table_header = html.Thead(
            html.Tr([
                html.Th(ABBREV_MODEL[model] + " Parameters"),
                html.Th("5th Quantile"),
                html.Th("50th Quantile"),
                html.Th("95th Quantile")
            ])
        )
        table_body = html.Tbody([
            html.Tr(
                [html.Td(name), html.Td(f"{resmin.x[i]:.6e}"), html.Td(f"{res50.x[i]:.6e}"), html.Td(f"{resmax.x[i]:.6e}")]) for i,name in enumerate(fitter.model_output_name[model]
            )
        ])
    
    children = html.Div([
        dbc.Table([table_header, table_body], bordered=True), 
        html.P("The above parameters table is copy-pastable in Excel")
    ])
    
    #plot
    data = [go.Scatter(**plot) for plot in graph_data]
    data += [go.Scatter(x=xdata, y=ydata, mode='markers', marker={"color":"blue"}, name="Data")]
    fig = go.Figure(
        data=data,
        layout = {
            "legend": {"xanchor":"right", "yanchor":"top"},
            "margin": dict(l=80, r=80, t=100, b=80),
        },
    )
    fig.update_xaxes(type="log")
    fig.update_layout(xaxis_title=header[0], yaxis_title=header[1])
    
    return fig, children


@app.callback(
    Output("download-results", "data"),
    Input("download-results-btn", "n_clicks"),
    State("dropdown-out-format-selector", "value"),
    State("result-data", "children"),
    prevent_initial_call=True,
)
def download_results(n_clicks, fmt, fit_res_table):
    #reparse res_table
    #this is awkward because the table object deeply nested...
    the_table = fit_res_table['props']['children'][0]
    column_header = [
        x['props']['children'] for x in the_table['props']['children'][0]['props']['children']['props']['children']
    ]
    model_str = column_header[0].split()[0]
    func = fitter.get_WRC_function(ABBREV_TO_MODEL[model_str])
    #note: parameter are writted sequentially in the table, so if we pass value to the function in the order we are fine!
    fit_params = []
    for nested_dict in the_table['props']['children'][1]['props']['children']:
        params = []
        for i in range(1,len(nested_dict['props']['children'])):
            params.append(float(nested_dict['props']['children'][i]['props']['children']))
        fit_params.append(params)
    fit_params = [[x[i] for x in fit_params] for i in range(len(fit_params[0]))]
    #plot function
    x_th = np.logspace(-2,6, 1000)
    y_th = [func(x_th, params) for params in fit_params]
    df = pd.DataFrame(
        {'Pressure': x_th, **{column_header[i+1]:y_th[i] for i in range(len(fit_params))}}
    )
    #send!
    output = io.BytesIO()
    if fmt == "CSV (.csv)":
        df.to_csv(output, index=False)
    elif fmt == "Excel (.xlsx)":
        df.to_excel(output, index=False)
    data = output.getvalue()
    return dcc.send_bytes(data, "calibrated_WRC."+fmt.split('.')[1].split(')')[0])

if __name__ == "__main__":
    app.run_server(debug=True)
