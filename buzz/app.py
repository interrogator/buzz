import argparse
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import plotly.graph_objects as go
import os
import sys
from collections import OrderedDict
from buzz.corpus import Corpus
from buzz.dashview import MAPPING, CHART_TYPES, _make_component, PLOTTERS, _df_to_plot
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import pandas as pd

LABELS = dict(
    w="Word",
    l="Lemma",
    p="Part of speech",
    g="Governor index",
    f="Dependency role",
    x="Wordclass",
    i="Token index",
    s="Sentence number",
    file="Filename",
    speaker="Speaker",
)

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True
# store corpus and search results in here
SEARCHES = OrderedDict()
TABLES = OrderedDict()
INITIAL = dict()


def _parse_cmdline_args():
    """
    Command line argument parsing
    """
    parser = argparse.ArgumentParser(
        description="Run the buzzword app for a given corpus."
    )

    parser.add_argument(
        "-l",
        "--load",
        default=True,
        action="store_true",
        required=False,
        help="Load corpus into memory. Longer startup, faster search.",
    )

    parser.add_argument(
        "-t", "--title", nargs="?", type=str, required=False, help="Title for app"
    )

    parser.add_argument("path", help="Path to the corpus")

    return vars(parser.parse_args())


class Site(object):
    """
    Our site. It stores a very helpful attributes and methods, but the app is global
    """

    def __init__(self, path, title=None, load=True):
        self.path = path
        self.title = title or f"Explore: {os.path.basename(path)}"
        self.corpus = Corpus(self.path).load()
        self.colors = {"background": "#ffffff", "text": "#7FDBFF"}
        SEARCHES["corpus"] = self.corpus
        INITIAL["search"] = self.corpus.just.x.NOUN
        INITIAL["table"] = INITIAL["search"].table(show="l", subcorpora="f")
        TABLES["initial"] = INITIAL["table"]

        dataset = self._build_dataset_space()
        frequencies = self._build_frequencies_space()
        chart = self._build_chart_space()
        concordance = self._build_concordance_space()
        self._make_tabs(dataset, frequencies, chart, concordance)

    def _make_tabs(self, dataset, frequencies, chart, concordance):
        search_from = [
            dict(value=i, label=_make_search_name(h)) for i, h in enumerate(SEARCHES)
        ]
        dropdown = dcc.Dropdown(id="search-from", options=search_from, value=0)
        search_from = html.Div(dropdown)
        app.layout = html.Div(
            [
                html.H1(
                    children=self.title,
                    style={"textAlign": "center", "color": self.colors["text"]},
                ),
                search_from,
                dcc.Tabs(
                    id="tabs",
                    value="dataset",
                    children=[
                        dcc.Tab(label="Dataset", value="dataset"),
                        dcc.Tab(label="Frequencies", value="frequencies"),
                        dcc.Tab(label="Chart", value="chart"),
                        dcc.Tab(label="Concordance", value="concordance"),
                    ],
                ),
                html.Div(
                    children=[
                        html.Div(
                            id="tab-dataset",
                            style={"display": "none"},
                            children=[
                                html.Div(id="display-dataset", children=[dataset]),
                            ],
                        ),
                        html.Div(
                            id="tab-frequencies",
                            style={"display": "none"},
                            children=[
                                html.Div(
                                    id="display-frequencies", children=[frequencies]
                                ),
                            ],
                        ),
                        html.Div(
                            id="tab-chart",
                            style={"display": "none"},
                            children=[
                                html.Div(id="display-chart", children=[chart]),
                            ],
                        ),
                        html.Div(
                            id="tab-concordance",
                            style={"display": "none"},
                            children=[
                                html.Div(
                                    id="display-concordance", children=[concordance]
                                ),
                            ],
                        ),
                    ]
                ),
            ]
        )

    def add(self, kind="div", data=None, add=None, id=None, **kwargs):
        """
        Make a component and add it to site children
        """
        comp = _make_component(kind, data, add, id, **kwargs)
        app.layout.children.append(comp)

    def _build_dataset_space(self):
        """
        Build the search interface and the conll display
        """
        col_order = ["file", "s", "i"] + list(self.corpus.columns)
        cols = [
            dict(label=LABELS.get(i, i.title().replace("_", " ")), value=i)
            for i in col_order
        ]
        cols += [dict(label="Dependencies", value="d"), dict(label="Trees", value="t")]
        dropdown = dcc.Dropdown(id="colselect", options=cols, value="w")
        df = SEARCHES["corpus"]
        df = df.reset_index()
        df = df[[i for i in col_order if i not in ["parse", "text"]]]

        search_space = html.Div(
            [
                html.Div(dropdown, style={"width": "20%", "display": "inline-block"}),
                html.Div(
                    dcc.Input(id="input-box", type="text"),
                    style={"width": "30%", "display": "inline-block"},
                ),
                html.Div(
                    daq.BooleanSwitch(id="skip-switch", on=False),
                    style={"display": "inline-block"},
                ),
                html.Div(
                    html.Button("Submit", id="search-button"),
                    style={"display": "inline-block"},
                ),
            ]
        )
        columns = [{"name": i, "id": i} for i in df.columns]
        data = df.to_dict("rows")
        conll_table = dash_table.DataTable(
            id="conll-view",
            columns=columns,
            data=data,
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            row_selectable="multi",
            row_deletable=True,
            selected_rows=[],
            page_action="native",
            page_current=0,
            page_size=50,
        )
        return html.Div(id="dataset-container", children=[search_space, conll_table])

    def _build_frequencies_space(self):
        """
        Build stuff related to the frequency table
        """
        cols = ["file", "s", "i"] + list(self.corpus.columns)
        cols = [dict(label=LABELS.get(i, i.title()), value=i) for i in cols]
        show_check = dcc.Checklist(id="show-for-table", options=cols, value=[])
        subcorpora_drop = dcc.Dropdown(
            id="subcorpora-for-table", options=cols, value="file"
        )
        relative_drop = dcc.Dropdown(
            id="relative-for-table",
            options=[
                {"label": "Absolute frequency", "value": "ff"},
                {"label": "Relative of result", "value": "tf"},
                {"label": "Relative of corpus", "value": "nf"},
                {"label": "Keyness: log likelihood", "value": "fl"},
                {"label": "Keyness: percent difference", "value": "fp"},
            ],
            value="tf",
        )
        sort_drop = dcc.Dropdown(
            id="sort-for-table",
            options=[
                {"label": "Total", "value": "total"},
                {"label": "Infrequent", "value": "infreq"},
                {"label": "Alphabetical", "value": "name"},
                {"label": "Increasing", "value": "increase"},
                {"label": "Decreasing", "value": "decrease"},
                {"label": "Static", "value": "static"},
                {"label": "Turbulent", "value": "turbulent"},
            ],
            value="total",
        )
        columns, data = _update_datatable(INITIAL["table"], conll=False)
        freq_table = dash_table.DataTable(
            id="freq-table",
            columns=columns,
            data=data,
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            row_selectable="multi",
            row_deletable=True,
            selected_rows=[],
            page_action="native",
            page_current=0,
            page_size=50,
        )

        table_space = html.Div(
            [
                html.Div(
                    [
                        html.Div(show_check),
                        html.Div(subcorpora_drop),
                        html.Div(sort_drop),
                        html.Div(relative_drop),
                        html.Button("Update", id="table-button"),
                        html.Div(
                            id="table-generate-outer", children="Generate a new table"
                        ),
                    ]
                ),
                freq_table,
            ]
        )

        return table_space

    def _build_concordance_space(self):

        cols = ["file", "s", "i"] + list(self.corpus.columns)
        cols = [dict(label=LABELS.get(i, i.title()), value=i) for i in cols]
        show_check = dcc.Checklist(id="show-for-conc", options=cols, value=[])
        conc_space = html.Div([show_check])
        df = INITIAL["search"].conc().head(100)
        columns = [{"name": i, "id": i} for i in df.columns]
        data = df.to_dict("rows")
        conc = dash_table.DataTable(
            id="conctable",
            columns=columns,
            data=data,
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            row_selectable="multi",
            row_deletable=True,
            selected_rows=[],
            page_action="native",
            page_current=0,
            page_size=50,
        )

        conc_space = html.Div([conc_space, conc])
        return conc_space

    def _build_chart_space(self):
        table_from = [
            dict(value=i, label=_make_table_name(h)) for i, h in enumerate(TABLES)
        ]
        dropdown = dcc.Dropdown(id="chart-from", options=table_from, value=0)
        types = [dict(label=i.title(), value=i) for i in CHART_TYPES]
        chart_type = dcc.Dropdown(id="chart-type", options=types, value="bar")
        chart_space = html.Div(
            [dropdown, html.Div(chart_type), html.Button("Update", id="figure-button")]
        )
        df = INITIAL["table"]
        figure = _df_to_figure(df, kind="bar")
        main_chart_data = dict(id="main-chart", figure=figure)
        return html.Div([chart_space, dcc.Graph(**main_chart_data)])


