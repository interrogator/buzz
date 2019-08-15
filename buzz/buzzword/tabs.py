# flake8: noqa

"""
buzz webapp: everything needed to populate app tabs initially
"""

import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
import dash_table

from buzz.constants import SHORT_TO_COL_NAME
from buzz.dashview import CHART_TYPES, _df_to_figure
from buzz.buzzword.helpers import _get_cols, _update_datatable, _drop_cols_for_datatable
from buzz.buzzword.strings import _make_search_name, _make_table_name, _capitalize_first
from buzz.buzzword import style


def _build_dataset_space(df, rows, **kwargs):
    """
    Build the search interface and the conll display
    """
    cols = _get_cols(df, kwargs["add_governor"])
    cols = [dict(label="Dependencies", value="d")] + cols
    df = _drop_cols_for_datatable(df, kwargs["add_governor"])
    df = df.reset_index()
    max_row, max_col = kwargs["table_size"]
    df = df.iloc[:max_row, :max_col]
    pieces = [
        dcc.Dropdown(
            id="search-target",
            options=cols,
            value="w",
            # title="Select the column you wish to search (e.g. word/lemma/POS) "
            # + ", or query language (e.g. Tgrep2, Depgrep)",
            style={"width": "200px", "fontFamily": "monospace"},
        ),
        dcc.Input(
            id="input-box",
            type="text",
            placeholder="Enter regular expression search query...",
            size="120",
            style=style.MARGIN_5_MONO,
        ),
        daq.BooleanSwitch(
            id="skip-switch",
            on=False,
            style={"verticalAlign": "middle", **style.MARGIN_5_MONO},
        ),
        html.Button("Search", id="search-button"),
    ]
    pieces = [html.Div(piece, style=style.CELL_MIDDLE_35) for piece in pieces]
    # add tooltip to boolean switch
    pieces[2].title = "Invert result"
    # pieces[0].style['position'] = "absolute";
    search_space = html.Div(
        pieces, style={"fontFamily": "bold", **style.VERTICAL_MARGINS}
    )
    columns = [
        {
            "name": _capitalize_first(SHORT_TO_COL_NAME.get(i, i)).replace("_", " "),
            "id": i,
            "deletable": False,
        }
        for i in df.columns
    ]
    data = df.to_dict("rows")

    conll_table = dash_table.DataTable(
        id="conll-view",
        columns=columns,
        data=data,
        editable=True,
        style_cell=style.HORIZONTAL_PAD_5,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        row_deletable=False,
        selected_rows=[],
        page_action="native",
        page_current=0,
        page_size=rows,
        # style_as_list_view=True,
        style_header=style.BOLD_DARK,
        style_cell_conditional=style.LEFT_ALIGN,
        style_data_conditional=style.INDEX + style.STRIPES,
    )
    return html.Div(id="dataset-container", children=[search_space, conll_table])


def _build_frequencies_space(corpus, table, rows, **kwargs):
    """
    Build stuff related to the frequency table
    """
    cols = _get_cols(corpus, kwargs["add_governor"])
    show_check = dcc.Dropdown(
        placeholder="Features to show",
        multi=True,
        id="show-for-table",
        options=cols,
        value=[],
        style=style.MARGIN_5_MONO,
    )
    subcorpora_drop = dcc.Dropdown(
        id="subcorpora-for-table",
        options=cols,
        placeholder="Feature for index",
        style=style.MARGIN_5_MONO,
    )
    relative_drop = dcc.Dropdown(
        id="relative-for-table",
        style=style.MARGIN_5_MONO,
        options=[
            {"label": "Absolute frequency", "value": "ff"},
            {"label": "Relative of result", "value": "tf"},
            {"label": "Relative of corpus", "value": "nf"},
            {"label": "Keyness: log likelihood", "value": "fl"},
            {"label": "Keyness: percent difference", "value": "fp"},
        ],
        placeholder="Relative/keyness calculation",
    )
    sort_drop = dcc.Dropdown(
        id="sort-for-table",
        style=style.MARGIN_5_MONO,
        options=[
            {"label": "Total", "value": "total"},
            {"label": "Infrequent", "value": "infreq"},
            {"label": "Alphabetical", "value": "name"},
            {"label": "Increasing", "value": "increase"},
            {"label": "Decreasing", "value": "decrease"},
            {"label": "Static", "value": "static"},
            {"label": "Turbulent", "value": "turbulent"},
        ],
        placeholder="Sort columns by...",
    )
    max_row, max_col = kwargs["table_size"]
    table = table.iloc[:max_row, :max_col]
    columns, data = _update_datatable(corpus, table, conll=False, deletable=False)

    # modify the style_index used for other tables to just work for this index
    style_index = style.FILE_INDEX
    style_index["if"]["column_id"] = table.index.name
    freq_table = dcc.Loading(
        type="default",
        children=[
            dash_table.DataTable(
                id="freq-table",
                columns=columns,
                data=data,
                editable=True,
                style_cell=style.HORIZONTAL_PAD_5,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                row_deletable=False,
                selected_rows=[],
                page_action="native",
                page_current=0,
                page_size=rows,
                style_header=style.BOLD_DARK,
                style_cell_conditional=style.LEFT_ALIGN,
                style_data_conditional=[style_index] + style.STRIPES,
            ),
            html.A(
                "Download",
                id="download-link",
                # download="freq-table.csv",
                href="",
                target="_blank",
            ),
        ],
    )
    tstyle = {**style.CELL_MIDDLE_35, **{"width": "25%", "display": "inline-block"}}
    left = html.Div(
        [html.Div(show_check, style=tstyle), html.Div(subcorpora_drop, style=tstyle)]
    )
    right = html.Div(
        [
            html.Div(sort_drop, style=tstyle),
            html.Div(relative_drop, style=tstyle),
            html.Button(
                "Generate table",
                id="table-button",
                style={"width": "20%", **style.CELL_MIDDLE_35, **style.MARGIN_5_MONO},
            ),
        ]
    )
    toolbar = html.Div([left, right], style=style.VERTICAL_MARGINS)
    return html.Div([toolbar, freq_table])


def _build_concordance_space(df, rows, **kwargs):
    """
    Div representing the concordance tab
    """
    cols = _get_cols(df, kwargs["add_governor"])

    show_check = dcc.Dropdown(
        multi=True,
        placeholder="Features to show",
        id="show-for-conc",
        options=cols,
        style=style.MARGIN_5_MONO,
    )
    update = html.Button("Update", id="update-conc", style=style.MARGIN_5_MONO)
    tstyle = dict(width="100%", **style.CELL_MIDDLE_35)
    toolbar = [html.Div(i, style=tstyle) for i in [show_check, update]]
    conc_space = html.Div(toolbar, style=style.VERTICAL_MARGINS)

    max_row, max_col = kwargs["table_size"]
    df = df.iloc[:max_row, :max_col]

    meta = ["file", "s", "i"]
    if "speaker" in df.columns:
        meta.append("speaker")

    df = df.just.x.NOUN.conc(metadata=meta, window=(100, 100))

    just = ["left", "match", "right", "file", "s", "i"]
    if "speaker" in df.columns:
        just.append("speaker")
    df = df[just]
    columns = [
        {
            "name": SHORT_TO_COL_NAME.get(i, i),
            "id": i,
            "deletable": i not in ["left", "match", "right"],
        }
        for i in df.columns
    ]
    style_data = [style.STRIPES[0], style.INDEX[0]] + style.CONC_LMR
    data = df.to_dict("rows")
    rule = "display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;"
    conc = dcc.Loading(
        type="default",
        children=[
            dash_table.DataTable(
                id="conc-table",
                css=[{"selector": ".dash-cell div.dash-cell-value", "rule": rule}],
                columns=columns,
                data=data,
                editable=True,
                style_cell=style.HORIZONTAL_PAD_5,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                row_deletable=True,
                selected_rows=[],
                page_action="native",
                page_current=0,
                page_size=rows,
                # style_as_list_view=True,
                style_header=style.BOLD_DARK,
                style_cell_conditional=style.LEFT_ALIGN_CONC,
                style_data_conditional=style_data,
            )
        ],
    )

    return html.Div([conc_space, conc])


def _build_chart_space(tables, rows, **kwargs):
    """
    Div representing the chart tab
    """
    charts = []
    for chart_num, kind in [
        (1, "stacked_bar"),
        (2, "line"),
        (3, "area"),
        (4, "heatmap"),
        (5, "bar"),
    ]:

        table_from = [
            dict(value=i, label=_make_table_name(h)) for i, h in enumerate(tables)
        ]
        dropdown = dcc.Dropdown(
            id=f"chart-from-{chart_num}",
            options=table_from,
            value=0,
            style=style.MARGIN_5_MONO,
        )
        types = [
            dict(label=_capitalize_first(i).replace("_", " "), value=i)
            for i in sorted(CHART_TYPES)
        ]
        chart_type = dcc.Dropdown(
            id=f"chart-type-{chart_num}",
            options=types,
            value=kind,
            style=style.MARGIN_5_MONO,
        )
        transpose = (
            daq.BooleanSwitch(
                id=f"chart-transpose-{chart_num}",
                on=False,
                style={"verticalAlign": "middle"},
            ),
        )
        top_n = dcc.Input(
            id=f"chart-top-n-{chart_num}",
            placeholder="Results to plot",
            type="number",
            min=1,
            max=99,
            value=7,
            style=style.MARGIN_5_MONO,
        )
        update = html.Button("Update", id=f"figure-button-{chart_num}")

        toolbar = [dropdown, chart_type, top_n, transpose, update]
        tstyle = dict(display="inline-block", verticalAlign="middle")
        widths = {
            dropdown: "50%",
            chart_type: "25%",
            top_n: "10%",
            transpose: "5%",
            update: "10%",
        }
        tools = list()
        for component in toolbar:
            width = widths.get(component, "10%")
            nstyle = {**tstyle, **{"width": width}}
            div = html.Div(component, style=nstyle)
            if component == transpose:
                div.title = "Transpose axes"
            elif component == top_n:
                div.title = "Number of entries to display"
            tools.append(div)
        toolbar = html.Div(tools, style=style.VERTICAL_MARGINS)
        df = tables["initial"]
        figure = _df_to_figure(df, kind=kind)
        chart_data = dict(
            id=f"chart-{chart_num}",
            figure=figure,
            style={"height": "60vh", "width": "95vw"},
        )
        chart = dcc.Graph(**chart_data)
        chart_space = html.Div([toolbar, chart])
        collapse = html.Details(
            [
                html.Summary(
                    f"Chart #{chart_num}",
                    style={
                        "fontWeight": "bold",
                        "fontSize": "11pt",
                        "paddingBottom": "10px",
                        "paddingTop": "10px",
                        **style.BOLD_DARK,
                    },
                ),
                html.Div(chart_space),
            ],
            open=chart_num == 1,
            # style={"borderStyle": "groove"}
        )
        charts.append(collapse)
    return html.Div(charts)


