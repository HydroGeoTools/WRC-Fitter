from dash import Dash, html, dcc
import dash_bootstrap_components as dbc


FOOTER_STYLE = {
    "position": "fixed",
    "bottom": 0,
    "left": 0,
    "right": 0,
    "height": 50,
    "padding": "1rem 1rem",
    "background-color": "white",
}



class WRCFitterUI:
    def __init__(self):
        self.layout = html.Div([
            self._header(),
            dbc.Row([
                dbc.Col([html.H1("WRC-Fitter", style={'textAlign':'center'})]),
                dbc.Col([
                    dbc.Button("Get help!", href="https://docs.hydrogeotools.com/wrc-fitter.html"),
                ], width="auto"),
            ], justify="end", align="center"),
            html.Hr(),
            dbc.Row([
                dbc.Col(self._visualization_pannel(), width=8),
                dbc.Col([
                    dbc.Row(self._calibration_pannel()),
                    dbc.Row(self._results_pannel())
                ]),
            ]),
            self._footer(),
        ])
        return
    
    def _header(self):
        contents = dbc.Alert([
            "This is the beta version of WRC-Fitter application. Let us know what you think at ",
            html.A("contact@hydrogeotools.com", href="mailto:contact@hydrogeotools.com"),
        ])
        return contents
    
    def _visualization_pannel(self):
        header = [
            html.H3("Experimental data", className="card-title"),
        ]
        upload = [
            html.H6("Upload your experimental Water Retention Curve: ", id="upload-text"),
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select a file'),
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
        ]
        graph = [
            html.H6("Visualize your data:", id="data-vis-text"),
            dcc.Graph(id='graph-content'),
            dbc.Button('Download a sample curve', id='button-sample-wrc', n_clicks=0),
            dcc.Download(id="download-sample-curve"),
        ]
        visualization_card = dbc.Card(
            dbc.CardBody(
                header +
                upload +
                graph
            ),
            style={"width": "100%"}
        )
        return visualization_card
    
    def _calibration_pannel(self):
        header = [
            html.H3("Calibration properties",className="card-title")
        ]
        fit_type = [
            html.H6("Select fit type: ", id="fit-text"),
            dbc.RadioItems(["Best fit with RMSE (deterministic)", "Quantile regression (statistical)"], "Best fit with RMSE (deterministic)", id="radio-fit-selector"),
            html.Hr(),
        ]
        model = [
            html.H6("Select model: ", id="model-text"),
            dbc.RadioItems(["Brooks and Corey (1964)", "Fredlund and Xing (1994)", "Van Genuchten (1980)"], "Van Genuchten (1980)", id="radio-model-selector"),
            html.Hr(),
        ]
        opt_button = [dbc.Button('Optimize', id='optimize_button', n_clicks=0)]
        calibration_card = dbc.Card(
            dbc.CardBody(
                header +
                fit_type +
                model +
                opt_button
            ),
            style={"width": "100%"}
        )
        return calibration_card
    
    def _results_pannel(self):
        header = [
            html.H3("Results"),
        ]
        params = [
            html.H6("Calibrated model parameters:", id="out-params-text"),
            html.Div(["Please optimize to view the fitted parameters."], id='result-data'),
        ]
        download = [
            html.H6("Download results in output format:", id="out-results-format-text"),
            dcc.Dropdown([
                "Excel (.xlsx)",
                "CSV (.csv)",
                "HydroGeoSphere (.mprops)"
            ], "CSV (.csv)", id="dropdown-out-format-selector"),
            dbc.Button('Download', id='download-results-btn', n_clicks=0),
            dcc.Download(id="download-results"),
        ]
        results_card = dbc.Card(
            dbc.CardBody(
                header
                + params
                + download
            )
        )
        return results_card
    
    def _footer(self):
        contents = [ html.P([
            "Application created by HydroGeoTools. See ", 
            html.A("www.hydrogeotools.com", href="https://www.hydrogeotools.com"),
            " for more contents.",
        ]) ]
        footer = html.Footer(contents, style=FOOTER_STYLE)
        return footer
    
    def packLayout(self):
        return dbc.Container(self.layout, fluid=True)
