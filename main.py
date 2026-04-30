# Import useful libraries

import numpy as np
import pandas as pd
from dash import Dash, html, dcc, callback, Output, Input, State, exceptions
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import module as mod # The plan is to put here the functions which do most of the work

# The following imports are necessary for long callbacks
from dash.long_callback import DiskcacheLongCallbackManager

import diskcache
cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)

# Create necessary folders

if not os.path.exists('Speckles'):
    os.mkdir('Speckles')

if not os.path.exists('Patterns'):
    os.mkdir('Patterns')

# Create the app
app = Dash(__name__)

# Layout of the interface; I define the layout as a function, as this allows the layout to be updated upon refreshing the page.
def serve_layout():
    return html.Div([
        # Title
        html.H1(children = 'Simulation and data analysis for an optics experiment about spatial coherence'),
        
        dcc.Tabs(id = 'select-tab', 
            value = 'intro',
            children = [
                dcc.Tab(label = 'Introduction', value = 'intro'),
                dcc.Tab(label = 'Generate speckle fields', value = 'simu-1'),
                dcc.Tab(label = 'Filter and generate interference pattern', value = 'simu-2'),
                dcc.Tab(label = 'Data analysis', value = 'data-an')
            ]
        ),
        
        # First tab
        html.Div(children = [
            html.H2(children = 'Introduction'),
            html.Div([ 
                html.Div([
                    html.Img(src = 'assets/part_12.png', width = '700px')
                ],
                className = 'box_blue'),
                # Text introduction
                html.Div([
                    dcc.Markdown("""
                        > The simulation is divided in two parts: 
                                 
                        > First, the code generates a certain number of 1D speckle fields, and each field is 
                        then spatially filtered to produce a partially coherent field. The number of fields and the type of filtering may be selected 
                        in the boxes below.   
                                 
                        > In the second part, the code simulates the production of Young interference fringes by passage of the (filtered) field through 
                        a double slit. It is expected that the visibility of the average pattern (i.e., the correlation length of the filtered field) should 
                        be related to the amount of spatial filtering. 
                    """)
                    # Since in the physical experiment the speckle field is produced by a rough glass surface which might have a non-negligible correlation length, it's also possible to generate fields which take that into account.
                ],
                className = 'box_blue'),
            ],
            className = 'container_blue'
            ),
        ],
        style = {'dispay': 'none'}, # The style is updated by the callback when the tab is selected or deselected
        id = 'first-tab'
        ),

        # Second tab
        html.Div(children = [
            html.H2(children = 'First part: generation of the speckle fields'),
    
            html.Div(children = [
                html.Div(children = [
                    html.Img(src = 'assets/part_1.png', width = '700px')
                ],
                className = 'box'
                ),
                html.Div(children = [
                    html.H3(children = 'START SIMULATION'),
                    html.Div([
                        # These buttons let the user start or stop the simulation
                        html.Button(id='part-one-button', children='Start'), 
                        html.Button(id='cancel-one', children = 'Cancel'),
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        # This is just a counter of the number of times the simulation has been ran
                        html.P(id='counter', children = 'Simulation number 1'),
                        # Progress bar
                        html.Progress(id='progress-bar-one')
                    ],
                    className = 'start'
                    ),
                    html.H3(children = 'PLOT A SAMPLE FIELD'),
                    html.Label(
                        # All the patterns generated are stored in a folder. The dropdown menu below shows the content of that folder, 
                        # letting the user choose a pattern to analyze individually if necessary
                        dcc.Markdown('Choose sample field to plot')
                    ),
                    dcc.Dropdown(os.listdir('Speckles')[:10], id = 'select-field-plot'),
                    html.Div([
                        html.Button(id='plot-field', children='Plot')
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        html.P(id='counter-field-plot', children = 'Plot number 1')
                    ],
                    className = 'start'
                    ),
                ],
                className = 'box'
                ),
            ],
            className = 'container'
            ),

            html.Div(children = [
                dcc.Graph(id = 'sample-speckle', style={'width': '1400px', 'height': '800px'}, mathjax = True),
            ],
            className = 'graph'
            ),

            html.Div(children = [ 
                # Input parameters for the first part of the simulation
                html.Div(children = [
                    html.H3(children = 'Geometry of the set-up and wavelength'),
                    html.Br(),
                    html.Div(
                        # Input the size of the "source", the source being essentially the portion of the rough glass surface on which the laser shines
                        dcc.Markdown(r'> We suppose that the beam is initially collimated, with a diameter of $0.5 \, \mathrm{cm}$', mathjax = True) 
                    ),
                    # For now I consider only one transversal and one longitudinal dimension

                    html.Br(),
                    html.Label(
                        # Input the distance over which the field propagates (forming a speckle field in the process) before the filtering
                        dcc.Markdown(r'> The speckle field is formed $15 \, \mathrm{cm}$ away from the rough glass surface', mathjax = True)
                    ),

                    html.Br(),
                    html.Label(
                        # Input laser wavelength
                        dcc.Markdown(r'> The wavelength is chosen to be $500 \, \mathrm{nm}$', mathjax = True)
                    ),
                    html.Br(),
                    # Show chosen value on screeen
                ],
                className = 'left'
                ),

                html.Div(children = [
                    html.H3(children = 'Number of fields produced, number of "scatterers" and correlation length of the rough glass surface'),
                    html.Br(),
                    html.Label(
                        # Input the number of speckle fields to produce 
                        dcc.Markdown(r"""
                                     $200$ speckle fields are generated by default for statistics. 
                                     If the correlation length of the source (i.e. the rough glass surface) is not zero, 
                                     more statistics could be necessary ($\sim 1000$)
                                     """, mathjax = True)
                    ),
                    dcc.Slider(
                        200,
                        2000,
                        step = 100,
                        value = 200,
                        marks = {str(x): str(x) for x in np.arange(200, 2000, 200)},
                        id='field-number'
                    ),
                    html.Br(),
                    html.Div([
                        dcc.Markdown(id = 'field-number-out',  mathjax = True)
                    ]),
                    html.Br(),
                    html.Label(
                        # Input the number of "scatterers" which produce the field. Essentialy, this number is the number of points of the source.
                        # I found it not practical to randomize the points for the interference part too, but it is possible to do it at least for the 
                        # first part, and this should minimize spurious effects due to the source form and sharp edges. 
                        dcc.Markdown(r'The speckle field is generated with a monte carlo randomization, with $1000$ points on the source', mathjax = True)
                    ),
                    
                ],
                className = 'right'
                ),
            ],
            className = 'container'
            ),
        ],
        style = {'display': 'none'},
        id = 'second-tab'
        ),

        # Third tab
        html.Div(children = [
            html.H2(children = 'Second part: propagation, spatial filtering and interference'), # Second part of the simulation
            html.Div(children = [
                html.Div(children = [
                    html.Img(src = 'assets/part_2.png', width = '700px')
                ],
                className = 'box_green'
                ),
                html.Div(children = [
                    html.H3(children = 'START SIMULATION'),
                    html.Div([
                        # These buttons let the user start or stop the simulation
                        html.Button(id='part-two-button', children='Start'), 
                        html.Button(id='cancel-two', children = 'Cancel'),
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        # Just a counter
                        html.P(id='counter-two', children = 'Simulation number 1'),
                        # Progress bar
                        html.Progress(id='progress-bar-two')
                    ],
                    className = 'start'
                    ),
                ],
                className = 'box_green'
                ),
            ],
            className = 'container_green'
            ),
            html.Div(children = [
                html.Div(children = [
                    html.H3(children = 'Spatial filtering parameters'),
                    html.Br(),
                    html.Label(
                        # Input the type of filtering, which should give different statistics of the filtered field (i.e., sinc or gaussian correlation function)
                        dcc.Markdown('Type of filtering')
                    ),
                    dcc.RadioItems(
                        ['Rectangular', 'Gaussian'],
                        'Rectangular',
                        id='filtering-type',
                        inline=True
                    ),
                    html.Br(),
                    html.Label(
                        # Input how much the spatial spectrum should be filtered
                        dcc.Markdown(r'Width of filtering slit ($\mathrm{mm}$)', mathjax = True)
                    ),
                    
                    dcc.RangeSlider( 
                        0.01,
                        0.1,
                        step = 0.005,
                        value = [0.01, 0.05],
                        marks = {str(x): str(x) for x in np.arange(0.01, 0.02, 0.1)},
                        id='filter-width'
                    ),
                    html.Br(),
                    # Show the chosen value on screen
                    html.Div([
                        dcc.Markdown(id = 'filter-width-out', mathjax = True)
                    ]),
                ],
                className = 'left_green'
                ),

                html.Div(children = [
                    html.H3('Set-up parameters'),
                    html.Br(),
                    html.Label(
                        # Input the distance from the interference slits and the screen on which the pattern appears. 
                        dcc.Markdown(r'The interference patterns are calculated in a far field approximation', mathjax = True)
                    ),
                    html.Br(),
                    html.Label(
                        # Input slits spacing
                        dcc.Markdown(r'Distance between slits range ($\mathrm{mm}$)', mathjax = True)
                    ),
                    dcc.RangeSlider( 
                        0.1,
                        10,
                        step = 0.05,
                        value = [0.5, 10],
                        marks = {str(x): str(x) for x in np.arange(5, 20, 5)},
                        id='slits-dist'
                    ),
                    html.Br(),
                    # Show chosen value on screen
                    html.Div([
                        dcc.Markdown(id = 'slits-dist-out', mathjax = True)
                    ]),
                    html.Br(),
                    # Input slit width 
                    html.Label(
                        dcc.Markdown(r'The slits are 200 $\mu\mathrm{m}$ wide', mathjax = True)
                    ),
                ],
                className = 'right_green'
                ),
            ],
            className = 'container_green'
            ),

            html.Div(children = [
                # Show the pattern which results form the simulation, averaged over all the speckle fields
                dcc.Graph(id = 'pattern', style={'width': '1400px', 'height': '800px'}),
            ],
            className = 'graph'
            ),
        ],
        style = {'display': 'none'},
        id = 'third-tab'
        ),

        # Fourth tab
        html.Div(children = [
            html.H2(children = 'Data Analysis'), # Third part: data analysis

            html.Div([
                html.Div([
                dcc.Markdown("""
                    > Once generated a bunch of patterns with different filterings with the functions above, refresh the page *only once* before starting the analysis.
                             
                    > The analysis consists of the calculation of the visibility of the interference patterns, which corresponds to the absolute value of the *field* 
                    correlation function of the speckle field (absolute value of the *complex degree of coherence*). In addition, the center of the pattern could be a 
                    local maximum, in which case the phase of the correlation function is +1, or a local minimum, in which case the phase is -1.
                             
                    > Each pattern can be analyzed individually in more detail, e.g. choosing manually the initial parameters for the fit, or they can all be analyzed 
                    automatically (with possibly a lesser accuracy). After the analysis of all patterns, it is possible to make improvement to suspicious points in the final 
                    graph by going back to the individual analysis.
                """)
                ],
                className = 'inner_pink')
            ],
            className = 'container_pink'),

            html.Div(children = [
                html.Div(children = [
                    html.Label(
                        # All the patterns generated are stored in a folder. The dropdown menu below shows the content of that folder, 
                        # letting the user choose a pattern to analyze individually if necessary
                        dcc.Markdown('> Choose pattern to view')
                    ),
                    dcc.Dropdown(os.listdir('Patterns'), id = 'select-pattern'),
                    html.H3(children = 'PLOT'),
                    html.Div([
                        html.Button(id='plot-button', children='Plot')
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        html.P(id='counter-plot', children = 'Plot number 1')
                    ],
                    className = 'start'
                    ),
                    html.H3(children = 'PRELIMINARY ANALYSIS'),
                    html.Div(children = [
                        html.Div([
                            html.Label(
                                dcc.Markdown('Guess fit parameter (visibility)')
                            ),
                            html.Br(),
                            dcc.Slider(
                                0.01, 
                                1,
                                step = 0.01,
                                value = 0.5, 
                                marks = {str(x/10): str(x/10) for x in np.arange(0, 10, 2)},
                                id = 'fit-guess'
                            )
                        ],
                        className = 'smol_l_pink'
                        ),
                        html.Div([
                            html.Label(
                                dcc.Markdown('(Amplitude correction)')
                            ),
                            html.Br(),
                            dcc.Slider(
                                0.1, 
                                1.5,
                                step = 0.01,
                                value = 1, 
                                marks = {str(x/10): str(x/10) for x in np.arange(5, 15, 5)},
                                id = 'fit-guess-2'
                            )
                        ],
                        className = 'smol_l_pink'
                        ),
                        html.Div([
                            html.Label(
                                dcc.Markdown('(Horizontal dilation)')
                            ),
                            html.Br(),
                            dcc.Slider(
                                0.5, 
                                1.5,
                                step = 0.01,
                                value = 1, 
                                marks = {str(x/10): str(x/10) for x in np.arange(5, 15, 5)},
                                id = 'fit-guess-3'
                            )
                        ],
                        className = 'smol_l_pink'
                        ),
                        html.Div([
                            html.Label(
                                dcc.Markdown('Options for preliminary analysis')
                            ),
                            html.Br(),
                            dcc.Checklist( # CONSIDER REPLACING WITH RADIO ITEMS
                                ['Fit guess', 'Extremal points', 'Rough fit', 'Convex hull'],
                                [],
                                id = 'pre-options',
                                inline = True
                            )
                        ],
                        className = 'smol_r_pink'
                        ),
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        html.Button(id='preprocess-button', children='Run')
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        html.P(id='counter-preprocessing', children = 'Run number 1')
                    ],
                    className = 'start'
                    ),
                    html.H3(children = 'PROCESSING'),
                    html.Div([
                        html.Button(id='process-button', children='Process')
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        html.P(id='counter-processing', children = 'Processing number 1')
                    ],
                    className = 'start'
                    ),
                ],
                className = 'box_pink'
                ),
                html.Div(children = [
                    html.H3(children = 'ANALYZE ALL PATTERNS'),
                    html.Div([
                        # This buttons let the user start or stop the analysis 
                        html.Button(id='part-three-button', children='Start analysis'), 
                        html.Button(id='cancel-three', children = 'Cancel'),
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        dcc.RadioItems(
                        ['Rough fit', 'Convex hull'],
                        'Convex hull',
                        id='norm-method',
                        inline=True
                    ),
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        # Counter and progress bar
                        html.P(id='counter-three', children = 'Analysis number 1'),
                        html.Progress(id='progress-bar-three')
                    ],
                    className = 'start'
                    ),
                    html.Label(
                        # All the patterns generated are stored in a folder. The dropdown menu below shows the content of that folder, 
                        # letting the user choose a pattern to analyze individually if necessary
                        dcc.Markdown('> Choose filtering width (click "choose" and then select)')
                    ),
                    html.Div([
                        html.Button(id='choose-filter', children = 'Choose')
                    ],
                    className = 'start'
                    ),
                    dcc.Dropdown(id = 'select-filter-width'),
                    html.H3(children = 'PLOT VISIBILITY'),
                    html.Div([
                        html.Button(id='plot-all-button', children = 'Plot')
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        html.P(id='counter-plot-all', children = 'Plot number 1')
                    ],
                    className = 'start'
                    ),
                    html.H3(children = 'PLOT CORRELATION LENGTH VS FILTER WIDTH'),
                    html.Div([
                        html.Button(id='plot-cvf-button', children = 'Plot')
                    ],
                    className = 'start'
                    ),
                    html.Div([
                        html.P(id='counter-plot-cvf', children = 'Plot number 1')
                    ],
                    className = 'start'
                    ),
                ],
                className = 'box_pink'
                ),
            ],
            className = 'container_pink'
            ),
            # I should maybe add ginput-like options to interact with the graph and extract data manually form it?

            html.Div(children = [
                dcc.Graph(id = 'pattern-analysis', style={'width': '700px', 'height': '400px'}, mathjax = True),
                dcc.Graph(id = 'patt-preprocess', style={'width': '700px', 'height': '400px'}, mathjax = True),
            ],
            style = {'width': '1400px', 'height': '400px', 'display': 'flex', 'background-color': '#000000', 'padding-top': '10px', 'padding-right': '10px', 'padding-bottom': '10px', 'padding-left': '10px', 'margin-bottom': '10px'}
            ),

            html.Div(children = [
                    dcc.Markdown(id = 'patt-param', mathjax = True)
            ]),

            html.Div(children = [
                dcc.Graph(id = 'patt-prof', style={'width': '700px', 'height': '400px'}, mathjax = True),
                dcc.Graph(id = 'patt-norm', style={'width': '700px', 'height': '400px'}, mathjax = True),
            ],
            style = {'width': '1400px', 'height': '400px', 'display': 'flex', 'background-color': '#000000', 'padding-top': '10px', 'padding-right': '10px', 'padding-bottom': '10px', 'padding-left': '10px', 'margin-top': '10px'}
            ),

            html.Div(children = [
                    dcc.Markdown(id = 'visibility', mathjax = True)
            ]),

            html.Div(children = [
                dcc.Graph(id = 'graph-all', style={'width': '700px', 'height': '400px'}, mathjax = True),
                dcc.Graph(id = 'graph-cvf', style={'width': '700px', 'height': '400px'}, mathjax = True),
            ],
            style = {'width': '1400px', 'height': '400px', 'display': 'flex', 'background-color': '#000000', 'padding-top': '10px', 'padding-right': '10px', 'padding-bottom': '10px', 'padding-left': '10px', 'margin-top': '10px'}
            ),

        ],
        style = {'display': 'none'},
        id = 'fourth-tab'
        )
    ],
    className = 'layout'
    )

