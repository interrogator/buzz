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
from buzz.helpers import _get_cols, _update_datatable, _drop_cols_for_datatable
from buzz.strings import _make_search_name, _make_table_name, _capitalize_first


class Style:
    """
    Reusable CSS
    """

    VERTICAL_MARGINS = {"marginBottom": 15, "marginTop": 15}
    HORIZONTAL_PAD_5 = {"paddingLeft": 5, "paddingRight": 5}
    CELL_MIDDLE_35 = {
        "display": "table-cell",
        "verticalAlign": "middle",
        "height": "35px",
    }
    BLOCK_MIDDLE_35 = {
        "display": "inline-block",
        "verticalAlign": "middle",
        "height": "35px",
    }
    MARGIN_5_MONO = {"marginLeft": 5, "marginRight": 5, "fontFamily": "monospace"}
    BOLD_DARK = {"fontWeight": "bold", "color": "#555555"}
    STRIPES = [{"if": {"row_index": "odd"}, "backgroundColor": "rgb(248, 248, 248)"}]
    LEFT_ALIGN = [
        {"if": {"column_id": c}, "textAlign": "left", "paddingLeft": "5px"}
        for c in ["file", "w", "l", "x", "p", "f", "speaker", "setting"]
    ]
    LEFT_ALIGN_CONC = [
        {"if": {"column_id": c}, "textAlign": "left", "paddingLeft": "5px"}
        for c in ["file", "match", "right", "speaker", "setting"]
    ]
    FILE_INDEX = {
        "if": {"column_id": "file"},
        "backgroundColor": "#fafafa",
        "color": "#555555",
        "fontWeight": "bold",
    }
    INDEX = [
        {
            "if": {"column_id": c},
            "backgroundColor": "#fafafa",
            "color": "#555555",
            "fontWeight": "bold",
        }
        for c in ["file", "s", "i"]
    ]
    CONC_LMR = [
        {"if": {"column_id": "match"}, "fontWeight": "bold"},
        {
            "if": {"column_id": "left"},
            "whiteSpace": "no-wrap",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
            "width": "35%",
            "maxWidth": 0,
            "direction": "rtl",
        },
        {
            "if": {"column_id": "right"},
            "whiteSpace": "no-wrap",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
            "width": "35%",
            "maxWidth": 0,
        },
    ]


def _build_dataset_space(df, rows, add_governor):
    """
    Build the search interface and the conll display
    """
    cols = _get_cols(df, add_governor)
    cols = [dict(label="Dependencies", value="d")] + cols
    df = _drop_cols_for_datatable(df, add_governor)
    df = df.reset_index()
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
            style=Style.MARGIN_5_MONO,
        ),
        daq.BooleanSwitch(
            id="skip-switch",
            on=False,
            style={"verticalAlign": "middle", **Style.MARGIN_5_MONO},
        ),
        html.Button("Search", id="search-button"),
    ]
    pieces = [html.Div(piece, style=Style.CELL_MIDDLE_35) for piece in pieces]
    # add tooltip to boolean switch
    pieces[2].title = "Invert result"
    # pieces[0].style['position'] = "absolute";
    search_space = html.Div(
        pieces, style={"fontFamily": "bold", **Style.VERTICAL_MARGINS}
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
        style_cell=Style.HORIZONTAL_PAD_5,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        row_deletable=False,
        selected_rows=[],
        page_action="native",
        page_current=0,
        page_size=rows,
        # style_as_list_view=True,
        style_header=Style.BOLD_DARK,
        style_cell_conditional=Style.LEFT_ALIGN,
        style_data_conditional=Style.INDEX + Style.STRIPES,
    )
    return html.Div(id="dataset-container", children=[search_space, conll_table])


