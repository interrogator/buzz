import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from buzz.word import app, CORPORA, CONFIG, INITIAL_TABLES
from buzz.buzzword import start, explore
from buzz.tabs import _make_tabs
from dash.exceptions import PreventUpdate
from collections import OrderedDict

import os

# where downloadable CSVs get stored
if not os.path.isdir('csv'):
    os.makedirs('csv')


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


def _make_explore_layout(slug):
    corpus = CORPORA[slug]
    SEARCHES = OrderedDict({corpus._name: corpus})
    TABLES = OrderedDict({"initial": INITIAL_TABLES[slug]})
    app.title = CONFIG["title"] or f"buzzword: {corpus._name}"
    layout = _make_tabs(SEARCHES, TABLES, slug, **CONFIG)
    return SEARCHES, TABLES, layout


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def _choose_correct_page(pathname):
    if pathname is None:
        raise PreventUpdate
    if pathname.startswith('/explore'):
        slug = pathname.rstrip('/').split('/')[-1]
        if slug not in CORPORA:
            pathname = "/"
        else:
            searches, tables, layout = _make_explore_layout(slug)
            return layout
    if pathname in {"", "/", "/start"}:
        app.name = "buzzword: home"
        return start.layout
    else:
        return '404'


if __name__ == '__main__':
    app.run_server(debug=True)
