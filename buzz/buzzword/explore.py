# flake8: noqa

from collections import OrderedDict

import os
import pandas as pd

import dash
from buzz.corpus import Corpus
from buzz.dashview import _df_to_figure
from buzz.buzzword.helpers import (
    _get_from_corpus,
    _preprocess_corpus,
    _translate_relative,
    _update_datatable,
    _make_csv,
)
from buzz.buzzword.strings import (
    _make_search_name,
    _make_table_name,
    _search_error,
    _table_error,
    _downloadable_name,
)
from buzz.buzzword.tabs import _make_tabs
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import flask
from flask import send_file, Response

from buzz.buzzword.main import app, CONFIG, CORPORA, INITIAL_TABLES, CORPUS_META

###########
# STORAGE #
###########
#
SEARCHES = OrderedDict({})
TABLES = OrderedDict()
# CLICKS is a hack for clear history. move eventually to hidden div
CLICKS = dict(clear=-1, table=-1)

#############
# CALLBACKS #
#############
#
@app.callback(Output("input-box", "placeholder"), [Input("search-target", "value")])
def _correct_placeholder(value):
    """
    More accurate placeholder text when doing dependencies
    """
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
    """
    Tab display callback. If the user clicked this tab, show it, otherwise hide
    """
    if tab is None:
        tab = "dataset"
    outputs = []
    for i in ["dataset", "frequencies", "chart", "concordance"]:
        if tab == i:
            outputs.append({"display": "block"})
        else:
            outputs.append({"display": "none"})
    return outputs


