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
from buzz.constants import SHORT_TO_LONG_NAME
from buzz.dashview import MAPPING, CHART_TYPES, _make_component, PLOTTERS, _df_to_figure
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from app.tabs import (
    _make_tabs,
    _build_dataset_space,
    _build_frequencies_space,
    _build_chart_space,
    _build_concordance_space,
    _update_datatable,
)
from app.cmd import _parse_cmdline_args
from app.strings import _make_search_name, _make_table_name

import pandas as pd

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True
# store corpus and search results in here
SEARCHES = OrderedDict()
TABLES = OrderedDict()


@app.callback(Output("input-box", "placeholder"), [Input("search-target", "value")])
def _correct_placeholder(value):
    if value == "d":
        return "Enter depgrep query..."
    else:
        return "Enter regular expression search query..."


@app.callback(
    [
        Output("tab-dataset", "style"),
        Output("tab-frequencies", "style"),
        Output("tab-chart", "style"),
        Output("tab-concordance", "style"),
    ],
    [Input("tabs", "value")],
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


for i in range(1, 4):

    @app.callback(
        Output(f"chart-{i}", "figure"),
        [Input(f"figure-button-{i}", "n_clicks")],
        [
            State(f"chart-from-{i}", "value"),
            State(f"chart-type-{i}", "value"),
            State(f"chart-top-n-{i}", "value"),
            State(f"chart-transpose-{i}", "on"),
        ],
    )
    def _new_chart(n_clicks, table_from, chart_type, top_n, transpose):
        """
        Make new chart by kind
        """
        if n_clicks is None:
            raise PreventUpdate
        specs, df = _get_from_corpus(table_from, dataset=TABLES)
        if transpose:
            df = df.T
        df = df.iloc[:, :top_n]
        return _df_to_figure(df, chart_type)


@app.callback(
    [
        Output("conll-view", "columns"),
        Output("conll-view", "data"),
        Output("search-from", "options"),
        Output("search-from", "value"),
    ],
    [Input("search-button", "n_clicks"),
     Input("clear-history", "n_clicks")],
    [
        State("search-from", "value"),
        State("skip-switch", "on"),
        State("search-target", "value"),
        State("input-box", "value"),
        State("search-from", "options"),
    ],
)
def _new_search(
    n_clicks, cleared, search_from, skip, col, search_string, search_from_options
):
    """
    Callback when a new search is submitted
    """
    if n_clicks is None:
        raise PreventUpdate

    if cleared:
        corpus = SEARCHES["corpus"]
        SEARCHES.clear()
        SEARCHES["corpus"] = corpus
        # the line below could be slow. can we get from elsewhere?
        datatable_cols, datatable_data = _update_datatable(SEARCHES["corpus"], SEARCHES["corpus"])
        search_from = [
            dict(value=i, label=_make_search_name(h)) for i, h in enumerate(SEARCHES)
        ]
        return datatable_cols, datatable_data, search_from, 0

    specs, corpus = _get_from_corpus(search_from)
    method = "just" if not skip else "skip"
    df = getattr(getattr(corpus, method), col)(search_string.strip())
    # we store this search specs as a tuple, with first item being specs of last search?
    # maybe can just store search_from instead?
    new_value = len(SEARCHES)
    this_search = (specs, col, skip, search_string, new_value)
    SEARCHES[this_search] = df.index
    datatable_cols, datatable_data = _update_datatable(SEARCHES["corpus"], df)
    option = dict(value=new_value, label=_make_search_name(this_search))
    search_from_options.append(option)
    return datatable_cols, datatable_data, search_from_options, new_value


@app.callback(
    [
        Output("freq-table", "columns"),
        Output("freq-table", "data"),
        Output("chart-from-1", "options"),
        Output("chart-from-1", "value"),
        Output("chart-from-2", "options"),
        Output("chart-from-2", "value"),
        Output("chart-from-3", "options"),
        Output("chart-from-3", "value"),
    ],
    [Input("table-button", "n_clicks")],
    [
        State("search-from", "value"),
        State("show-for-table", "value"),
        State("subcorpora-for-table", "value"),
        State("relative-for-table", "value"),
        State("sort-for-table", "value"),
        State("chart-from-1", "options"),
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
    nv = len(TABLES)
    this_table = (specs, tuple(show), subcorpora, relative, keyness, sort, nv)
    TABLES[this_table] = table
    cols, data = _update_datatable(SEARCHES["corpus"], table, conll=False)
    option = dict(value=nv, label=_make_table_name(this_table))
    tfo = table_from_options + [option]
    return cols, data, tfo, nv, tfo, nv, tfo, nv


def _translate_relative(inp):
    """
    Get relative and keyness from two-character input
    """
    assert len(inp) == 2
    mapping = dict(t=True, f=False, n=SEARCHES["corpus"], l="ll", p="pd")
    return mapping[inp[0]], mapping[inp[1]]


if __name__ == "__main__":
    # when run as script, parse the command line arguments and start the site
    kwargs = _parse_cmdline_args()
    path = kwargs["path"]
    title = kwargs["title"] or f"Explore: {os.path.basename(path)}"
    # create all the data we start with. loaded corpus, nouns, and noun table
    SEARCHES["corpus"] = Corpus(path).load()
    open_class = ["NOUN", "VERB", "ADJ", "ADV"]
    TABLES["initial"] = (
        SEARCHES["corpus"].just.x(open_class).table(show="x", subcorpora="file")
    )
    app.layout = _make_tabs(title, SEARCHES, TABLES)
    app.run_server(debug=True)