app.layout = serve_layout

# Callbacks

@callback( # This is the callback for the tabs
    Output('first-tab', 'style'),
    Output('second-tab', 'style'),
    Output('third-tab', 'style'),
    Output('fourth-tab', 'style'),
    Input('select-tab', 'value')
)
def render(tab):
    on = {'display': 'block'}
    off = {'display': 'none'}

    if tab == 'intro':
        return on, off, off, off
    elif tab == 'simu-1':
        return off, on, off, off
    elif tab == 'simu-2':
        return off, off, on, off
    elif tab == 'data-an':
        return off, off, off, on

@callback( # This serves to return the values selected in the sliders
    Output('field-number-out', 'children'),
    # Output('correlation-length-out', 'children'),
    Output('filter-width-out', 'children'),
    Output('slits-dist-out', 'children'),
    Input('field-number', 'value'),
    # Input('correlation-length', 'value'),
    Input('filter-width', 'value'),
    Input('slits-dist', 'value'),
)
def update_values(a, c, d): 
    return ['Generating {} fields'.format(a)], ['Filter width between {} and {}'.format(c[0], c[1]) + r'$\, \mathrm{mm}$'], ['Slit separation between {} and {}'.format(d[0], d[1]) + r'$\, \mathrm{mm}$']

@app.long_callback( 
    # This is the callback for the first simulation. Long callback since for regular callbacks there's a max time of 30 s.
    # Also, long callback allows to manage the layout during the function call
    output = [
        Output('counter', 'children') # Only output is the counter
    ],
    inputs = [
        Input('part-one-button', 'n_clicks'), # The only input is the click of the 'start' button
        # The other parameters are passed as states, so changing them does not trigger the start of the simulation,
        State('field-number', 'value'),
        # State('correlation-length', 'value'),
    ],
    running=[ # When the simulation is running,
        (Output('part-one-button', 'disabled'), True, False), # The start button is disabled
        (Output('cancel-one', 'disabled'), False, True), # And it is possible to cancel the operation
        (
            Output('counter', 'style'), # Show or hid the counter (visible when not running, hidden when running)
            {'visibility': 'hidden'},
            {'visibility': 'visible'},
        ),
        (
            Output('progress-bar-one', 'style'), # Show or hid the progress bar (hidden when not running, visible when running)
            {'visibility': 'visible'},
            {'visibility': 'hidden'},
        ),
    ],
    cancel = [Input('cancel-one', 'n_clicks')], # Link to cancel button id
    progress = [Output('progress-bar-one', 'value'), Output('progress-bar-one', 'max')], # Link to progress bar id
    manager = long_callback_manager
)
def generate_fields(set_progress, n_clicks, field_num):
    if n_clicks is None:
        raise exceptions.PreventUpdate() # This is necessary in order for the simulation not to start automatically upon launching the app
    
    ### Choose fixed parameters here because I want to include the average intensity, which is computed here, so I do it all at once
    source_size = 0.5
    dist = 15 # [cm]
    scatt_num = 1000 
    wavelen = 500 # [nm]
    avg_intensity = 0
    screen_size = 30 # [cm]
    slit_width = 0.2 # [mm]
    dist_2 = 1e4 # [cm]
    dx = 0.005 # [cm]

    for i in range(field_num):
        field, screen = mod.generate_speckle_field(source_size, dist, scatt_num, wavelen) # Generate a field
        avg_intensity += np.mean(np.abs(field).real ** 2)
        field_data = pd.DataFrame({
            'screen': screen, 
            'spec_re': field.real, 
            'spec_im': field.imag
        }) # Create a data frame
        field_data.to_csv('Speckles/speckle_num_{}.csv'.format(i)) # Store in csv
        set_progress((str(i + 1), str(field_num))) # Update progress bar

    numbers = {'avg_intensity': avg_intensity, 
               'field_num': field_num, 
               'wavelen_nm': wavelen, 
               'screen_size_cm': screen_size, 
               'slit_width_mm': slit_width, 
               'dx_cm': dx, 
               'dist2_cm': dist_2}
    
    with open('numbers.json', 'w') as f:
        json.dump(numbers, f)

    return ['Simulation number {}'.format(n_clicks + 1)] # Return counter

