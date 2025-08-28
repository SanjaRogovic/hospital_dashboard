import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import sass

compiled_css = sass.compile(filename="assets/style.scss")
with open("assets/style.css", "w") as f:
    f.write(compiled_css)

def load_data():
    data = pd.read_csv('assets/healthcare.csv')
    data["Billing Amount"] = pd.to_numeric(data["Billing Amount"], errors='coerce') #coerce replaces error into NaN
    data["Date of Admission"] = pd.to_datetime(data["Date of Admission"])
    data["YearMonth"] = data["Date of Admission"].dt.to_period('M') #creating this as it does not exists in csv
    return data

data = load_data()
num_records = len(data)
avg_billing = data["Billing Amount"].mean()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP]) #create an app and add style sheet

#container is a class that takes a list, it contains of rows and within rows columns
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Healthcare Dashboard"), width=15, className="text-center my-5")
    ]),

    #hospital statistics
    dbc.Row([
        dbc.Col(html.Div(f"Total Patient Records: {num_records}", className="text-center my-3 top-text"), width=5),
        dbc.Col(html.Div(f"Average Billing Amount: {avg_billing:,.2f}", className="text-center my-3 top-text"), width=5) #.2f means round up the value
    ], className="mb-5"),

    #demographics - male or female
    dbc.Row([
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    html.H4("Patient Demogrpahics", className="card-title"),
                    dcc.Dropdown(
                        id="gender-filter",
                        options=[{"label": gender, "value": gender} for gender in data["Gender"].unique()],
                        value=None,
                        placeholder="Select a Gender"
                    ),
                    dcc.Graph(id="age-distribution")
                ])
            )
        ], width=6),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Medical Condition Distribution", className="card-title"),
                    dcc.Graph(id="condition-distribution")
                ])
            ])
        ], width=6)        
    ]),

    #insurance providers
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Insurance Provider Comparison", className="card-title"),
                    dcc.Graph(id="insurance-comparison")
                ])
            ])
        ], width=12)
    ]),

    #billing distribution
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Billing Amount Distribution", className="card-title"),
                    dcc.Slider(
                        id="billing-slider",
                        min=data["Billing Amount"].min(),
                        max=data["Billing Amount"].max(),
                        value=data["Billing Amount"].median(),
                        marks={int(value): f"${int(value):,}" for value in data["Billing Amount"].quantile([0, 0.25, 0.5, 0.75, 1]).values},
                        step=100
                    ),
                    dcc.Graph(id="billing-distribution")
                ])
            ])
        ], width=12)
    ]),

    #trends in admission
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Trends in Admission", className="card-title"),
                    dcc.RadioItems(
                        id="chart-type",
                        options=[{"label": "Line Chart", "value": "line"}, {"label": "Bar Chart", "value": "bar"}],
                        value="line",
                        inline=True,
                        className="mb-4"
                    ),
                    dcc.Dropdown(
                        id="condition-filter",
                        options=[{"label": condition, "value": condition} for condition in data["Medical Condition"].unique()],
                        value=None,
                        placeholder="Select a Medical Condition"
                    ),
                    dcc.Graph(id="admission-trends")
                ])
            ])
        ], width=12)
    ])
], fluid=True)

#create callbacks

@app.callback(
    Output("age-distribution", "figure"),
    Input("gender-filter", "value")
)

def update_distribution(selected_gender):
    if selected_gender:
        filtered_data_frame = data[data["Gender"] == selected_gender]
    else:
        filtered_data_frame = data
    
    if filtered_data_frame.empty:
        return {}
    
    fig = px.histogram(
        filtered_data_frame,
        x="Age",
        nbins=10,
        color="Gender",
        title="Age Distribution by Gender",
        color_discrete_sequence=["#636EFA", "#EF553B"]
    )

    return fig


@app.callback(
    Output("condition-distribution", "figure"),
    Input("gender-filter", "value")
)

def update_medical_condition(selected_gender):
    filtered_data_frame = data[data["Gender"] == selected_gender] if selected_gender else data
    fig = px.pie(filtered_data_frame, names="Medical Condition", title="Medical Condiiton Distribution")
    return fig


@app.callback(
    Output("insurance-comparison", "figure"), 
    Input("gender-filter", "value")
)

def update_insurance(selected_gender):
    filtered_data_frame = data[data["Gender"] == selected_gender] if selected_gender else data
    fig = px.bar(
        filtered_data_frame,
        x="Insurance Provider",
        y="Billing Amount",
        color="Medical Condition",
        barmode="group",
        title="Insurance Provider Price Comparison",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    return fig


@app.callback(
    Output("billing-distribution", "figure"),
    [Input("gender-filter", "value"), 
     Input("billing-slider", "value")]
)

def update_billing(selected_gender, slider_value):
    filtered_data_frame = data[data["Gender"] == selected_gender] if selected_gender else data
    filtered_data_frame = filtered_data_frame[filtered_data_frame["Billing Amount"] <= slider_value]

    fig = px.histogram(
        filtered_data_frame,
        x="Billing Amount",
        nbins=10,
        title="Billing Amount Distribution"
    )
    return fig


@app.callback(
    Output("admission-trends", "figure"),
    [Input("chart-type", "value"),
     Input("condition-filter", "value")]
)

def update_admission(chart_type, selected_condition):
    filtered_data_frame = data[data["Medical Condition"] == selected_condition] if selected_condition else data
    trend_data_frame = filtered_data_frame.groupby("YearMonth").size().reset_index(name="Count")
    trend_data_frame["YearMonth"] = trend_data_frame["YearMonth"].astype(str)


    if chart_type == "line":
        fig = px.line(trend_data_frame, x="YearMonth", y="Count", title="Admission Trends over Time")
    else:
        fig = px.bar(trend_data_frame, x="YearMonth", y="Count", title="Admission Trends over Time")

    return fig


if __name__ == "__main__":
    app.run(debug=True)