def _build_frequencies_space(corpus, table, rows, add_governor):
    """
    Build stuff related to the frequency table
    """
    cols = _get_cols(corpus, add_governor)
    show_check = dcc.Dropdown(
        placeholder="Features to show",
        multi=True,
        id="show-for-table",
        options=cols,
        value=[],
        style=Style.MARGIN_5_MONO,
    )
    subcorpora_drop = dcc.Dropdown(
        id="subcorpora-for-table",
        options=cols,
        placeholder="Feature for index",
        style=Style.MARGIN_5_MONO,
    )
    relative_drop = dcc.Dropdown(
        id="relative-for-table",
        style=Style.MARGIN_5_MONO,
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
        style=Style.MARGIN_5_MONO,
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
    columns, data = _update_datatable(corpus, table, conll=False, deletable=False)
    # modify the style_index used for other tables to just work for this index
    style_index = Style.FILE_INDEX
    style_index["if"]["column_id"] = table.index.name
    freq_table = dash_table.DataTable(
        id="freq-table",
        columns=columns,
        data=data,
        editable=True,
        style_cell=Style.HORIZONTAL_PAD_5,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        row_deletable=False,
        selected_rows=[],
        page_action="native",
        page_current=0,
        page_size=rows,
        style_header=Style.BOLD_DARK,
        style_cell_conditional=Style.LEFT_ALIGN,
        style_data_conditional=[style_index] + Style.STRIPES,
    )
    style = {**Style.CELL_MIDDLE_35, **{"width": "25%", "display": "inline-block"}}
    left = html.Div(
        [html.Div(show_check, style=style), html.Div(subcorpora_drop, style=style)]
    )
    right = html.Div(
        [
            html.Div(sort_drop, style=style),
            html.Div(relative_drop, style=style),
            html.Button(
                "Generate table",
                id="table-button",
                style={"width": "20%", **Style.CELL_MIDDLE_35, **Style.MARGIN_5_MONO},
            ),
        ]
    )
    toolbar = html.Div([left, right], style=Style.VERTICAL_MARGINS)
    return html.Div([toolbar, freq_table])


def _build_concordance_space(df, rows, add_governor):
    """
    Div representing the concordance tab
    """
    cols = _get_cols(df, add_governor)

    show_check = dcc.Dropdown(
        multi=True,
        placeholder="Features to show",
        id="show-for-conc",
        options=cols,
        style=Style.MARGIN_5_MONO,
    )
    update = html.Button("Update", id="update-conc", style=Style.MARGIN_5_MONO)
    style = dict(width="100%", **Style.CELL_MIDDLE_35)
    toolbar = [html.Div(i, style=style) for i in [show_check, update]]
    conc_space = html.Div(toolbar, style=Style.VERTICAL_MARGINS)
    df = df.just.x.NOUN.conc(metadata=["file", "s", "i", "speaker"], window=(100, 100))
    df = df[["left", "match", "right", "file", "s", "i", "speaker"]]
    columns = [
        {
            "name": SHORT_TO_COL_NAME.get(i, i),
            "id": i,
            "deletable": i not in ["left", "match", "right"],
        }
        for i in df.columns
    ]
    style_data = [Style.STRIPES[0], Style.INDEX[0]] + Style.CONC_LMR
    data = df.to_dict("rows")
    rule = "display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;"
    conc = dash_table.DataTable(
        id="conc-table",
        css=[{"selector": ".dash-cell div.dash-cell-value", "rule": rule}],
        columns=columns,
        data=data,
        editable=True,
        style_cell=Style.HORIZONTAL_PAD_5,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        row_deletable=True,
        selected_rows=[],
        page_action="native",
        page_current=0,
        page_size=rows,
        # style_as_list_view=True,
        style_header=Style.BOLD_DARK,
        style_cell_conditional=Style.LEFT_ALIGN_CONC,
        style_data_conditional=style_data,
    )

    return html.Div([conc_space, conc])


def _build_chart_space(tables, rows):
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
            style=Style.MARGIN_5_MONO,
        )
        types = [
            dict(label=_capitalize_first(i).replace("_", " "), value=i)
            for i in sorted(CHART_TYPES)
        ]
        chart_type = dcc.Dropdown(
            id=f"chart-type-{chart_num}",
            options=types,
            value=kind,
            style=Style.MARGIN_5_MONO,
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
            style=Style.MARGIN_5_MONO,
        )
        update = html.Button("Update", id=f"figure-button-{chart_num}")

        toolbar = [dropdown, chart_type, top_n, transpose, update]
        style = dict(display="inline-block", verticalAlign="middle")
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
            nstyle = {**style, **{"width": width}}
            div = html.Div(component, style=nstyle)
            if component == transpose:
                div.title = "Transpose axes"
            elif component == top_n:
                div.title = "Number of entries to display"
            tools.append(div)
        toolbar = html.Div(tools, style=Style.VERTICAL_MARGINS)
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
                        **Style.BOLD_DARK,
                    },
                ),
                html.Div(chart_space),
            ],
            open=chart_num == 1,
            # style={"borderStyle": "groove"}
        )
        charts.append(collapse)
    return html.Div(charts)


def _make_tabs(searches, tables, title=None, page_size=25, **kwargs):
    """
    Generate initial layout div
    """
    add_gov = kwargs["add_governor"]
    corpus = next(iter(searches.values()))
    dataset = _build_dataset_space(corpus, page_size, add_gov)
    frequencies = _build_frequencies_space(
        corpus, tables["initial"], page_size, add_gov
    )
    chart = _build_chart_space(tables, page_size)
    concordance = _build_concordance_space(corpus, page_size, add_gov)

    search_from = [
        dict(value=i, label=_make_search_name(h, len(corpus)))
        for i, h in enumerate(searches)
    ]
    clear = html.Button("Clear history", id="clear-history", style=Style.MARGIN_5_MONO)
    dropdown = dcc.Dropdown(
        id="search-from", options=search_from, value=0, disabled=True
    )

    pad_block = {**Style.HORIZONTAL_PAD_5, **Style.BLOCK_MIDDLE_35}
    drop_style = {
        "fontFamily": "monospace",
        "width": "60%",
        **Style.HORIZONTAL_PAD_5,
        **Style.BLOCK_MIDDLE_35,
    }

    top_bit = [
        html.Img(
            src="assets/bolt.jpg", height=42, width=38, style=Style.BLOCK_MIDDLE_35
        ),
        html.H3(children="buzzword", style={"paddingBottom": "5px", **pad_block}),
        # these spaces are used to flash messages to the user if something is wrong
        dcc.ConfirmDialog(id="dialog-search", message=""),
        dcc.ConfirmDialog(id="dialog-table", message=""),
        dcc.ConfirmDialog(id="dialog-chart", message=""),
        dcc.ConfirmDialog(id="dialog-conc", message=""),
        html.Div(dropdown, style=drop_style),
        html.Div(clear, style=dict(width="10%", **Style.BLOCK_MIDDLE_35)),
    ]
    top_bit = html.Div(top_bit, style=Style.VERTICAL_MARGINS)

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
        dcc.Loading(
            type="default",
            id="loading-main",
            fullscreen=True,
            className="loading-main",
            children=[
                html.Div(
                    id="tab-dataset",
                    style={"display": "none"},
                    children=[html.Div(id="display-dataset", children=[dataset])],
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
            ],
        )
    ]
    tab_contents = html.Div(id="tab-contents", children=tab_contents)

    return html.Div(id="everything", children=[top_bit, tab_headers, tab_contents])