@app.long_callback(
    # This is the callback for the second simulation. 
    output = [
        Output('counter-two', 'children'), # Counter
        Output('pattern', 'figure') # Graph
    ],
    inputs = [
        Input('part-two-button', 'n_clicks'), # As before, the only input is the click on the button and the other parameters are states.
        State('filtering-type', 'value'),
        State('filter-width', 'value'),
        State('slits-dist', 'value'),
    ],
    running=[ # This is identical to above
        (Output('part-two-button', 'disabled'), True, False),
        (Output('cancel-two', 'disabled'), False, True),
        (
            Output('counter-two', 'style'),
            {'visibility': 'hidden'},
            {'visibility': 'visible'},
        ),
        (
            Output('progress-bar-two', 'style'),
            {'visibility': 'visible'},
            {'visibility': 'hidden'},
        ),
    ],
    cancel = [Input('cancel-two', 'n_clicks')],
    progress = [Output('progress-bar-two', 'value'), Output('progress-bar-two', 'max')],
    manager = long_callback_manager
)
def filter_and_interfere(set_progress, n_clicks, filter_type, filter_width_ext, slits_dist_ext):
    if n_clicks is None:
        raise exceptions.PreventUpdate()
    
    with open('numbers.json', 'r') as f:
        numbers = json.load(f)

    slit_width = numbers['slit_width_mm']
    dist_2 = numbers['dist2_cm']
    wavelen = numbers['wavelen_nm']
    screen_size = numbers['screen_size_cm'] # [cm] 
    dx = numbers['dx_cm'] # [cm] (resolution)
    dim = int(screen_size/dx) + 1 # Dimension of the arrays

    filter_width_ext = [round(g * 2e5 * np.pi / wavelen, 2) for g in filter_width_ext] # convert in k units

    filter_width_step = round(0.01 * 2e5 * np.pi / wavelen, 2)
    slits_dist_step = 0.1
    vect = os.listdir('Speckles')
    
    num = (filter_width_ext[1] + filter_width_step - filter_width_ext[0]) * (slits_dist_ext[1] + slits_dist_step - slits_dist_ext[0]) / (filter_width_step * slits_dist_step)
    slits_dist_ext = [l/10 for l in slits_dist_ext]
    
    # Convert lengths to cm
    slit_width = slit_width / 10
    wavelen = wavelen / 1e7
    slits_dist_step = slits_dist_step / 10
    counter = 1

    totem = []

    for filter_width in np.arange(filter_width_ext[0], filter_width_ext[1] + filter_width_step, filter_width_step):
        for slits_dist in np.arange(slits_dist_ext[0], slits_dist_ext[1] + slits_dist_step, slits_dist_step):

            pattern = np.zeros(dim) # Array containing the interference pattern

            
            avg_intensity_fi = 0 # intensity of the filtered field
            for i in vect:
                field_data = pd.read_csv('Speckles/' + i) # Read the csv with the speckle field 
                field = field_data['spec_re'].to_numpy() + field_data['spec_im'].to_numpy() * 1j # Convert to ndarray
                screen = field_data['screen'].to_numpy() 
                filt_field = mod.filter(filter_type, field, filter_width, screen_size, dx) # Spatially filter the field
                avg_intensity_fi += np.mean(np.abs(filt_field).real ** 2)

                # Add the pattern generated by the speckle field to the average
                pattern += mod.create_pattern(filt_field, slits_dist, screen, dist_2, wavelen, slit_width)

            pattern_data = pd.DataFrame({
                'screen': screen,
                'pattern': pattern,
                'filter_type': [filter_type for i in range(len(screen))],
                'filter_width': [round(filter_width, 2) for i in range(len(screen))],
                'slits_dist': [slits_dist for i in range(len(screen))]
            }) # Convert to data frame

            # fig = px.line(pattern_data.melt(id_vars = 'screen', value_vars = ['profile', 'pattern']), x = 'screen', y = 'value', title = 'Averaged interference pattern', line_group = 'variable', color = 'variable') 
            fig = px.line(pattern_data, x = 'screen', y = 'pattern', title = 'Averaged interference pattern', labels  = {
                'screen': 'x [cm]',
                'pattern': 'Field intensity'
            }) # Create the figure of the graph
            pattern_data.to_csv('Patterns/Pattern_F={}_D={}.csv'.format(round(filter_width, 2), round(slits_dist, 2))) # Store the pattern to csv

            counter += 1
            set_progress((str(counter), str(num))) # Update progress bar

        totem.append([round(filter_width, 2), avg_intensity_fi / len(vect)])

    with open('intensity.json', 'w') as f:
        json.dump(totem, f)

    return ['Simulation number {}'.format(n_clicks + 1)], fig # Return the number of clicks and the last pattern computed

