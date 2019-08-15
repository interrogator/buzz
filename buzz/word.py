import json
import os
from collections import OrderedDict

import dash
import dash_core_components as dcc
import dash_html_components as html
from buzz.buzzword.configure import _configure_buzzword
from buzz.buzzword.helpers import _preprocess_corpus
from buzz.buzzword.tabs import _make_tabs
from buzz.corpus import Corpus
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True
app.title = "buzzword"
server = app.server

CONFIG = _configure_buzzword(__name__)


def _get_corpus_config(local_conf, global_conf):
    """
    get some configs, from json, backup from global, or none
    """
    max_ds = global_conf.get("max_dataset_rows", None)
    max_ds = local_conf.get("max_dataset_rows", max_ds)
    drop_col = global_conf.get("drop_columns", None)
    drop_col = local_conf.get("drop_columns", drop_col)
    add_gov = global_conf.get("add_governor", None)
    add_gov = local_conf.get("add_governor", add_gov)
    return dict(max_dataset_rows=max_ds, drop_columns=drop_col, add_governor=add_gov)


def _get_corpora(corpus_meta):
    """
    Load in all available corpora and make their initial tables
    """
    corpora = dict()
    tables = dict()
    for i, (corpus_name, metadata) in enumerate(corpus_meta.items(), start=1):
        if metadata.get("disabled"):
            print("Skipping corpus because it is disabled: {}".format(corpus_name))
            continue
        corpus = Corpus(metadata["path"])
        conf = _get_corpus_config(metadata, CONFIG)
        print('Loading corpus into memory: {} ...'.format(corpus_name))
        corpus = corpus.load(add_governor=conf["add_governor"])
        corpus = _preprocess_corpus(corpus, **conf)
        initial_table = corpus.table(show="p", subcorpora="file")
        corpora[metadata["slug"]] = corpus
        tables[metadata["slug"]] = initial_table
    return corpora, tables


corpora_file = CONFIG["corpora_file"]
with open(corpora_file, "r") as fo:
    CORPUS_META = json.loads(fo.read())


CORPORA, INITIAL_TABLES = _get_corpora(CORPUS_META)


# where downloadable CSVs get stored
if not os.path.isdir("csv"):
    os.makedirs("csv")


app.layout = html.Div(
    [dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
)

LAYOUTS = dict()


def _make_explore_layout(slug, name):
    corpus = CORPORA[slug]
    searches = OrderedDict({name: corpus})
    tables = OrderedDict({"initial": INITIAL_TABLES[slug]})
    return _make_tabs(searches, tables, slug, **CONFIG)


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def _choose_correct_page(pathname):
    from buzz.buzzword import start, explore
    if pathname is None:
        raise PreventUpdate
    if pathname.startswith("/explore"):
        slug = pathname.rstrip("/").split("/")[-1]
        if slug not in CORPORA:
            pathname = "/"
        else:
            gen = (k for k, v in CORPUS_META.items() if v["slug"] == slug)
            name = next(gen, None)
            name = name or slug
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
