# flake8: noqa

from multiprocessing import Process

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objects as go

MAPPING = {
    "markdown": dcc,
    "h1": html,
    "h2": html,
    "h3": html,
    "h4": html,
    "div": html,
    "graph": dcc,
    "table": html,
}


CHART_TYPES = {"line", "bar", "heatmap", "area", "stacked_bar"}  # "pie"


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


def _bar_chart(row_name, row):
    return dict(x=list(row.index), y=list(row), type="bar", name=row_name)


def _line_chart(row_name, row):
    return go.Scatter(
        x=list(row.index), y=list(row), mode="lines+markers", name=row_name
    )


def _area_chart(row_name, row):
    return go.Scatter(
        x=list(row.index),
        y=list(row),
        hoverinfo="x+y",
        mode="lines",
        stackgroup="one",
        name=row_name,
    )


def _heatmap(df):
    return [go.Heatmap(z=df.T.values, x=list(df.index), y=list(df.columns))]


PLOTTERS = dict(
    line=_line_chart,
    bar=_bar_chart,
    heatmap=_heatmap,
    area=_area_chart,
    stacked_bar=_bar_chart,
)


def _df_to_plot(df, kind, idx):
    """
    todo: delete this?
    """
    datapoints = list()
    plotter = PLOTTERS[kind]
    if kind == "heatmap":
        datapoints = plotter(df)
    else:
        for row_name, row in df.T.iterrows():
            datapoints.append(plotter(row_name, row))
    layout = dict()
    if kind == "stacked_bar":
        layout["barmode"] = "stack"
    return dict(id=idx, figure=dict(data=datapoints, layout=layout))


def _df_to_figure(df, kind="bar"):
    """
    Helper to generate charts
    """
    datapoints = list()
    plotter = PLOTTERS[kind]
    if kind == "heatmap":
        datapoints = plotter(df)
    else:
        for row_name, row in df.T.iterrows():
            datapoints.append(plotter(row_name, row))
    layout = dict(width=1300)
    if kind == "stacked_bar":
        layout["barmode"] = "stack"
    return dict(data=datapoints, layout=layout)


def _make_component(kind="div", data=None, idx=None, **kwargs):
    if kind in CHART_TYPES:
        get_from = dcc
        chart_type = kind
        kind = "graph"
    else:
        chart_type = None
        get_from = MAPPING.get(kind.lower(), html)
    if kind.lower() == "datatable":
        datatable = _make_datatable(data, idx)
        return datatable
    elif kind.lower() == "markdown":
        contents = dict(children=data)
    elif get_from == html:
        contents = dict(
            children=data,
            # style={"textAlign": "center"},
        )
    elif get_from == dcc:
        contents = _df_to_plot(data, chart_type, id)
    else:
        raise ValueError(f'Do not understand component type "{kind}"')

    return getattr(get_from, kind.title())(**contents, **kwargs)


class DashSite(object):
    def __init__(self, title=None):
        self.app = dash.Dash(
            __name__,
            external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"],
        )
        self.title = title or "buzz project (pass `title` argument to rename)"
        self.colors = {"background": "#ffffff", "text": "#7FDBFF"}
        self._process = None
        self.app.layout = html.Div(
            style={"backgroundColor": self.colors["background"]},
            children=[
                html.H1(
                    children=self.title,
                    style={"textAlign": "center", "color": self.colors["text"]},
                )
            ],
        )

    def add(self, kind="div", data=None, idx=None, **kwargs):
        if not idx:
            idx = "el-" + str(id(data))
        comp = _make_component(kind, data, idx, **kwargs)
        self.app.layout.children.append(comp)
        if self._process and self._process.is_alive():
            self.reload()

    def run(self):
        def _flask_thread():
            self.app.run_server(debug=False)

        self._process = Process(target=_flask_thread)
        self._process.start()
        print("* Process running on pid: {}".format(self._process.pid))

    def kill(self):
        if self._process is not None:
            self._process.terminate()

    def reload(self):
        self.kill()
        self.run()

    def remove(self, idx):
        if isinstance(idx, int):
            idx = str(idx)
        elif not isinstance(idx, str):
            idx = str(id(idx))
        if not idx.startswith("el-"):
            idx = "el-" + idx
        self.app.layout.children = [
            i
            for i in self.app.layout.children
            if str(getattr(i, "id", None)) != str(idx)
        ]
        self.reload()

    def empty(self):
        self.app.layout.children = [self.app.layout.children[0]]
        self.reload()
