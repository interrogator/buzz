import argparse
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import plotly.graph_objects as go
import os
import sys

from buzz.corpus import Corpus
from buzz.dashview import DashSite

LABELS = dict(
    w="Word",
    l="Lemma",
    g="Governor index",
    f="Dependency role",
    x="Wordclass",
    i="Token index",
    s="Sentence number",
    file="Filename",
    speaker="Speaker",
)


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
    def __init__(self, path, title=None, load=True):
        self.initialising = True
        self.path = path
        # Corpus(os.path.expanduser(path))
        self.title = title or f"Explore: {os.path.basename(path)}"
        # if load:
        #    self.corpus = self.corpus.load()
        self._search_history = list()
        self.site = DashSite("a title")
        self.app = self.site.app
        self.corpus = Corpus(self.path).load()
        self._build_layout()
        self.initialising = False

    def _build_search_space(self):
        self.site.add("markdown", "## Search space\n\nCreate a new search here")
        cols = ["file", "s", "i"] + list(self.corpus.columns)
        cols = [dict(label=LABELS.get(i, i.title()), value=i) for i in cols]
        cols += [dict(label="Dependencies", value="d"), dict(label="Trees", value="t")]
        dropdown = dcc.Dropdown(id="colselect", options=cols, value="w")
        search_space = html.Div(
            [
                html.Div(dropdown),
                html.Div(dcc.Input(id="input-box", type="text")),
                html.Button("Submit", id="button"),
                daq.BooleanSwitch(id="skip-switch", on=False),
                html.Div(
                    id="output-container-button",
                    children="Enter a value and press submit",
                ),
            ]
        )
        print('ADDING THINGS TO SITE')
        self.app.layout.children.append(search_space)

    def _build_table_space(self, data):
        self.site.add("markdown", "## Table space")
        cols = ["file", "s", "i"] + list(self.corpus.columns)
        cols = [dict(label=LABELS.get(i, i.title()), value=i) for i in cols]
        show_check = dcc.Checklist(id="show-for-table", options=cols, value=["l", "x"])
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
        table_space = html.Div(
            [
                html.Div(show_check),
                html.Div(subcorpora_drop),
                html.Div(sort_drop),
                html.Div(relative_drop),
                html.Button("Update", id="update-button"),
                html.Div(id="table-generate-outer", children="Generate a new table"),
            ]
        )
        self.app.layout.children.append(table_space)
        self.site.add("datatable", data, id="freq-table")

    def _build_layout(self):
        self._build_search_space()
        self.site.add("datatable", self.corpus, id="conll-view")
        nouns = self.corpus.just.x.NOUN
        tab = nouns.table(subcorpora="file", show="l", relative=True)
        self.site.add("bar", tab.square(20), id="main-chart")
        self.site.add("markdown", "## Concordancing")
        self.site.add("datatable", nouns.conc().head(100), id="conctable")
        self._build_table_space(tab.square(20))


def _make_datatable(df, id):
    df = df.drop("parse", axis=1, errors="ignore")
    return dash_table.DataTable(
        id=id,
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict("rows"),
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


def _line_chart(row_name, row):
    return go.Scatter(
        x=list(row.index), y=list(row), mode="lines+markers", name=row_name
    )


def _bar_chart(row_name, row):
    return dict(x=list(row.index), y=list(row), type="bar", name=row_name)


def _df_to_figure(df):
    datapoints = list()
    for row_name, row in df.T.iterrows():
        datapoints.append(_bar_chart(row_name, row))
    layout = dict(
        # plot_bgcolor=self.colors["background"],
        # paper_bgcolor=self.colors["background"],
        # font=dict(color=self.colors["text"]),
    )
    return dict(data=datapoints, layout=layout)


def main(path, **kwargs):
    print('MAKING SITE')
    site = Site(path=path)
    app = site.app
    corpus = site.corpus

    def _translate_relative(inp):
        mapping = dict(t=True, f=False, n=corpus, l="ll", p="pd")
        assert len(inp) == 1
        return mapping[inp[0]], mapping[inp[1]]

        @app.callback(
            [
                dash.dependencies.Output("conll-view", "figure"),
                # todo: search from...
                # dash.dependencies.Output('search-from', 'children')
            ],
            [
                dash.dependencies.Input("colselect", "value"),
                dash.dependencies.Input("skip-switch", "on"),
            ],
            [dash.dependencies.State("input-box", "value")],
        )
        def new_search(col, skip, search_string):
            print("NEW SEARCH CALLBACK", col, skip, search_string)
            # seems to callback on load, don't know why
            # this is therefore what is shown initially
            if search_string is None:
                return _df_to_figure(data)
            method = "just" if not skip else "skip"
            df = getattr(getattr(DATA, method), col)(search_string.strip())
            this_search = (col, skip, search_string, df.index)
            SITE._search_history.append(this_search)
            df = df.table(show="l", subcorpora="file").square(20)
            return _df_to_figure(df)

    @app.callback(
        [
            dash.dependencies.Output("main-chart", "figure"),
            dash.dependencies.Output("freq-table", "figure"),
        ],
        [
            dash.dependencies.Input("show-for-table", "value"),
            dash.dependencies.Input("subcorpora-for-table", "value"),
            dash.dependencies.Input("relative-for-table", "value"),
            dash.dependencies.Input("sort-for-table", "value"),
        ],
    )
    def new_table(show, subcorpora, relkey, sort):
        print("NEW TABLE CALLBACK", show, subcorpora, relkey, sort)
        if True:
            tab = CORPUS.just.x.NOUN.table(subcorpora="file", show="l", relative=True)
            return (_df_to_figure(tab), _make_datatable(CORPUS.head(100), "freq-table"))
        relative, keyness = translate_relative(relkey)
        if relative is None:
            relative = CORPUS
        to_search = CORPUS  # if not search_from else search_from...
        table = to_search.table(
            show=show,
            subcorpora=subcorpora,
            relative=relative,
            keyness=keyness,
            sort=sort,
        )
        return (_df_to_figure(table), _make_datatable(df, "freq-table"))

    app.run_server(debug=True)

if __name__ == "__main__":
    main(**_parse_cmdline_args())

