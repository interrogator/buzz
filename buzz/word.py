import dash
from buzz.corpus import Corpus
import json
from buzz.helpers import _preprocess_corpus
from buzz.configure import _configure_buzzword

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True

server = app.server

CORPORA = dict()

CONFIG = _configure_buzzword(__name__)


def _get_corpora():
    """
    Load in all available corpora and make their initial tables
    """
    corpora = dict()
    tables = dict()
    corpora_file = CONFIG["corpora_file"]
    with open(corpora_file, "r") as fo:
        configured = json.loads(fo.read())
    for i, (corpus_name, metadata) in enumerate(configured.items(), start=1):
        corpus = Corpus(metadata["path"]).load(add_governor=CONFIG["add_governor"])
        initial_table = corpus.table(show="p", subcorpora="file")
        corpus = _preprocess_corpus(corpus, **CONFIG)
        corpora[metadata["slug"]] = corpus
        tables[metadata["slug"]] = initial_table
    return corpora, tables


CORPORA, INITIAL_TABLES = _get_corpora()