@callback(
    # This is the callback for the plot of an individual pattern in the data analysis part. A long callback isn't necessary here
    Output('pattern-analysis', 'figure'), # Output a counter, the graph and the parameters of the pattern
    Output('counter-plot', 'children'),
    Output('patt-param', 'children'),
    Input('plot-button', 'n_clicks'), # Input the button click, other parameters are states
    State('select-pattern', 'value')
)
def plot_pattern(n_clicks, patt_name):
    if n_clicks is None:
        raise exceptions.PreventUpdate()
    
    pattern_data = pd.read_csv('Patterns/' + patt_name) # Read the pattern from csv
    fig = px.line(pattern_data, x = 'screen', y = 'pattern', title = 'Interference pattern', labels = {
        'screen': 'x [cm]',
        'pattern': 'Field intensity'
    }) # Create the figure

    return fig, ['Plot number {}'.format(n_clicks + 1)], ['Filter type: ' + pattern_data['filter_type'][0] + ', filter width: {}'.format(pattern_data['filter_width'][0]) + r'$\, \mathrm{cm}^{-1}$' + ', slit separation: {}'.format(pattern_data['slits_dist'][0]) + r'$\, \mathrm{mm}$']

@callback(
    # This is the callback for the plot of an individual pattern in the data analysis part. A long callback isn't necessary here
    Output('sample-speckle', 'figure'), # Output a counter, the graph and the parameters of the pattern
    Output('counter-field-plot', 'children'),
    Input('plot-field', 'n_clicks'), # Input the button click, other parameters are states
    State('select-field-plot', 'value')
)
def plot_field(n_clicks, field_name):
    if n_clicks is None:
        raise exceptions.PreventUpdate()
    
    field_data = pd.read_csv('Speckles/' + field_name) # Read the pattern from csv
    data_spec = pd.concat([field_data['screen'], (field_data['spec_re'] ** 2 + field_data['spec_im'] ** 2).rename('spec')], axis = 1)

    fig = px.line(data_spec, x = 'screen', y = 'spec', title = 'Speckle field', labels = {
        'screen': 'x [cm]',
        'spec': 'Field intensity'
    }) # Create the figure

    return fig, ['Plot number {}'.format(n_clicks + 1)],

