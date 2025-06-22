#!/usr/bin/env python
# coding: utf-8

# ## Dissertation Gantt Tracker Dashboard

# 
# 
# 
# This Dash app visualizes and manages the progress of a dissertation project
# as an editable Gantt chart. It allows for task tracking, progress updates,
# and supervisor comments. Edits made in the table are persisted to CSV.
# 
# Author: Pritid Nandy
# Date: June 2025

# In[1]:


import os
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State, dash_table
from flask import send_from_directory
import datetime

# Constants
DOCS_FOLDER = "docs"
if not os.path.exists(DOCS_FOLDER):
    os.makedirs(DOCS_FOLDER)

# Load data
df = pd.read_csv("gantt_data.csv")
df['Start'] = pd.to_datetime(df['Start'])
df['Finish'] = pd.to_datetime(df['Finish'])

def create_spirit_glass_chart_from_csv(filepath="eu_exports.csv"):
    import plotly.graph_objects as go

    df = pd.read_csv(filepath)

    # Clean export values: remove £ and commas, convert to float
    df["EU Export (£)"] = df["EU Export (£)"].replace('[£,]', '', regex=True).astype(float)

    # Keep only spirit categories (excluding sugary waters, cider, etc.)
    spirit_df = df[df["Product"].str.contains("Whiskies|Gin|Vodka|Liqueurs|Ethyl alcohol", case=False)]

    # Sort descending by value
    spirit_df = spirit_df.sort_values(by="EU Export (£)", ascending=False)

    colors = ["#b5651d", "#f4d03f", "#d98880", "#5dade2", "#bb8fce", "#85c1e9"]

    fig = go.Figure()
    total = spirit_df["EU Export (£)"].sum()
    cumulative = 0

    for i, row in enumerate(spirit_df.itertuples()):
        fig.add_trace(go.Bar(
            y=["Total Export"],
            x=[row._4],
            name=row.Product,
            orientation="h",
            marker_color=colors[i % len(colors)],
            base=cumulative,
            hovertemplate=f"<b>{row.Product}</b><br>Export: £{{x:,.0f}}<br>Share: {row._4 / total:.1%}<extra></extra>"
        ))
        cumulative += row._4

    fig.update_layout(
        title="🥃 EU Spirit Exports (2021–2025): 'Spirit in a Glass' Visualisation",
        barmode="stack",
        xaxis=dict(title="Export Value (£)", tickformat=","),
        yaxis=dict(showticklabels=False),
        height=300,
        margin=dict(l=30, r=30, t=60, b=40),
        showlegend=True
    )

    return fig

# Initialize app
app = Dash(__name__)
server = app.server  # Needed for file download

# Gantt Chart Generator
def create_figure(dataframe):
    fig = px.timeline(
        dataframe,
        x_start="Start", x_end="Finish",
        y="Task", color="Phase", text="Progress",
        title="Dissertation Gantt Chart"
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
    return fig
# 🔁 Generate clickable file links
def get_file_links():
    links = []
    for filename in sorted(os.listdir(DOCS_FOLDER)):
        path = f"/docs/{filename}"
        links.append(html.Div([
            html.A(f"📄 {filename}", href=path, target="_blank", style={'fontFamily': 'Georgia'})
        ]))
    return links

# ✅ App layout starts AFTER the function is defined
app.layout = html.Div([
    html.H1("🧾 Dissertation Gantt Tracker", style={'fontFamily': 'Georgia'}),

    # 📊 Gantt chart
    dcc.Graph(id="gantt", figure=create_figure(df)),

    # 🍸 Spirit Chart (Insert Here)
    html.H2("🥃 EU Spirit Exports: 'Spirit in a Glass' Chart", style={'fontFamily': 'Georgia'}),
    html.Div([
        html.Div(
            dcc.Graph(figure=create_spirit_glass_chart_from_csv()),
            style={'width': '65%', 'display': 'inline-block', 'verticalAlign': 'top'}
        ),
        html.Div(
            dash_table.DataTable(
                id='eu-exports-table',
                columns=[
                    {"name": col, "id": col} for col in pd.read_csv("eu_exports.csv").columns
                ],
                data=pd.read_csv("eu_exports.csv").to_dict('records'),
                style_table={'overflowX': 'auto'},
                style_cell={'fontFamily': 'Georgia', 'textAlign': 'left'},
                style_header={'fontWeight': 'bold'},
                page_size=10
            ),
            style={'width': '33%', 'display': 'inline-block', 'paddingLeft': '15px'}
        )
    ]),


    # 📝 Data Table for editing
    html.H2("📋 Edit Progress and Notes", style={'fontFamily': 'Georgia'}),
    dash_table.DataTable(
        id='datatable',
        columns=[{"name": i, "id": i, "editable": True} for i in df.columns],
        data=df.to_dict('records'),
        editable=True,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'fontFamily': 'Georgia'},
    ),
    html.Button("Update Chart", id='update', n_clicks=0),
    html.Div(id='update-msg', style={'marginTop': '10px', 'fontStyle': 'italic'}),

    # 📁 File upload/view
    html.H2("📁 Upload or View Files", style={'fontFamily': 'Georgia', 'marginTop': '40px'}),
    
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            '📤 Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '60%',
            'height': '80px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=True
    ),
    html.Div(children=get_file_links(), id='file-list', style={'marginTop': '10px'})
])


# 📊 Update Chart + Save Edits
@app.callback(
    Output("gantt", "figure"),
    Output("update-msg", "children"),
    Input("update", "n_clicks"),
    State("datatable", "data")
)
def update_chart(n_clicks, data):
    if not data:
        return create_figure(df), "⚠️ No data to update."
    updated_df = pd.DataFrame(data)
    updated_df['Start'] = pd.to_datetime(updated_df['Start'])
    updated_df['Finish'] = pd.to_datetime(updated_df['Finish'])
    updated_df.to_csv("gantt_data.csv", index=False)
    return create_figure(updated_df), "✅ Chart updated and saved."

# 📁 Save uploaded files
import base64

@app.callback(
    Output('file-list', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def save_file(contents, filenames):
    if contents and filenames:
        for content, name in zip(contents, filenames):
            try:
                header, encoded = content.split(',', 1)
                data = base64.b64decode(encoded)
                with open(os.path.join(DOCS_FOLDER, name), "wb") as f:
                    f.write(data)
            except Exception as e:
                print(f"Error saving file {name}: {e}")
    return get_file_links()

# 📄 Generate clickable links for all docs
DOCS_FOLDER = "docs"
os.makedirs(DOCS_FOLDER, exist_ok=True)

def get_file_links():
    try:
        files = sorted(os.listdir(DOCS_FOLDER))
        links = []
        for filename in files:
            if filename.startswith("."):  # skip hidden files
                continue
            path = f"/docs/{filename}"
            links.append(html.Div([
                html.A(f"📄 {filename}", href=path, target="_blank", style={'fontFamily': 'Georgia'})
            ]))
        return links or [html.Div("📂 No documents uploaded yet.")]
    except Exception as e:
        return [html.Div(f"⚠️ Error loading files: {e}")]

# 🧭 Route to serve uploaded files
@server.route("/docs/<path:filename>")
def serve_file(filename):
    return send_from_directory(DOCS_FOLDER, filename, as_attachment=False)

# 🚀 Launch
if __name__ == '__main__':
    app.run_server(host="0.0.0.0", port=10000, debug=False)
#   app.run_server(jupyter_mode='external', debug=True, port=7400)


# In[ ]:




