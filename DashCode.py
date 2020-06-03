import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import dash_table
from collections import defaultdict

import plotly.express as px
import plotly.graph_objects as go
import pyTigerGraph as tg
import pandas as pd
import flat_table

# Create connection to TG Cloud
graph = tg.TigerGraphConnection(
            host="https://61af4f31021c449e85f690cbec28ef7a.i.tgcloud.io",
            graphname="MyGraph",
            apiToken="r72kccg1jaso02s8gn20fskgfnh7brim"
        )
# Query to grab all authors, publication doi, number of publications
parsAuth = graph.runInstalledQuery("AuthorSearchDash", {}, timeout=20000, sizeLimit=40000000)

# Query to grab publication doi, title, URL
parsPubs = graph.runInstalledQuery("GrabPubs", {}, timeout=20000, sizeLimit=40000000)

# Sort Publication data
df_pub = pd.DataFrame(parsPubs[0])
df1_pub = flat_table.normalize(df_pub)
df2_pub = df1_pub.rename(columns={'Pubs.attributes.Pubs.id': 'Doi',
                                  'Pubs.attributes.Pubs.pub_title': 'Title',
                                  'Pubs.attributes.Pubs.pub_url': 'URL'})
df3_pub = df2_pub[['Doi', 'Title', 'URL']]

# Sort Author data
df_auth = pd.DataFrame(parsAuth[0])
df1_auth = flat_table.normalize(df_auth)
df2_auth = df1_auth.rename(columns={'Author.attributes.@pubNum': 'pubCount',
                                    'Author.attributes.author_name': 'Name',
                                    'Author.attributes.@pubList': 'Publications'})
df3_auth = df2_auth[['index', 'Name', 'pubCount', 'Publications']]

# Create lists to easily access data
temp_list = set()             # Set of author names
map_list = defaultdict(list)  # Map of author names to their publications
num_list = {}                 # Map of author names to number of publications

# Loop over data to add to lists
for index, row in df3_auth.iterrows():
    temp_list.add(row['Name'])
    map_list[row['Name']].append(row['Publications'])
    num_list[row['Name']] = row['pubCount']

# Style sheet used for our Dash layout
external_stylesheets = [dbc.themes.BOOTSTRAP]

# Create the application
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Colors for our bar chart
colorscale = {
    0: 'rgb(75, 41, 145)',
    1: 'rgb(135, 44, 162)',
    2: 'rgb(192, 54, 157)',
    3: 'rgb(234, 79, 136)',
    4: 'rgb(250, 120, 118)',
    5: 'rgb(246, 169, 122)',
    6: 'rgb(237, 217, 163)'
}

# Counter to prevent duplicate legends in bar chart
numscale = {
    0: 0,
    1: 0,
    2: 0,
    3: 0,
    4: 0,
    5: 0,
    6: 0
}

# Create our blank bar chart
fig = px.bar()
fig.update_layout(
    title_text='Number of Publications by Author',
    title_font_size=25,
    title_font_color='black',
    title_xanchor='left',

    plot_bgcolor='white',
    paper_bgcolor='white',

    xaxis_title_text='Authors',
    xaxis_color='black',
    xaxis_title_font_size=15,
    xaxis_anchor='free',
    xaxis_ticks='',
    xaxis_type='category',
    xaxis_linecolor='black',
    xaxis_showline=True,

    yaxis_title_text="Number of Publications",
    yaxis_rangemode="nonnegative",
    yaxis_color='black',
    yaxis_linecolor='black',
    yaxis_gridcolor='black',
    yaxis_dtick=1,
    yaxis_showline=True,

    showlegend=True,
    legend_bordercolor='black',
    legend_borderwidth=1,
    autosize=True,

    margin_l=80,
    margin_r=20,
    margin_t=50,
    margin_b=50,

)
# Generate header & parent div for layout
app.layout = html.Div(style={'backgroundColor': 'white', 'fontFamily': 'Georgia, serif', 'height': '100vh'}, children=[
    html.H1(
        children='Publication Analyzer',
        style={
            'textAlign': 'center',
            'color': 'blue'
        }

    ),
    # Subtitle div
    html.Div(
        children='Searching Biomedical Articles Related to Covid-19',
        style={
            'textAlign': 'center',
            'color': 'blue'

        }
    ),
    # Title div for our author search
    html.Div(
        children='Author Search',
        style={
            'textAlign': 'left',
            'color': 'blue'

        }
    ),
    # Create a row to place items side-by-side
    dbc.Row(
        [
            # Column with dropdown menu, table printout
            dbc.Col(
                    # Dropdown div
                    html.Div(
                        style={'color': 'black', 'backgroundColor': 'white', 'display': 'grid'}, children=[
                            html.Div(
                                dcc.Dropdown(
                                    id='auth_list',
                                    options=[{'label': i, 'value': i} for i in sorted(temp_list)],
                                    placeholder="Choose an Author",
                                    style={'color': 'black', 'backgroundColor': 'white', 'width': '100%'}
                                )
                            ),
                            # Div to print out number of publications
                            html.H4(
                                id='num-pub-container',
                                children='Author Publications',
                                style={
                                    'textAlign': 'left',
                                    'color': 'blue',
                                    'backgroundColor': 'white'
                                }
                            ),
                            # Div to print out table of Articles
                            html.Div(
                                id='pub-output-container',
                                style={'color': 'black', 'backgroundColor': 'white', 'width': '99%'},
                            )
                        ],
                    ),
                    width=6,
            ),
            # Column with bar chart
            dbc.Col(
                # Div for bar chart
                html.Div([
                    dcc.Graph(
                        id='author_num_graph',
                        figure=fig
                    ),
                ],
                    style={'height': '100%', 'width': '90%'}
                ),
                width=6,
                align='center'
            )
        ],
    ),

])


