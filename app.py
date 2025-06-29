#!/usr/bin/env python
# coding: utf-8

"""
Dissertation Gantt Tracker Dashboard

This Dash app visualizes and manages the progress of a dissertation project
as an editable Gantt chart. It allows for task tracking, progress updates,
and supervisor comments. Edits made in the table are persisted to CSV.

Author: Pritid Nandy
Date: June 2025
"""

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, dash_table
from flask import send_from_directory
import datetime
import base64

# Constants
DOCS_FOLDER = "docs"
if not os.path.exists(DOCS_FOLDER):
    os.makedirs(DOCS_FOLDER)

# Create sample data if files don't exist
def create_sample_data():
    if not os.path.exists("gantt_data.csv"):
        sample_gantt = pd.DataFrame({
            'Task': [
                'Literature Review & Finalizing Proposal',
                'Data Collection & Preparation', 
                'Model Development & Testing',
                'Analysis & Scenario Modelling',
                'Drafting Report & Visuals',
                'Supervisor Review Period',
                'Incorporate Feedback & Final Polish',
                'Final Submission'
            ],
            'Phase': ['Planning', 'Preparation', 'Development', 'Analysis', 'Reporting', 'Review', 'Revision', 'Submission'],
            'Start': [
                '2025-06-17', '2025-06-17', '2025-07-01', '2025-07-29', 
                '2025-07-29', '2025-08-12', '2025-08-26', '2025-09-03'
            ],
            'Finish': [
                '2025-06-30', '2025-07-28', '2025-08-11', '2025-08-11',
                '2025-08-11', '2025-08-25', '2025-09-02', '2025-09-03'
            ],
            'Progress': ['100%', '50%', '20%', '0%', '0%', '0%', '0%', '0%'],
            'Notes': [
                'Completed - proposal finalized',
                'Ongoing - data gathering in progress', 
                'Starting model framework',
                'Planned - forecasting scenarios',
                'Planned - first draft completion',
                '2 weeks for supervisor feedback - CRITICAL',
                'Address supervisor comments',
                'DEADLINE - Submit by end of day'
            ]
        })
        sample_gantt.to_csv("gantt_data.csv", index=False)
    
    if not os.path.exists("eu_exports.csv"):
        sample_exports = pd.DataFrame({
            'Product': ['Whiskies', 'Gin', 'Vodka', 'Liqueurs', 'Ethyl alcohol'],
            'EU Export (£)': ['£1,250,000', '£890,000', '£650,000', '£420,000', '£320,000'],
            'Year': [2024, 2024, 2024, 2024, 2024]
        })
        sample_exports.to_csv("eu_exports.csv", index=False)

# Initialize sample data
create_sample_data()

# Load data
try:
    df = pd.read_csv("gantt_data.csv")
    df['Start'] = pd.to_datetime(df['Start'])
    df['Finish'] = pd.to_datetime(df['Finish'])
except Exception as e:
    print(f"Error loading gantt_data.csv: {e}")
    # Create minimal fallback data
    df = pd.DataFrame({
        'Task': ['Sample Task'],
        'Phase': ['Research'],
        'Start': [pd.Timestamp('2025-01-01')],
        'Finish': [pd.Timestamp('2025-01-31')],
        'Progress': ['50%'],
        'Notes': ['Sample note']
    })

