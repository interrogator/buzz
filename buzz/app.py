from collections import OrderedDict

import pandas as pd

import dash
from buzz.cmdline import _parse_cmdline_args
from buzz.strings import _make_search_name, _make_table_name, _search_error, _table_error
from buzz.tabs import _make_tabs
from buzz.helpers import (
    _get_from_corpus,
    _translate_relative,
    _update_datatable,
    _preprocess_corpus,
)
from buzz.corpus import Corpus
from buzz.dashview import _df_to_figure
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

#######################
# MAKE FLASK/DASH APP #
#######################
#
external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True
server = app.server

###########
# STORAGE #
###########
#
SEARCHES = OrderedDict()
TABLES = OrderedDict()
CLICKS = dict(clear=-1)


def _corpus():
    """Get the corpus data, whatever its name may be"""
    return next(iter(SEARCHES.values()))


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
        Make new chart by kind. Do it 3 times, once for each chart space
        """
        # before anything is loaded, do nothing
        if n_clicks is None:
            raise PreventUpdate
        # get correct dataset to chart
        specs, df = _get_from_corpus(table_from, dataset=TABLES)
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
    ],
    [Input("search-button", "n_clicks"), Input("clear-history", "n_clicks")],
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
    # the first callback, before anything is loaded
    if n_clicks is None:
        raise PreventUpdate

    specs, corpus = _get_from_corpus(search_from, SEARCHES)

    msg = _search_error(col, search_string)
    if msg:
        cols, data = _update_datatable(_corpus(), _corpus())
        return cols, data, search_from_options, search_from, False, True, msg

    new_value = len(SEARCHES)
    this_search = (specs, col, skip, search_string, new_value)

    exists = next((i for i in SEARCHES if list(this_search)[:4] == list(i)[:4]), False)
    if exists:
        msg = "Table already exists. Switching to that one to save memory."
        df = corpus.loc[SEARCHES[exists]]

    # if the user has done clear history
    if cleared and cleared != CLICKS["clear"]:
        # clear searches
        SEARCHES.clear()
        SEARCHES[corpus._name] = corpus
        # todo: the line below could be slow. can we get from elsewhere?
        cols, data = _update_datatable(_corpus(), _corpus())
        search_from = [
            dict(value=i, label=_make_search_name(h)) for i, h in enumerate(SEARCHES)
        ]
        # set number of clicks at last moment
        CLICKS["clear"] = cleared
        return cols, data, search_from, 0, True, False, ""

    if not exists:
        # the expected callback. run a search and update dataset view and search history
        if col == "t":
            df = corpus.tgrep(search_string, inverse=skip)
        elif col == "d":
            df = corpus.depgrep(search_string, inverse=skip)
        else:
            method = "just" if not skip else "skip"
            df = getattr(getattr(corpus, method), col)(search_string.strip())

    SEARCHES[this_search] = df.index
    datatable_cols, datatable_data = _update_datatable(_corpus(), df)
    if not msg:
        option = dict(value=new_value, label=_make_search_name(this_search))
        search_from_options.append(option)
    elif exists:
        new_value = exists[-1]
    else:
        new_value = search_from
    return (
        datatable_cols,
        datatable_data,
        search_from_options,
        new_value,
        False,
        bool(msg),
        msg,
    )


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
    ],
    [Input("table-button", "n_clicks")],
    [
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
    ],
)
def _new_table(
    n_clicks,
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
):
    """
    Callback when a new freq table is generated
    """
    # do nothing if not yet loaded
    if n_clicks is None:
        raise PreventUpdate

    # parse options and get correct data
    specs, corpus = _get_from_corpus(search_from, SEARCHES)
    if not sort:
        sort = "total"
    relative, keyness = _translate_relative(relkey, _corpus())

    # check if there are any validation problems
    msg = _table_error(show, subcorpora)
    nv = len(TABLES)
    this_table = (specs, tuple(show), subcorpora, relative, keyness, sort, nv)

    # if table already made, use that one
    exists = next((i for i in TABLES if list(this_table)[:6] == list(i)[:6]), False)
    if exists:
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
    # if error, keep as they are
    cols, data = _update_datatable(_corpus(), table.iloc[:MAX_ROWS, :MAX_COLUMNS], conll=False)
    tfo = table_from_options
    if not msg:
        option = dict(value=nv, label=_make_table_name(this_table))
        tfo.append(option)
        nv1, nv2, nv3, nv4, nv5 = nv, nv, nv, nv, nv
    elif exists:
        nv1, nv2, nv3, nv4, nv5 = (
            exists[-1],
            exists[-1],
            exists[-1],
            exists[-1],
            exists[-1],
        )

    return cols, data, tfo, nv1, tfo, nv2, tfo, nv3, tfo, nv4, tfo, nv5, bool(msg), msg


@app.callback(
    [Output("conc-table", "columns"), Output("conc-table", "data")],
    [Input("update-conc", "n_clicks")],
    [State("show-for-conc", "value"), State("search-from", "value")],
)
def new_conc(n_clicks, show, search_from):
    """
    Callback for conc. We just pick what to show and where from...
    """
    if n_clicks is None:
        raise PreventUpdate
    specs, corpus = _get_from_corpus(search_from, SEARCHES)
    conc = corpus.conc(show=show, window=(100, 100))
    cols, data = _update_datatable(_corpus(), conc.iloc[:MAX_ROWS, :MAX_COLUMNS], conll=False)
    return cols, data


if __name__ == "__main__":
    # when run as script, parse the command line arguments and start the site
    kwargs = _parse_cmdline_args()
    MAX_ROWS, MAX_COLUMNS = kwargs["table_size"]
    # create all the data we start with. loaded corpus, nouns, and noun table
    # note that we have to suppress callback warnings, because we don't make tabs
    # until after callbacks are defined. the reason for this is, we need to pass
    # initial data to the tabs, which we can't generate without knowing the path
    corpus = Corpus(kwargs["path"]).load()
    corpus = _preprocess_corpus(corpus, **kwargs)
    SEARCHES[corpus._name] = corpus
    open_class = ["NOUN", "VERB", "ADJ", "ADV"]
    opens = _corpus().just.x(open_class).table(show="p", subcorpora="file")
    TABLES["initial"] = opens
    app.title = f"buzzword: {corpus._name}"
    app.layout = _make_tabs(SEARCHES, TABLES, **kwargs)
    if kwargs["debug"]:
        app.run_server(debug=True)
    else:
        app.run(host='0.0.0.0', port=5000, debug=False)
