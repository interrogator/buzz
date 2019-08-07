"""
buzz webapp: everything needed to populate app tabs initially
"""

import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq

from .strings import _make_table_name, _make_search_name
from .utils import _get_cols, _update_datatable
from buzz.constants import SHORT_TO_COL_NAME
from buzz.dashview import CHART_TYPES, _df_to_figure


def _build_dataset_space(df, rows):
    """
    Build the search interface and the conll display
    """
    cols = _get_cols(df)
    cols += [dict(label="Dependencies", value="d"), dict(label="Trees", value="t")]
    df = df.reset_index()
    df = df.drop(["parse", "text", "e", "sent_id", "sent_len"], axis=1, errors="ignore")
    pieces = [
        dcc.Dropdown(
            id="search-target", options=cols, value="w", style={"width": "200px", "fontFamily": "monospace"}
        ),
        dcc.Input(
            id="input-box",
            type="text",
            placeholder="Enter regular expression search query...",
            size="120",
            style={"fontFamily": "monospace", "marginLeft": 5, "marginRight": 5},
        ),
        daq.BooleanSwitch(
            id="skip-switch",
            on=False,
            style={"verticalAlign": "middle", "marginLeft": 5, "marginRight": 5},
        ),
        html.Button("Search", id="search-button"),
    ]
    pieces = [
        html.Div(
            piece,
            style={
                "display": "table-cell",
                "verticalAlign": "middle",
                "height": "35px",
            },
        )
        for piece in pieces
    ]
    # add tooltip to boolean switch
    pieces[2].title = "Invert result"
    # pieces[0].style['position'] = "absolute";
    search_space = html.Div(pieces, style={"marginBottom": 15, "marginTop": 15, "fontFamily": "bold"})
    columns = [
        {
            "name": SHORT_TO_COL_NAME.get(i, i).capitalize().replace("_", " "),
            "id": i,
            "deletable": i not in ["s", "i"],
        }
        for i in df.columns
    ]
    data = df.to_dict("rows")
    left_aligns = ["file", "w", "l", "x", "p", "f", "speaker", "setting"]
    style_index = [
        {
            "if": {"column_id": c},
            "backgroundColor": "#fafafa",
            # "color": "white",
            "color": "#555555",
            "fontWeight": "bold",
        }
        for c in ["file", "s", "i"]
    ]
    # style_index.append({"if": {"column_id": "w"}, "fontWeight": "bold"})
    stripes = [{"if": {"row_index": "odd"}, "backgroundColor": "rgb(248, 248, 248)"}]
    aligns = [{"if": {"column_id": c}, "textAlign": "left", "paddingLeft": "5px"} for c in left_aligns]
    pads = [{"if_not": {"column_id": c}, "paddingRight": "5px"} for c in left_aligns]
    conll_table = dcc.Loading(
        type="default",
        children=[
            dash_table.DataTable(
                id="conll-view",
                columns=columns,
                data=data,
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                # row_selectable="multi",
                row_deletable=True,
                selected_rows=[],
                page_action="native",
                page_current=0,
                page_size=rows,
                # style_as_list_view=True,
                style_header={"fontWeight": "bold", "color": "#555555"},
                style_cell_conditional=aligns + pads,
                style_data_conditional=style_index + stripes,
            )
        ],
    )
    return html.Div(id="dataset-container", children=[search_space, conll_table])