def _make_tabs(searches, tables, corpus_slug, title=None, page_size=25, **kwargs):
    """
    Generate initial layout div
    """
    corpus = next(iter(searches.values()))
    dataset = _build_dataset_space(corpus, page_size, **kwargs)
    frequencies = _build_frequencies_space(
        corpus, tables["initial"], page_size, **kwargs
    )
    chart = _build_chart_space(tables, page_size, **kwargs)
    concordance = _build_concordance_space(corpus, page_size, **kwargs)

    search_from = [
        dict(value=i, label=_make_search_name(h, len(corpus)))
        for i, h in enumerate(searches)
    ]
    clear = html.Button("Clear history", id="clear-history", style=style.MARGIN_5_MONO)
    dropdown = dcc.Dropdown(
        id="search-from", options=search_from, value=0, disabled=True
    )

    pad_block = {**style.HORIZONTAL_PAD_5, **style.BLOCK_MIDDLE_35}
    drop_style = {
        "fontFamily": "monospace",
        "width": "60%",
        **style.HORIZONTAL_PAD_5,
        **style.BLOCK_MIDDLE_35,
    }

    top_bit = [
        html.Img(
            src="../assets/bolt.jpg", height=42, width=38, style=style.BLOCK_MIDDLE_35
        ),
        dcc.Link("buzzword", href="/", style=style.NAV_HEADER),
        # these spaces are used to flash messages to the user if something is wrong
        dcc.ConfirmDialog(id="dialog-search", message=""),
        dcc.ConfirmDialog(id="dialog-table", message=""),
        dcc.ConfirmDialog(id="dialog-chart", message=""),
        dcc.ConfirmDialog(id="dialog-conc", message=""),
        html.Div(dropdown, style=drop_style),
        html.Div(clear, style=dict(width="10%", **style.BLOCK_MIDDLE_35)),
    ]
    top_bit = html.Div(top_bit, style=style.VERTICAL_MARGINS)

    tab_headers = dcc.Tabs(
        id="tabs",
        value="dataset",
        style={
            "lineHeight": 0,
            "fontFamily": "monospace",
            "font": "12px Arial",
            "fontWeight": 600,
            "color": "#555555",
        },
        children=[
            dcc.Tab(label="DATASET", value="dataset"),
            dcc.Tab(label="FREQUENCIES", value="frequencies"),
            dcc.Tab(label="CHART", value="chart"),
            dcc.Tab(label="CONCORDANCE", value="concordance"),
        ],
    )

    tab_contents = [
        html.Div(
            children=[
                dcc.Loading(
                    type="default",
                    id="loading-main",
                    fullscreen=True,
                    className="loading-main",
                    children=[
                        html.Div(
                            id="tab-dataset",
                            style={"display": "block"},
                            children=[
                                html.Div(id="display-dataset", children=[dataset])
                            ],
                        )
                    ],
                ),
                html.Div(
                    id="tab-frequencies",
                    style={"display": "none"},
                    children=[
                        html.Div(id="display-frequencies", children=[frequencies])
                    ],
                ),
                html.Div(
                    id="tab-chart",
                    style={"display": "none"},
                    children=[html.Div(id="display-chart", children=[chart])],
                ),
                html.Div(
                    id="tab-concordance",
                    style={"display": "none"},
                    children=[
                        html.Div(id="display-concordance", children=[concordance])
                    ],
                ),
            ]
        )
    ]
    tab_contents = html.Div(id="tab-contents", children=tab_contents)

    hidden_corpus_name = html.Div(
        id="corpus-slug", children=corpus_slug, style={"display": "none"}
    )
    return html.Div(
        id="everything",
        children=[top_bit, tab_headers, tab_contents, hidden_corpus_name],
    )