@callback(
    # Callback for analysis of a single field
    Output('visibility', 'children'),
    Output('patt-prof', 'figure'),
    Output('patt-norm', 'figure'),
    Output('counter-processing', 'children'),
    Input('process-button', 'n_clicks'), # Input the button click, other parameters are states
    State('select-pattern', 'value'),
    State('fit-guess', 'value'),
    State('fit-guess-2', 'value'),
    State('fit-guess-3', 'value')
)
def analyze(n_clicks, patt_name, guess, A_1, B_1):
    if n_clicks is None:
        raise exceptions.PreventUpdate()

    pattern_data = pd.read_csv('Patterns/' + patt_name) # Read the pattern from csv

    with open('numbers.json', 'r') as f:
        numbers = json.load(f)

    with open('intensity.json', 'r') as f:
        totem = json.load(f)

    # get the correct intensity, corresponding to the given filter width
    fw = pattern_data['filter_width'][0]
    for t in totem:
        if t[0] == fw:
            avg_intensity_f = t[1]

    avg_intensity = numbers['avg_intensity']
    slit_width = numbers['slit_width_mm']
    dist_2 = numbers['dist2_cm']
    wavelen = numbers['wavelen_nm']
    screen_size = numbers['screen_size_cm']
    dx = numbers['dx_cm']
    sample_size = numbers['field_num']

    avg_intensity_f = avg_intensity_f * sample_size / dx ** 2
    # nedded since 1) the averaged pattern is calculated by summing (instead of averaging) over the ensemble, and 2) avg_intensity is supposed to be an integral, not a sum.

    # Convert lengths to cm
    slit_width = slit_width / 10
    wavelen = wavelen / 1e7 

    

    patt_data_proc, patt_data_norm, vis = mod.process_pattern(pattern_data, guess, A_1, B_1, dist_2, wavelen, slit_width, avg_intensity_f)
    
    # fig_1 = px.line(patt_data_proc.melt(id_vars = 'screen', value_vars = ['pattern', 'prof_up', 'prof_down']), x = 'screen', y = 'value', title = 'Interference pattern', line_group = 'variable', color = 'variable')
    fig_1 = px.line(patt_data_proc.melt(id_vars = 'screen', value_vars = ['pattern', 'prof_up', 'prof_down']), x = 'screen', y = 'value', title = 'Interference pattern', line_group = 'variable', color = 'variable', labels = {
        'screen': 'x [cm]',
        'pattern': 'Interference pattern',
        'prof_up': 'Upper profile',
        'prof_down': 'Lower profile',
        'value': 'Field intensity',
        'variable': 'Legend'
    })
    fig_2 = px.line(patt_data_norm, x = 'screen_cut', y = 'patt_norm', title = 'Normalized interference pattern', labels = {
        'screen_cut': 'x [cm]',
        'patt_norm': 'Field intensity'
    })

    if os.path.exists('corr_data.csv'):
        vis_data = pd.read_csv('corr_data.csv')
        filt_wid = vis_data['filter_width'].to_numpy()
        sli_dis = vis_data['slits_dist'].to_numpy()
        visib = vis_data['corr'].to_numpy()
        phase = vis_data['phase'].to_numpy()
        condition = np.logical_and(filt_wid == pattern_data['filter_width'][0], np.logical_or(sli_dis == pattern_data['slits_dist'][0], sli_dis == -pattern_data['slits_dist'][0]))
        visib[condition] = vis
        vis_data = pd.DataFrame({
            'slits_dist': sli_dis,
            'filter_width': filt_wid,
            'corr': visib,
            'phase': phase,
            'filter_type': [pattern_data['filter_type'][0] for i in range(len(sli_dis))]
        })
        vis_data.to_csv('corr_data.csv')


    return  ['Visibility = {}'.format(vis)], fig_1, fig_2, ['Processing number {}'.format(n_clicks + 1)]