def create_spirit_glass_chart_from_csv(filepath="eu_exports.csv"):
    """Create spirit exports visualization"""
    try:
        df_exports = pd.read_csv(filepath)
        
        # Clean export values: remove £ and commas, convert to float
        df_exports["EU Export (£)"] = df_exports["EU Export (£)"].replace('[£,]', '', regex=True).astype(float)
        
        # Keep only spirit categories (excluding sugary waters, cider, etc.)
        spirit_df = df_exports[df_exports["Product"].str.contains("Whiskies|Gin|Vodka|Liqueurs|Ethyl alcohol", case=False)]
        
        # Sort descending by value
        spirit_df = spirit_df.sort_values(by="EU Export (£)", ascending=False)
        
        colors = ["#b5651d", "#f4d03f", "#d98880", "#5dade2", "#bb8fce", "#85c1e9"]
        
        fig = go.Figure()
        total = spirit_df["EU Export (£)"].sum()
        cumulative = 0
        
        for i, row in enumerate(spirit_df.itertuples()):
            export_value = getattr(row, 'EU Export (£)', 0)
            fig.add_trace(go.Bar(
                y=["Total Export"],
                x=[export_value],
                name=row.Product,
                orientation="h",
                marker_color=colors[i % len(colors)],
                base=cumulative,
                hovertemplate=f"<b>{row.Product}</b><br>Export: £{{x:,.0f}}<br>Share: {export_value / total:.1%}<extra></extra>"
            ))
            cumulative += export_value
        
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
    except Exception as e:
        print(f"Error creating spirit chart: {e}")
        # Return empty figure if there's an error
        fig = go.Figure()
        fig.update_layout(title="⚠️ Unable to load spirit exports data")
        return fig

# Initialize app
app = Dash(__name__)
server = app.server  # Needed for deployment and file download

# Gantt Chart Generator
def create_figure(dataframe):
    """Create Gantt chart from dataframe"""
    try:
        fig = px.timeline(
            dataframe,
            x_start="Start", x_end="Finish",
            y="Task", color="Phase", text="Progress",
            title="Dissertation Gantt Chart"
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
        return fig
    except Exception as e:
        print(f"Error creating Gantt chart: {e}")
        fig = go.Figure()
        fig.update_layout(title="⚠️ Unable to create Gantt chart")
        return fig

def get_file_links():
    """Generate clickable file links"""
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

# App layout
app.layout = html.Div([
    html.H1("🧾 Dissertation Gantt Tracker", style={'fontFamily': 'Georgia'}),

    # 📊 Gantt chart
    dcc.Graph(id="gantt", figure=create_figure(df)),

    # 🍸 Spirit Chart
    html.H2("🥃 EU Spirit Exports: 'Spirit in a Glass' Chart", style={'fontFamily': 'Georgia'}),
    html.Div([
        html.Div(
            dcc.Graph(figure=create_spirit_glass_chart_from_csv()),
            style={'width': '65%', 'display': 'inline-block', 'verticalAlign': 'top'}
        ),
        html.Div([
            dash_table.DataTable(
                id='eu-exports-table',
                columns=[
                    {"name": col, "id": col} for col in pd.read_csv("eu_exports.csv").columns
                ] if os.path.exists("eu_exports.csv") else [],
                data=pd.read_csv("eu_exports.csv").to_dict('records') if os.path.exists("eu_exports.csv") else [],
                style_table={'overflowX': 'auto'},
                style_cell={'fontFamily': 'Georgia', 'textAlign': 'left'},
                style_header={'fontWeight': 'bold'},
                page_size=10
            )
        ], style={'width': '33%', 'display': 'inline-block', 'paddingLeft': '15px'})
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
    html.Button("Update Chart", id='update', n_clicks=0, style={'margin': '10px'}),
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
    """Update chart and save data"""
    if not data or n_clicks == 0:
        return create_figure(df), ""
    
    try:
        updated_df = pd.DataFrame(data)
        updated_df['Start'] = pd.to_datetime(updated_df['Start'])
        updated_df['Finish'] = pd.to_datetime(updated_df['Finish'])
        updated_df.to_csv("gantt_data.csv", index=False)
        return create_figure(updated_df), "✅ Chart updated and saved."
    except Exception as e:
        return create_figure(df), f"⚠️ Error updating chart: {str(e)}"

# 📁 Save uploaded files
@app.callback(
    Output('file-list', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def save_file(contents, filenames):
    """Save uploaded files"""
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

# 🧭 Route to serve uploaded files
@server.route("/docs/<path:filename>")
def serve_file(filename):
    """Serve uploaded files"""
    try:
        return send_from_directory(DOCS_FOLDER, filename, as_attachment=False)
    except Exception as e:
        return f"Error serving file: {e}", 404

# 🚀 Launch
if __name__ == '__main__':
    # Get port from environment variable (required for cloud deployment)
    port = int(os.environ.get('PORT', 10000))
    app.run_server(host="0.0.0.0", port=port, debug=False)