# Output table to corresponding container
@app.callback(
    Output('pub-output-container', 'children'),
    [Input('auth_list', 'value')]
)
# Sort data
def update_output(value):
    df = pd.DataFrame(columns=["Doi", "Title", "URL"])
    for x in map_list[value]:
        df = pd.concat([df, df3_pub.loc[df3_pub["Doi"] == x]])

    # Create table
    tbl = dash_table.DataTable(
        id='pub_data',
        style_data={
            'whitespace': 'normal',
            'height': 'auto',

        },
        style_table={
            'height': '375px',
            'overflowY': 'auto',
            'overflowX': 'hidden',
        },
        style_cell={
            'textAlign': 'center',
            'border': '2px solid black',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'maxWidth': 0
        },
        style_header={
            'font_size': '20px',
            'text-align': 'center',
        },
        css=[{'selector': '.row', 'rule': 'margin: 0'}],
        # Allow for table data to overflow and appear as ellipsis
        tooltip_data=[
            {
                column: {'value': str(value), 'type': 'markdown'}
                for column, value in row.items()
            } for row in df.to_dict('rows')
        ],
        tooltip_duration=1000,
        # Assign data and columns to table
        data=df.to_dict('records'),
        columns=[{'name': 'Doi', 'id': 'Doi'}, {'name': 'Title', 'id': 'Title'}, {'name': 'URL', 'id': 'URL'}],
    )
    return tbl


# Output number of publications
@app.callback(
    Output('num-pub-container', 'children'),
    [Input('auth_list', 'value')]
)
def update_num(value):
    return "Author Publications: {}".format(num_list[value])


# Update graph with data
@app.callback(
    Output('author_num_graph', 'figure'),
    [Input('auth_list', 'value')]
)
def update_graph(value):
    # Create legendgroup, assign color and check if legend already exists
    luf = ''
    puf = ''
    bool = True
    x = 0
    if num_list[value] > 6:
        luf = 'legendgroup6'
        puf = '>6'
        numscale[6] += 1
        if numscale[6] > 1:
            bool = False
        x = 6
    else:
        luf = 'legendgroup{}'.format(num_list[value] - 1)
        puf = '{}'.format(num_list[value])
        numscale[num_list[value] - 1] += 1
        if numscale[num_list[value]-1] > 1:
            bool = False
        x = num_list[value] - 1

    # Add data as new trace to bar chart
    fig.add_trace(go.Bar(
        x=[value],
        y=[num_list[value]],
        marker_color=colorscale[x],
        showlegend=bool,
        legendgroup=luf,
        name=puf,
    ))
    return fig


# Run app
if __name__ == '__main__':
    app.run_server(debug=True)

__author__ = 'Akash Kaul'
__copyright__ = 'N/A'
__license__ = 'N/A'
__email__ = 'akash.kaul@wustl.edu'