@app.callback(
    [
        Output("tab-dataset", "style"),
        Output("tab-frequencies", "style"),
        Output("tab-chart", "style"),
        Output("tab-concordance", "style"),
    ],
    [Input("tabs", "value")]
)
def render_content(tab):
    if tab is None:
        tab = "dataset"
    outputs = []
    for i in ["dataset", "frequencies", "chart", "concordance"]:
        if tab == i:
            outputs.append({"display": "block"})
        else:
            outputs.append({"display": "none"})
    return outputs


def _get_from_corpus(from_number, dataset=SEARCHES):
    """
    Get the correct dataset from number stored in the dropdown for search_from
    """
    specs, corpus = list(dataset.items())[from_number]
    # load from index to save memory
    if not isinstance(corpus, pd.DataFrame):
        corpus = dataset["corpus"].loc[corpus]
    return specs, corpus


def _make_search_name(history):
    """
    Generate a search name from its history
    """
    if history == "corpus":
        return "corpus"
    previous, col, skip, search_string = history
    no = "not " if skip else ""
    basic = f"{LABELS[col]} {no}matching '{search_string}'"
    hyphen = ""
    while isinstance(previous, tuple):
        hyphen += "─"
        previous = previous[0]
    if hyphen:
        basic = f"└{hyphen} " + basic
    return basic