def _build_frequencies_space(corpus, table, rows):
    """
    Build stuff related to the frequency table
    """
    cols = _get_cols(corpus)
    show_check = dcc.Dropdown(
        placeholder="Features to show",
        multi=True,
        id="show-for-table",
        options=cols,
        value=[],
        style={"marginLeft": 5, "marginRight": 5, "fontFamily": "monospace"},
    )
    subcorpora_drop = dcc.Dropdown(
        id="subcorpora-for-table",
        options=cols,
        placeholder="Feature for index",
        style={"marginLeft": 5, "marginRight": 5, "fontFamily": "monospace"},
    )
    relative_drop = dcc.Dropdown(
        id="relative-for-table",
        style={"marginLeft": 5, "marginRight": 5, "fontFamily": "monospace"},
        options=[
            {"label": "Absolute frequency", "value": "ff"},
            {"label": "Relative of result", "value": "tf"},
            {"label": "Relative of corpus", "value": "nf"},
            {"label": "Keyness: log likelihood", "value": "fl"},
            {"label": "Keyness: percent difference", "value": "fp"},
        ],
        placeholder="Relative/keyness calculation",
    )
    sort_drop = dcc.Dropdown(
        id="sort-for-table",
        style={"marginLeft": 5, "marginRight": 5, "fontFamily": "monospace"},
        options=[
            {"label": "Total", "value": "total"},
            {"label": "Infrequent", "value": "infreq"},
            {"label": "Alphabetical", "value": "name"},
            {"label": "Increasing", "value": "increase"},
            {"label": "Decreasing", "value": "decrease"},
            {"label": "Static", "value": "static"},
            {"label": "Turbulent", "value": "turbulent"},
        ],
        placeholder="Sort columns by...",
    )
    columns, data = _update_datatable(corpus, table, conll=False)
    style_index = [
        {
            "if": {"column_id": table.index.name},
            "backgroundColor": "#fafafa",
            # "color": "white",
            "fontWeight": "bold",
        }
    ]
    stripes = [{"if": {"row_index": "odd"}, "backgroundColor": "rgb(248, 248, 248)"}]
    left_aligns = ["file", "w", "l", "x", "p", "f", "speaker", "setting"]
    aligns = [{"if": {"column_id": c}, "textAlign": "left", "paddingLeft": "5px"} for c in left_aligns]
    pads = [{"if_not": {"column_id": c}, "paddingRight": "5px"} for c in left_aligns]
    freq_table = dcc.Loading(
        type="default",
        children=[
            dash_table.DataTable(
                id="freq-table",
                columns=columns,
                data=data,
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                # row_selectable="multi",
                row_deletable=True,
                selected_rows=[],
                page_action="native",
                page_current=0,
                page_size=rows,
                style_header={"fontWeight": "bold", "color": "#555555"},
                style_cell_conditional=aligns + pads,
                style_data_conditional=style_index + stripes,
            )
        ],
    )

    style = dict(
        display="inline-block", verticalAlign="middle", height="35px", width="25%"
    )
    left = html.Div(
        [html.Div(show_check, style=style), html.Div(subcorpora_drop, style=style)]
    )
    right = html.Div(
        [
            html.Div(sort_drop, style=style),
            html.Div(relative_drop, style=style),
            html.Button(
                "Generate table",
                id="table-button",
                style={**style, **{"width": "20%", "marginLeft": 5, "marginRight": 5}},
            ),
        ]
    )
    toolbar = html.Div([left, right], style={"marginBottom": 15, "marginTop": 15})
    return html.Div([toolbar, freq_table])


def _build_concordance_space(df, rows):
    """
    Div representing the concordance tab
    """
    cols = _get_cols(df)

    show_check = dcc.Dropdown(
        multi=True,
        placeholder="Features to show",
        id="show-for-conc",
        options=cols,
        style={"marginLeft": 5, "marginRight": 5, "fontFamily": "monospace"},
    )
    update = html.Button(
        "Update", id="update-conc", style={"marginLeft": 5, "marginRight": 5}
    )
    style = dict(
        display="table-cell", verticalAlign="middle", height="35px", width="100%"
    )
    toolbar = [html.Div(i, style=style) for i in [show_check, update]]
    conc_space = html.Div(toolbar, style={"marginBottom": 15, "marginTop": 15})
    df = df.just.x.NOUN.conc(metadata=["file", "s", "i", "speaker"], window=(80, 80))
    df = df[["left", "match", "right", "file", "s", "i", "speaker"]]
    columns = [
        {
            "name": SHORT_TO_COL_NAME.get(i, i),
            "id": i,
            "deletable": i not in ["left", "match", "right"],
        }
        for i in df.columns
    ]
    data = df.to_dict("rows")
    left_aligns = ["match", "right", "speaker", "file"]
    aligns = [{"if": {"column_id": c}, "textAlign": "left", "paddingLeft": "5px"} for c in left_aligns]
    pads = [{"if_not": {"column_id": c}, "paddingRight": "5px"} for c in left_aligns]
    conc = dcc.Loading(
        type="default",
        children=[
            dash_table.DataTable(
                id="conc-table",
                columns=columns,
                data=data,
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                # row_selectable="multi",
                row_deletable=True,
                selected_rows=[],
                page_action="native",
                page_current=0,
                page_size=rows,
                # style_as_list_view=True,
                style_header={"fontWeight": "bold", "color": "#555555"},
                style_cell_conditional=pads + aligns,
                style_data_conditional=[
                    {
                        "if": {"column_id": "match"},
                        "fontWeight": "bold",
                        "paddingLeft": "10px",
                    },
                    {"if": {"column_id": "file"}, "fontWeight": "bold"},
                    {
                        "if": {"row_index": "odd"},
                        "backgroundColor": "rgb(248, 248, 248)",
                    },
                ],
            )
        ],
    )

    return html.Div([conc_space, conc])