@callback( # Callback for the preliminary analysis
    Output('patt-preprocess', 'figure'),
    Output('counter-preprocessing', 'children'),
    Input('preprocess-button', 'n_clicks'),
    State('pre-options', 'value'),
    State('fit-guess', 'value'),
    State('fit-guess-2', 'value'),
    State('fit-guess-3', 'value'),
    State('select-pattern', 'value')
)
def pre_process(n_clicks, options, guess, A_1, B_1, patt_name):
    if n_clicks is None:
        raise exceptions.PreventUpdate()

    with open('numbers.json', 'r') as f:
        numbers = json.load(f)

    with open('intensity.json', 'r') as f:
        totem = json.load(f)

    avg_intensity = numbers['avg_intensity']
    slit_width = numbers['slit_width_mm']
    dist_2 = numbers['dist2_cm']
    wavelen = numbers['wavelen_nm']
    screen_size = numbers['screen_size_cm']
    dx = numbers['dx_cm']
    sample_size = numbers['field_num']

    # Convert lengths to cm
    slit_width = slit_width / 10
    wavelen = wavelen / 1e7 

    pattern_data = pd.read_csv('Patterns/' + patt_name) # Read the pattern from csv

    # get the correct intensity, corresponding to the given filter width
    fw = pattern_data['filter_width'][0]
    for t in totem:
        if t[0] == fw:
            avg_intensity_f = t[1]

    avg_intensity_f = avg_intensity_f * sample_size / dx ** 2

    fig_data, fig_layout = mod.pre_process(pattern_data, slit_width, wavelen, dist_2, options, guess, A_1, B_1, avg_intensity_f)

    fig = go.Figure(data = fig_data, layout = fig_layout)

    return fig, 'Run number {}'.format(n_clicks + 1)