# one for each chart space
for i in range(1, 6):

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
        Make new chart by kind. Do it 5 times, once for each chart space
        """
        # before anything is loaded, do nothing
        if n_clicks is None:
            raise PreventUpdate
        # get correct dataset to chart
        specs, df = _get_from_corpus(table_from, None, dataset=TABLES)
        # transpose and cut down items to plot
        if transpose:
            df = df.T
        df = df.iloc[:, :top_n]
        # generate chart
        return _df_to_figure(df, chart_type)


@app.callback(
    [
        Output("conll-view", "columns"),
        Output("conll-view", "data"),
        Output("search-from", "options"),
        Output("search-from", "value"),
        Output("search-from", "disabled"),
        Output("dialog-search", "displayed"),
        Output("dialog-search", "message"),
        Output("conll-view", "row_deletable"),
        Output("loading-main", "className"),
        Output("loading-main", "fullscreen"),
    ],
    [Input("search-button", "n_clicks"), Input("clear-history", "n_clicks")],
    [
        State("search-from", "value"),
        State("skip-switch", "on"),
        State("search-target", "value"),
        State("input-box", "value"),
        State("search-from", "options"),
        State("conll-view", "columns"),
        State("conll-view", "data"),
        State("corpus-slug", "children"),
    ],
)
def _new_search(
    n_clicks,
    cleared,
    search_from,
    skip,
    col,
    search_string,
    search_from_options,
    current_cols,
    current_data,
    slug,
):
    """
    Callback when a new search is submitted

    Validate input, run the search, store data and display things
    """
    # the first callback, before anything is loaded
    if n_clicks is None:
        return (
            current_cols,
            current_data,
            search_from_options,
            search_from,
            True,
            False,
            "",
            False,
            "loading-non-main",
            False,
        )

    add_governor = CONFIG["add_governor"]

    specs, corpus = _get_from_corpus(search_from, CORPORA, SEARCHES, slug=slug)

    msg = _search_error(col, search_string)
    if msg:
        return (
            current_cols,
            current_data,
            search_from_options,
            search_from,
            False,
            True,
            msg,
            False,
            "loading-non-main",
            False,
        )

    new_value = len(SEARCHES) + 1
    this_search = [specs, col, skip, search_string]

    exists = next((i for i in SEARCHES if this_search == list(i)[:4]), False)
    if exists:
        msg = "Table already exists. Switching to that one to save memory."
        df = corpus.loc[SEARCHES[exists]]

    # if the user has done clear history
    if cleared and cleared != CLICKS["clear"]:
        # clear searches
        SEARCHES.clear()
        name = next(k for k, v in CORPUS_META.items() if v["slug"] == slug)
        SEARCHES[name] = corpus
        # todo: the line below could be slow. can we get from elsewhere?
        cols, data = _update_datatable(
            CORPORA[slug], CORPORA[slug], drop_govs=add_governor
        )
        search_from = [
            dict(value=i, label=_make_search_name(h, len(corpus)))
            for i, h in enumerate(SEARCHES)
        ]
        # set number of clicks at last moment
        CLICKS["clear"] = cleared
        return (
            cols,
            data,
            search_from,
            0,
            True,
            False,
            "",
            False,
            "loading-non-main",
            False,
        )

    found_results = True

    if not exists:
        # the expected callback. run a search and update dataset view and search history
        if col == "t":
            df = corpus.tgrep(search_string, inverse=skip)
        elif col == "d":
            try:
                df = corpus.depgrep(search_string, inverse=skip)
            except Exception as error:
                # todo: handle invalid queries properly...
                # we need to give hepful message back to user...
                print(f"DEPGREP ERROR: {type(error)}: {error}")
                # after which, either we return previous, or return none:
                df = df.iloc[:0, :0]
        else:
            method = "just" if not skip else "skip"
            df = getattr(getattr(corpus, method), col)(search_string.strip())
        # if there are no results
        if not len(df):
            found_results = False
            msg = "No results found, sorry."

    this_search = tuple(this_search + [new_value, len(df)])
    if found_results:
        SEARCHES[this_search] = df.index
        corpus = CORPORA[slug]
        current_cols, current_data = _update_datatable(
            corpus, df, drop_govs=add_governor, deletable=True
        )
    if not msg:
        name = _make_search_name(this_search, len(corpus))
        option = dict(value=new_value, label=name)
        search_from_options.append(option)
    elif exists:
        new_value = exists[-1]
    else:
        new_value = search_from
    return (
        current_cols,
        current_data,
        search_from_options,
        new_value,
        False,
        bool(msg),
        msg,
        True,
        "loading-non-main",
        False,
    )


opts = [Output(f"chart-from-{i}", "options") for i in range(1, 6)]
vals = [Output(f"chart-from-{i}", "values") for i in range(1, 6)]
stat = [State(f"chart-from-{i}", "value") for i in range(1, 6)]


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
        Output("chart-from-4", "options"),
        Output("chart-from-4", "value"),
        Output("chart-from-5", "options"),
        Output("chart-from-5", "value"),
        Output("dialog-table", "displayed"),
        Output("dialog-table", "message"),
        Output("freq-table", "row_deletable"),
        Output("download-link", "href"),
    ],
    [
        Input("table-button", "n_clicks"),
        Input("freq-table", "columns_previous"),
        Input("freq-table", "data_previous"),
    ],
    [
        State("freq-table", "columns"),
        State("freq-table", "data"),
        State("search-from", "value"),
        State("show-for-table", "value"),
        State("subcorpora-for-table", "value"),
        State("relative-for-table", "value"),
        State("sort-for-table", "value"),
        State("chart-from-1", "options"),
        State("chart-from-1", "value"),
        State("chart-from-2", "value"),
        State("chart-from-3", "value"),
        State("chart-from-4", "value"),
        State("chart-from-5", "value"),
        State("corpus-slug", "children"),
    ],
)
def _new_table(
    n_clicks,
    prev_cols,
    prev_data,
    current_cols,
    current_data,
    search_from,
    show,
    subcorpora,
    relkey,
    sort,
    table_from_options,
    nv1,
    nv2,
    nv3,
    nv4,
    nv5,
    slug,
):
    """
    Callback when a new freq table is generated. Same logic as new_search.
    """
    # do nothing if not yet loaded
    if n_clicks is None:
        raise PreventUpdate

    # because no option below can return initial table, rows can now be deleted
    row_deletable = True

    # parse options and get correct data
    specs, corpus = _get_from_corpus(search_from, CORPORA, SEARCHES, slug=slug)
    if not sort:
        sort = "total"
    relative, keyness = _translate_relative(relkey, CORPORA[slug])

    # check if there are any validation problems
    if CLICKS["table"] != n_clicks:
        updating = False
        CLICKS["table"] = n_clicks
    else:
        updating = prev_data is not None and (
            len(prev_data) != len(current_data)
            or len(prev_data[0]) != len(current_data[0])
        )
    msg = _table_error(show, subcorpora, updating)
    nv = len(TABLES) + 1
    this_table = (specs, tuple(show), subcorpora, relative, keyness, sort, nv, 0)

    # if table already made, use that one
    exists = next((i for i in TABLES if list(this_table)[:6] == list(i)[:6]), False)

    # if we are updating the table:
    if updating:
        table = TABLES[exists]
        times_updated = exists[-1] + 1
        exists = tuple(list(exists)[:-1] + [times_updated])
        this_table = exists
        table = table[[i["id"] for i in current_cols[1:]]]
        table = table.loc[[i["_" + table.index.name] for i in current_data]]
        TABLES[exists] = table
    elif exists:
        msg = "Table already exists. Switching to that one to save memory."
        table = TABLES[exists]
    # if there was a validation problem, juse use last table (?)
    elif msg:
        table = list(TABLES.values())[-1]
    else:
        # generate table
        table = corpus.table(
            show=show,
            subcorpora=subcorpora,
            relative=relative,
            keyness=keyness,
            sort=sort,
        )
        # round df if floats are used
        if relative is not False or keyness:
            table = table.round(2)

        # cannot hash a corpus, which relative may be. none will denote corpus as reference
        if isinstance(relative, pd.DataFrame):
            relative = None

        # store the search information and the result
        TABLES[this_table] = table

    # format various outputs for display.
    # nv numbers are what we update the chart-from dropdowns.
    # if successful table, update all to latest
    # if table existed, update all to that one
    # if error, keep as they are (ths is why we need many states)
    # if updating, we reuse the current data
    if updating:
        cols, data = current_cols, current_data
    else:
        max_row, max_col = CONFIG["table_size"]
        cols, data = _update_datatable(
            CORPORA[slug], table.iloc[:max_row, :max_col], conll=False
        )

    table_name = _make_table_name(this_table)

    # todo: slow to do this every time!
    csv_path = _make_csv(table, table_name)

    tfo = table_from_options
    if not msg and not updating:
        option = dict(value=nv, label=table_name)
        tfo.append(option)
        nv1, nv2, nv3, nv4, nv5 = nv, nv, nv, nv, nv
    elif exists or updating:
        nv1, nv2, nv3, nv4, nv5 = (
            exists[-1],
            exists[-1],
            exists[-1],
            exists[-1],
            exists[-1],
        )

    return (
        cols,
        data,
        tfo,
        nv1,
        tfo,
        nv2,
        tfo,
        nv3,
        tfo,
        nv4,
        tfo,
        nv5,
        bool(msg),
        msg,
        row_deletable,
        csv_path,
    )


@app.callback(
    [
        Output("conc-table", "columns"),
        Output("conc-table", "data"),
        Output("dialog-conc", "displayed"),
        Output("dialog-conc", "message"),
    ],
    [Input("update-conc", "n_clicks")],
    [
        State("show-for-conc", "value"),
        State("search-from", "value"),
        State("conc-table", "columns"),
        State("conc-table", "data"),
        State("corpus-slug", "children"),
    ],
)
def _new_conc(n_clicks, show, search_from, current_cols, current_data, slug):
    """
    Callback for concordance. We just pick what to show and where from...
    """
    if n_clicks is None:
        raise PreventUpdate

    # easy validation!
    msg = "" if show else "No choice made for match formatting."
    if not show:
        return current_cols, current_data, True, msg

    specs, corpus = _get_from_corpus(search_from, CORPORA, SEARCHES)
    conc = corpus.conc(
        show=show, metadata=["file", "s", "i", "speaker"], window=(100, 100)
    )
    max_row, max_col = CONFIG["table_size"]
    cols, data = _update_datatable(
        CORPORA[slug], conc.iloc[:max_row, :max_col], conc=True
    )
    return cols, data, bool(msg), msg


@app.server.route("/csv/<path:path>")
def serve_static(path):
    """
    Download the file at the specified path
    """
    root_dir = os.path.join(os.getcwd(), "csv")
    return flask.send_from_directory(root_dir, path)


if __name__ == "__main__":
    app.run_server(port=8050, debug=CONFIG["debug"], threaded=True)