def _build_chart_space(tables, rows):
    """
    Div representing the chart tab
    """
    charts = []
    for chart_num, kind in [
        (1, "bar"),
        (2, "line"),
        (3, "area"),
        (4, "heatmap"),
        (5, "stacked_bar"),
    ]:

        table_from = [
            dict(value=i, label=_make_table_name(h)) for i, h in enumerate(tables)
        ]
        dropdown = dcc.Dropdown(
            id=f"chart-from-{chart_num}", options=table_from, value=0, style=dict(fontFamily="monospace")
        )
        types = [dict(label=i.capitalize().replace('_', ' '), value=i) for i in sorted(CHART_TYPES)]
        chart_type = dcc.Dropdown(
            id=f"chart-type-{chart_num}",
            options=types,
            value=kind,
            style={"marginLeft": 5, "marginRight": 5, "fontFamily": "monospace"},
        )
        transpose = (
            daq.BooleanSwitch(
                id=f"chart-transpose-{chart_num}",
                on=False,
                style={"verticalAlign": "middle"},
            ),
        )
        top_n = dcc.Input(
            id=f"chart-top-n-{chart_num}",
            placeholder="Results to plot",
            type="number",
            min=1,
            max=99,
            value=7,
            style={"marginLeft": 5, "marginRight": 5},
        )
        update = html.Button("Update", id=f"figure-button-{chart_num}")

        toolbar = [dropdown, chart_type, top_n, transpose, update]
        style = dict(display="inline-block", verticalAlign="middle")
        widths = {
            dropdown: "50%",
            chart_type: "25%",
            top_n: "10%",
            transpose: "5%",
            update: "10%",
        }
        tools = list()
        for component in toolbar:
            width = widths.get(component, "10%")
            nstyle = {**style, **{"width": width}}
            div = html.Div(component, style=nstyle)
            if component == transpose:
                div.title = "Transpose axes"
            elif component == top_n:
                div.title = "Number of entries to display"
            tools.append(div)
        toolbar = html.Div(tools, style={"marginBottom": 15, "marginTop": 15})
        df = tables["initial"]
        figure = _df_to_figure(df, kind=kind)
        chart_data = dict(
            id=f"chart-{chart_num}", figure=figure, style={"height": "500px"}
        )
        chart = dcc.Loading(type="default", children=[dcc.Graph(**chart_data)])
        chart_space = html.Div([toolbar, chart])
        collapse = html.Details(
            [
                html.Summary(f"Chart #{chart_num}", style={"fontWeight": "bold", "fontSize": "11pt", "fontFamily": "monospace", "paddingBottom": "10px", "paddingTop": "10px", "color": "#555555"}),
                html.Div(chart_space),
            ],
            open=chart_num == 1,
            #style={"borderStyle": "groove"}
        )
        charts.append(collapse)
    return html.Div(charts)


def _make_tabs(searches, tables, title=None, rows=25, **kwargs):
    """
    Generate initial layout div
    """
    corpus = next(iter(searches.values()))
    dataset = _build_dataset_space(corpus, rows)
    frequencies = _build_frequencies_space(corpus, tables["initial"], rows)
    chart = _build_chart_space(tables, rows)
    concordance = _build_concordance_space(corpus, rows)

    search_from = [
        dict(value=i, label=_make_search_name(h)) for i, h in enumerate(searches)
    ]
    clear = html.Button("Clear history", id="clear-history", style={"marginLeft": 5})
    dropdown = dcc.Dropdown(
        id="search-from", options=search_from, value=0, disabled=True
    )

    top_bit = [
        html.H3(children=title, style={"textAlign": "left", "display": "table-cell"}),
        dcc.ConfirmDialog(
            id='dialog-search',
            message='',
        ),
        dcc.ConfirmDialog(
            id='dialog-table',
            message='',
        ),
        dcc.ConfirmDialog(
            id='dialog-chart',
            message='',
        ),
        dcc.ConfirmDialog(
            id='dialog-conc',
            message='',
        ),
        html.Div(
            dropdown,
            style=dict(
                fontFamily="monospace",
                display="table-cell",
                width="60%",
                verticalAlign="middle",
                height="35px",
            ),
        ),
        html.Div(
            clear,
            style=dict(
                display="table-cell", width="10%", verticalAlign="middle", height="35px"
            ),
        ),
    ]
    top_bit = html.Div(top_bit, style={"marginBottom": 15, "marginTop": 15})
    style = dict(font="12px Arial", fontWeight=600, color="#555555")
    tab_headers = dcc.Tabs(
        id="tabs",
        value="dataset",
        style={"lineHeight": 0, "fontFamily": "monospace", **style},
        children=[
            dcc.Tab(label="DATASET", value="dataset"),
            dcc.Tab(label="FREQUENCIES", value="frequencies"),
            dcc.Tab(label="CHART", value="chart"),
            dcc.Tab(label="CONCORDANCE", value="concordance"),
        ],
    )

    tab_contents = [
        html.Div(
            id="tab-dataset",
            style={"display": "none"},
            children=[html.Div(id="display-dataset", children=[dataset])],
        ),
        html.Div(
            id="tab-frequencies",
            style={"display": "none"},
            children=[html.Div(id="display-frequencies", children=[frequencies])],
        ),
        html.Div(
            id="tab-chart",
            style={"display": "none"},
            children=[html.Div(id="display-chart", children=[chart])],
        ),
        html.Div(
            id="tab-concordance",
            style={"display": "none"},
            children=[html.Div(id="display-concordance", children=[concordance])],
        ),
    ]
    tab_contents = html.Div(children=tab_contents)

    return html.Div([top_bit, tab_headers, tab_contents], style=dict(fontFamily="monospace !important"))
