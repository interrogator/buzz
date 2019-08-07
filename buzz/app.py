import dash
import os
from collections import OrderedDict
from buzz.corpus import Corpus
from buzz.dashview import _df_to_figure
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from app.tabs import _make_tabs
from app.cmd import _parse_cmdline_args
from app.strings import _make_search_name, _make_table_name
from app.utils import _get_from_corpus, _translate_relative, _update_datatable

# create the app itself
external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True

# store corpus and search results in here
SEARCHES = OrderedDict()
TABLES = OrderedDict()
CLICKS = dict(clear=-1)

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
        Make new chart by kind. Do it 3 times, once for each chart space
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

    # if the user has done clear history
    if cleared and cleared != CLICKS["clear"]:
        corpus = SEARCHES["corpus"]
        SEARCHES.clear()
        SEARCHES["corpus"] = corpus
        # the line below could be slow. can we get from elsewhere?
        datatable_cols, datatable_data = _update_datatable(
            SEARCHES["corpus"], SEARCHES["corpus"]
        )
        search_from = [
            dict(value=i, label=_make_search_name(h)) for i, h in enumerate(SEARCHES)
        ]
        CLICKS["clear"] = cleared
        return datatable_cols, datatable_data, search_from, 0

    # the expected callback. run a search and update dataset view and search history
    specs, corpus = _get_from_corpus(search_from, SEARCHES)
    method = "just" if not skip else "skip"
    df = getattr(getattr(corpus, method), col)(search_string.strip())
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
    # do nothing if not yet loaded
    if n_clicks is None:
        raise PreventUpdate

    # parse options and run .table method
    specs, corpus = _get_from_corpus(search_from, SEARCHES)
    relative, keyness = _translate_relative(relkey, SEARCHES["corpus"])
    table = corpus.table(
        show=show, subcorpora=subcorpora, relative=relative, keyness=keyness, sort=sort
    )
    if relative is not False or keyness:
        table = table.round(2)
    # store the search information and the result
    nv = len(TABLES)
    this_table = (specs, tuple(show), subcorpora, relative, keyness, sort, nv)
    TABLES[this_table] = table
    # format various outputs for display
    cols, data = _update_datatable(SEARCHES["corpus"], table, conll=False)
    option = dict(value=nv, label=_make_table_name(this_table))
    tfo = table_from_options + [option]
    return cols, data, tfo, nv, tfo, nv, tfo, nv


@app.callback(
    [Output("conc-table", "columns"), Output("conc-table", "data")],
    [Input("update-conc", "n_clicks")],
    [State("show-for-conc", "value"), State("search-from", "value")],
)
def new_conc(n_clicks, show, search_from):
    if n_clicks is None:
        raise PreventUpdate
    specs, corpus = _get_from_corpus(search_from, SEARCHES)
    conc = corpus.conc(show=show, window=(80, 80))
    cols, data = _update_datatable(SEARCHES["corpus"], conc, conll=False)
    return cols, data


if __name__ == "__main__":
    # when run as script, parse the command line arguments and start the site
    kwargs = _parse_cmdline_args()
    path = kwargs["path"]
    title = kwargs["title"] or f"Explore: {os.path.basename(path)}"
    if title.endswith("-parsed"):
        title = title.rsplit("-", 1)[0]

    # create all the data we start with. loaded corpus, nouns, and noun table
    SEARCHES["corpus"] = Corpus(path).load()
    open_class = ["NOUN", "VERB", "ADJ", "ADV"]
    opens = SEARCHES["corpus"].just.x(open_class).table(show="x", subcorpora="file")
    TABLES["initial"] = opens
    app.layout = _make_tabs(title, SEARCHES, TABLES)
    app.run_server(debug=True)