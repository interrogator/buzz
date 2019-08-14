import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from buzz.word import app, CORPORA, CONFIG, INITIAL_TABLES, CORPUS_META
from buzz.buzzword import start, explore
from buzz.tabs import _make_tabs
from dash.exceptions import PreventUpdate
from collections import OrderedDict

import os

# where downloadable CSVs get stored
if not os.path.isdir("csv"):
    os.makedirs("csv")


app.layout = html.Div(
    [dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
)

LAYOUTS = dict()


def _make_explore_layout(slug, name):
    corpus = CORPORA[slug]
    SEARCHES = OrderedDict({name: corpus})
    TABLES = OrderedDict({"initial": INITIAL_TABLES[slug]})
    tabs = _make_tabs(SEARCHES, TABLES, slug, **CONFIG)
    return dcc.Loading(
        type="default",
        id="loading-main",
        fullscreen=True,
        className="loading-main",
        children=tabs,
    )


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def _choose_correct_page(pathname):
    if pathname is None:
        raise PreventUpdate
    if pathname.startswith("/explore"):
        slug = pathname.rstrip("/").split("/")[-1]
        if slug not in CORPORA:
            pathname = "/"
        else:
            name = next(k for k, v in CORPUS_META.items() if v["slug"] == slug)
            if slug in LAYOUTS:
                layout = LAYOUTS[slug]
            else:
                layout = _make_explore_layout(slug, name)
                LAYOUTS[slug] = layout
            # app.title = "buzzword: {}".format(name)
            return layout
    if pathname in {"", "/", "/start"}:
        # app.title = "buzzword: home"
        return start.layout
    else:
        return "404"


if __name__ == "__main__":
    app.run_server(debug=True)