def _make_table_name(history):
    """
    Generate a table name from its history
    """
    if history == "initial":
        return "Show lemma by dependency role -- from 'Corpus'"
    specs, show, subcorpora, relative, keyness, sort = history
    show = [LABELS.get(i, i).lower().replace('_', ' ') for i in show]
    show = ', '.join(show)
    relkey = " calculating relative frequency" if relative else " calculating keyness"
    if keyness:
        relkey = f"{relkey} ({keyness})"
    if relative is False and keyness is False:
        relkey = " showing absolute frequencies"
    basic = f"Table showing {show} by {subcorpora}{relkey}, sorting by {sort}"
    parent = _make_search_name(specs)
    return f"{basic} -- from '{parent}'"


@app.callback(
    Output("main-chart", "figure"),
    [Input("figure-button", "n_clicks")],
    [State("chart-from", "value"),
     State("chart-type", "value")],
)
def _new_chart(n_clicks, table_from, chart_type):
    """
    Make new chart by kind
    """
    if n_clicks is None:
        raise PreventUpdate
    specs, df = _get_from_corpus(table_from, dataset=TABLES)
    return _df_to_figure(df, chart_type)


@app.callback(
    [
        Output("conll-view", "columns"),
        Output("conll-view", "data"),
        Output("search-from", "options"),
        Output("search-from", "value"),
    ],
    [Input("search-button", "n_clicks")],
    [
        State("search-from", "value"),
        State("skip-switch", "on"),
        State("colselect", "value"),
        State("input-box", "value"),
        State("search-from", "options"),
    ],
)
def _new_search(n_clicks, search_from, skip, col, search_string, search_from_options):
    """
    Callback when a new search is submitted
    """
    specs, corpus = _get_from_corpus(search_from)
    if n_clicks is None:
        raise PreventUpdate
    method = "just" if not skip else "skip"
    df = getattr(getattr(corpus, method), col)(search_string.strip())
    # we store this search specs as a tuple, with first item being specs of last search?
    # maybe can just store search_from instead?
    this_search = (specs, col, skip, search_string)
    new_value = len(SEARCHES)
    SEARCHES[this_search] = df.index
    datatable_cols, datatable_data = _update_datatable(df)
    option = dict(value=new_value, label=_make_search_name(this_search))
    search_from_options.append(option)
    return datatable_cols, datatable_data, search_from_options, new_value