@app.long_callback( 
    # This is the callback for the first simulation. Long callback since for regular callbacks there's a max time of 30 s.
    # Also, long callback allows to manage the layout during the function call
    output = [
        Output('counter-three', 'children'),
        # Output('graph-all', 'figure')
    ],
    inputs = [
        Input('part-three-button', 'n_clicks'), # The only input is the click of the 'start' button
        State('norm-method', 'value'),
        # The other parameters are passed as states, so changing them does not trigger the start of the simulation,
        # State('select-pattern', 'value')
    ],
    running=[ # When the simulation is running,
        (Output('part-three-button', 'disabled'), True, False), # The start button is disabled
        (Output('cancel-three', 'disabled'), False, True), # And it is possible to cancel the operation
        (
            Output('counter-three', 'style'), # Show or hide the counter (visible when not running, hidden when running)
            {'visibility': 'hidden'},
            {'visibility': 'visible'},
        ),
        (
            Output('progress-bar-three', 'style'), # Show or hide the progress bar (hidden when not running, visible when running)
            {'visibility': 'visible'},
            {'visibility': 'hidden'},
        ),
    ],
    cancel = [Input('cancel-three', 'n_clicks')], # Link to cancel button id
    progress = [Output('progress-bar-three', 'value'), Output('progress-bar-three', 'max')], # Link to progress bar id
    manager = long_callback_manager
)
def analyze_all(set_progress, n_clicks, method):
    if n_clicks is None:
        raise exceptions.PreventUpdate()
    
    vect = os.listdir('Patterns')
    num = len(vect)

    with open('numbers.json', 'r') as f:
        numbers = json.load(f)

    with open('intensity.json', 'r') as f:
        totem = json.load(f)

    avg_intensity = numbers['avg_intensity']
    slit_width = numbers['slit_width_mm']
    dist_2 = numbers['dist2_cm']
    wavelen = numbers['wavelen_nm']
    screen_size = numbers['screen_size_cm']
    dx = numbers['dx_cm']
    sample_size = numbers['field_num']

    # Convert lengths to cm
    slit_width = slit_width / 10
    wavelen = wavelen / 1e7 

    visib = []
    filter_width = []
    slits_dist = []
    phase = []
    
    counter = 1
    for i in vect:
        data_temp = pd.read_csv('Patterns/' + i)

        # get the correct intensity, corresponding to the given filter width
        fw = data_temp['filter_width'][0]
        for t in totem:
            if t[0] == fw:
                avg_intensity_f = t[1]

        avg_intensity_f = avg_intensity_f * sample_size / dx ** 2

        vis, pha, _, _, _ = mod.fast_process(data_temp, slit_width, wavelen, dist_2, method, avg_intensity_f)

        slits_dist.append(round(data_temp['slits_dist'][0], 2))
        filter_width.append(round(data_temp['filter_width'][0], 2))
        visib.append(vis)
        phase.append(pha)

        # Mirror the data by symmetry
        slits_dist.append(-round(data_temp['slits_dist'][0], 2))
        filter_width.append(round(data_temp['filter_width'][0], 2))
        visib.append(vis)
        phase.append(pha)

        set_progress((str(counter), str(num)))
                     
    data = pd.DataFrame({
        'slits_dist': slits_dist,
        'filter_width': filter_width,
        'corr': visib,
        'phase': phase,
        'filter_type': [data_temp['filter_type'][0] for i in range(len(slits_dist))]
    })
    
    data.to_csv('corr_data.csv')

    # fig = px.scatter(data, x = 'slits_dist', y = 'vis', title = 'Visibility', color = 'filter_width')

    return ['Analysis number {}'.format(n_clicks + 1)]


@callback(
    # Callback for choosing the filter width to plot
    Output('select-filter-width', 'options'),
    Input('choose-filter', 'n_clicks'), # Input the button click, other parameters are states
)
def choose_filter(n_clicks):
    if n_clicks is None:
        raise exceptions.PreventUpdate()
    corr_data = pd.read_csv('corr_data.csv')
    filter_width = corr_data['filter_width'].to_numpy()
    
    return np.sort(np.array([i for i in set(filter_width)])) # Remove redundancy

