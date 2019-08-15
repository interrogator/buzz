import base64
import json
import os

import dash_core_components as dcc
import dash_html_components as html
from buzz.constants import SPACY_LANGUAGES
from buzz.corpus import Corpus
from buzz.buzzword.main import app, CORPORA, INITIAL_TABLES, CORPUS_META
from buzz.buzzword.strings import _slug_from_name
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from buzz.buzzword.nav import navbar
from buzz.buzzword import style


def _make_corpus_table():
    """
    Create HTML table with links to each corpus in corpora.json
    """
    import locale

    locale.setlocale(locale.LC_ALL, "")
    corpora_file = "corpora.json"
    with open(corpora_file, "r") as fo:
        corpora = json.loads(fo.read())
    fields = ["#", "title", "date", "language", "description", "info", "tokens"]
    columns = [html.Tr([html.Th(col) for col in fields])]
    rows = list()
    for i, (corpus, metadata) in enumerate(corpora.items(), start=1):
        if metadata.get("disabled"):
            continue
        slug = metadata["slug"]
        link = "explore/{}".format(slug)
        date = metadata.get("date", "undated")
        lang = metadata.get("language", "unknown")
        tokens = "{:n}".format(metadata["len"])
        url = metadata.get("url", "none")
        row_data = [i, corpus, date, lang, metadata["desc"], url, tokens]
        row = list()
        for j, value in enumerate(row_data):
            if j == 1:
                cell = html.Td(html.A(href=link, children=value))
            elif j == 5:
                hyper = html.A(href=value, children="ⓘ", target="_blank")
                cell = html.Td(className="no-underline", children=hyper)
            else:
                cell = html.Td(children=value)
            row.append(cell)
        rows.append(html.Tr(row))
    return html.Table(columns + rows)


def _make_upload_parse_space():
    """
    Make space for uploading files, and toolbar for submit
    """

    upload = dcc.Upload(
        id="upload-data",
        children=html.Div(["Drag-and-drop or ", html.A("select files")]),
        style={
            "width": "61vw",
            "height": "60px",
            "lineHeight": "60px",
            "borderWidth": "1px",
            "borderStyle": "dashed",
            "borderRadius": "5px",
            "textAlign": "center",
            "marginBottom": "10px",
        },
        # Allow multiple files to be uploaded
        multiple=True,
    )
    corpus_name = dcc.Input(
        id="upload-corpus-name",
        type="text",
        placeholder="Enter a name for your corpus",
        style={**style.BLOCK, **{"width": "25vw"}},
    )
    lang = dcc.Dropdown(
        placeholder="Language of corpus",
        id="corpus-language",
        options=[{"value": v, "label": k} for k, v in SPACY_LANGUAGES.items()],
        style={**style.BLOCK, **{"width": "20vw"}},
    )
    upload = html.Div(children=[upload, html.Div(id="show-upload-files")])
    dialog = dcc.ConfirmDialog(id="dialog-upload", message="")
    upload_button = html.Button(
        "Upload and parse",
        id="upload-parse-button",
        style={**style.BLOCK, **{"width": "15vw"}},
    )
    explore = dcc.Link(
        "Explore",
        id="explore-uploaded",
        href="",
        style={**style.BLOCK, **{"display": "none"}},
    )
    toolbar = html.Div([corpus_name, lang, upload_button])
    return html.Div(
        id="upload-space",
        children=dcc.Loading(
            type="default", children=[dialog, upload, toolbar, explore]
        ),
    )


def _store_corpus(contents, filenames, corpus_name):
    """
    From content and filenames, build a corpus and return the path to it
    """
    extensions = set()
    if not os.path.isdir("uploads"):
        os.makedirs("uploads")
    store_at = os.path.join("uploads", corpus_name)
    os.makedirs(store_at)
    for content, filename in zip(contents, filenames):
        extensions.add(os.path.splitext(filename)[-1])
        if len(extensions) > 1:
            break
        content_type, content_string = content.split(",")
        decoded = base64.b64decode(content_string)
        outpath = os.path.join(store_at, filename)
        with open(outpath, "wb") as fo:
            fo.write(decoded)
    if not len(extensions):
        raise ValueError("No file extensions provided")
    elif len(extensions) > 1:
        raise ValueError("Multiple extensions provided: {}".format(extensions))
    is_parsed = all(i.endswith(("conll", "conllu")) for i in filenames)
    return store_at, is_parsed


@app.callback(
    [
        Output("dialog-upload", "displayed"),
        Output("dialog-upload", "message"),
        Output("explore-uploaded", "href"),
        Output("explore-uploaded", "style"),
        Output("explore-uploaded", "children"),
    ],
    [Input("upload-parse-button", "n_clicks")],
    [
        State("upload-data", "contents"),
        State("upload-data", "filename"),
        State("corpus-language", "value"),
        State("upload-corpus-name", "value"),
    ],
)
def _upload_files(n_clicks, contents, names, corpus_lang, corpus_name):
    """
    Callback when the user clicks 'upload and parse'
    """
    if n_clicks is None:
        raise PreventUpdate
    msg = ""
    try:
        path, is_parsed = _store_corpus(contents, names, corpus_name)
        corpus = Corpus(path)
        if not is_parsed:
            corpus = corpus.parse(cons_parser=None, language=corpus_lang)
    except Exception as error:
        msg = str(error)
        raise
    if not msg:
        slug = _slug_from_name(corpus_name)
        CORPORA[slug] = corpus.load()
        CORPUS_META[corpus_name] = dict(slug=slug)
        INITIAL_TABLES[slug] = CORPORA[slug].table(show="p", subcorpora="file")
    slug = _slug_from_name(corpus_name)
    href = "/explore/{}".format(slug)
    display = {"display": "block", "fontSize": 24} if not msg else {"display": "none"}
    display = {**display, **style.BLOCK}
    text = "Explore: " + corpus_name
    return bool(msg), msg, href, display, text


@app.callback(
    Output("show-upload-files", "children"),
    [Input("upload-data", "contents")],
    [State("upload-data", "filename")],
)
def show_uploaded(contents, filenames):
    """
    Display files for upload underneath the upload space
    """
    if not contents:
        raise PreventUpdate
    markdown = "* " + "\n* ".join([i for i in filenames])
    return dcc.Markdown(markdown)


header = html.H2("buzzword: a tool for analysing annotated linguistic data")

intro = html.P(
    "Here you can create and explore parsed and annotated corpora. "
    "If you want to work with your own corpus, simply upload plain text files, "
    "annotated text files, or CONLL-U files. Otherwise, you can try out the corpora below."
)
uphead = html.H3("Upload data")

demos = html.Div([html.H3("Available corpora"), _make_corpus_table()])

upload = _make_upload_parse_space()

content = html.Div([navbar, header, intro, uphead, upload, demos])
# Define layout
layout = html.Div(content, style={"marginLeft": "10px", "marginRight": "10px"})