@app.callback(
    [
        Output("freq-table", "columns"),
        Output("freq-table", "data"),
        Output("chart-from", "options"),
        Output("chart-from", "value"),
    ],
    [Input("table-button", "n_clicks")],
    [
        State("search-from", "value"),
        State("show-for-table", "value"),
        State("subcorpora-for-table", "value"),
        State("relative-for-table", "value"),
        State("sort-for-table", "value"),
        State("chart-from", "options"),
    ],
)
def _new_table(
    n_clicks, search_from, show, subcorpora, relkey, sort, table_from_options
):
    """
    Callback when a new freq table is generated
    """
    if n_clicks is None:
        raise PreventUpdate
    specs, corpus = _get_from_corpus(search_from)
    relative, keyness = _translate_relative(relkey)
    table = corpus.table(
        show=show, subcorpora=subcorpora, relative=relative, keyness=keyness, sort=sort
    )
    this_table = (specs, tuple(show), subcorpora, relative, keyness, sort)
    new_value = len(TABLES)
    TABLES[this_table] = table
    cols, data = _update_datatable(table, conll=False)
    option = dict(value=new_value, label=_make_table_name(this_table))
    table_from_options.append(option)
    return (cols, data, table_from_options, new_value)


def _update_datatable(df, conll=True):
    """
    Helper for datatables
    """
    if conll:
        col_order = ["file", "s", "i"] + list(SEARCHES['corpus'].columns)
        col_order = [i for i in col_order if i not in ['parse', 'text']]
    else:
        col_order = list(df.index.names)
        extra = [i for i in list(df.columns) if i not in col_order]
        col_order += extra
    df = df.reset_index()
    df = df[col_order]
    columns = [{"name": i, "id": i} for i in df.columns]
    data = df.to_dict("rows")
    return columns, data


def _df_to_figure(df, kind="bar"):
    """
    Helper to generate charts
    """
    datapoints = list()
    plotter = PLOTTERS[kind]
    if kind == "heatmap":
        datapoints = plotter(df)
    else:
        for row_name, row in df.T.iterrows():
            datapoints.append(plotter(row_name, row))
    layout = dict(width=2000)
    if kind == "stacked_bar":
        layout["barmode"] = "stack"
    return dict(data=datapoints, layout=layout)


def _translate_relative(inp):
    """
    Get relative and keyness from two-character input
    """
    assert len(inp) == 2
    mapping = dict(t=True, f=False, n=SEARCHES["corpus"], l="ll", p="pd")
    return mapping[inp[0]], mapping[inp[1]]


if __name__ == "__main__":
    # when run as script, parse the command line arguments and start the site
    site = Site(**_parse_cmdline_args())
    app.run_server(debug=True)