@callback(
    # Callback for plotting the correlation functions
    Output('counter-plot-all', 'children'),
    Output('graph-all', 'figure'),
    Input('plot-all-button', 'n_clicks'), # Input the button click, other parameters are states
    State('select-filter-width', 'value')
)
def plot_all(n_clicks, selected_fw):
    if n_clicks is None:
        raise exceptions.PreventUpdate()
    
    with open('numbers.json', 'r') as f:
        numbers = json.load(f)

    wavelen = numbers['wavelen_nm']

    corr_data = pd.read_csv('corr_data.csv')
    corr_data = corr_data[corr_data['filter_width'] == selected_fw]

    filter_width = corr_data['filter_width'].to_numpy()
    slits_dist = corr_data['slits_dist'].to_numpy()
    filter_type = corr_data['filter_type'].to_numpy()

    M = np.max(slits_dist)
    m = np.min(slits_dist)

    x_axis = np.linspace(m, M, 500)

    theo = [x_axis]
    cols = ['x_axis']

    fw = filter_width * wavelen / (2e5 * np.pi) 

    for f in set(filter_width):
        if filter_type[0] == 'Rectangular':
            theo.append(np.abs(np.sinc(f * x_axis / (2 * np.pi))))
        else:
            theo.append(np.exp(-2 * (f * x_axis / 2) ** 2))
        cols.append(str(f))

    corr_theo = pd.DataFrame(columns = cols, data = np.transpose(np.array(theo)))

    fig_1 = px.scatter(corr_data, x = 'slits_dist', y = 'corr', title = 'Field correlation function', color = 'filter_width', labels = {
        'slits_dist': 'Slit separation [mm]',
        'corr': 'Correlation',
        'filter_width': 'Filter width'
    }) 

    fig_2 = px.line(corr_theo.melt(id_vars = 'x_axis', value_vars = cols[1:]), x = 'x_axis', y = 'value', line_group = 'variable', color = 'variable')
    fig_2.update_traces(line = dict(color = 'rgba(50,50,50,0.2)'))

    fig = go.Figure(data = fig_1.data + fig_2.data, layout = fig_1.layout)

    fig.update_layout(title = go.layout.Title(text = 'Field correlation function'), 
                      xaxis = go.layout.XAxis(title = go.layout.xaxis.Title(text = 'Slit separation [mm]')),
                      yaxis = go.layout.YAxis(title = go.layout.yaxis.Title(text = 'Correlation function')),
                      legend_visible = False
    )

    return ['Plot number {}'.format(n_clicks + 1)], fig

@callback(
    # Callback for plotting the correlation length versus the filter width
    Output('counter-plot-cvf', 'children'),
    Output('graph-cvf', 'figure'),
    Input('plot-cvf-button', 'n_clicks'), # Input the button click, other parameters are states
)
def plot_cvf(n_clicks):
    if n_clicks is None:
        raise exceptions.PreventUpdate()
    
    with open('numbers.json', 'r') as f:
        numbers = json.load(f)

    wavelen = numbers['wavelen_nm']
    wavelen = wavelen / 1e7 # Convert to cm
    
    corr_data = pd.read_csv('corr_data.csv')
    filter_width = corr_data['filter_width'].to_numpy()
    corr = corr_data['corr'].to_numpy()
    slits_dist = corr_data['slits_dist'].to_numpy()

    fw = []
    cl = []

    for f in set(filter_width):
        temp_corr = corr[filter_width == f]
        temp_sl = slits_dist[filter_width == f]

        # Sort the arrays properly
        ind = np.argsort(temp_sl)
        temp_sl = temp_sl[ind]
        temp_corr = temp_corr[ind]

        cl.append(mod.FWHM(temp_corr, temp_sl) * 10) # Convert to mm
        # fw.append((wavelen * 1e-7 * f * 100/ (2 * np.pi))) # Convert to mm
        fw.append(f)

    fw = np.array(fw)
    cl = np.array(cl)

    ind = np.argsort(fw)
    fw = fw[ind]
    cl = cl[ind]

    # Fit con una proporzionalità inversa
    def fit_invrel(x, y):
        A = np.sum(1 / x ** 2)
        B = np.sum(y / x)

        return B / A

    popt = fit_invrel(fw, cl)

    df = pd.DataFrame({
        'filter_width': fw,
        'corr_length': cl,
    })

    df2 = pd.DataFrame({
        'filter_width': fw,
        'fit': popt / fw
    })

    fig = go.Figure(layout = go.Layout(title = 'Inverse relation between correlation length and filter width'))
    fig.update_xaxes(title_text='Correlation length [mm]')
    fig.update_yaxes(title_text='Filter width [mm]')

    fig.add_trace(go.Scatter(x = df['filter_width'], y = df['corr_length'], name = 'Data'))
    fig.add_trace(go.Scatter(x = df2['filter_width'], y = df2['fit'], name = 'Fit', mode = 'lines'))
    
    # fig.add_trace(px.line(df2, x = 'filter_width', y = 'fit'))

    #fig = px.scatter(df, x = 'filter_width', y = 'corr_length', title = 'Inverse relation between correlation length and filter width', labels = {
    #    'corr_length': 'Correlation length [mm]',
    #   'filter_width': 'Filter width [mm]'
    # })
    
    
    df.to_csv('corr_vs_filter.csv')

    return ['Plot number {}'.format(n_clicks + 1)], fig


if __name__ == '__main__':
    app.run(debug=True)