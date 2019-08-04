from multiprocessing import Process

import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go

import dash

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

CHART_TYPES = {"line", "bar", "pie", "heatmap", "area", "stacked_bar"}


class DashSite(object):
    def __init__(self, title=None):
        self.app = dash.Dash(
            __name__,
            external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"],
        )
        self._n_chart = 0
        self.title = title or "buzz project (pass `title` argument to rename)"
        self.colors = {"background": "#ffffff", "text": "#7FDBFF"}
        self._process = None
        self._plotters = dict(
            line=self._line_chart,
            bar=self._bar_chart,
            heatmap=self._heatmap,
            area=self._area_chart,
            stacked_bar=self._bar_chart,
        )
        self.app.layout = html.Div(
            style={"backgroundColor": self.colors["background"]},
            children=[
                html.H1(
                    children=self.title,
                    style={"textAlign": "center", "color": self.colors["text"]},
                )
            ],
        )

    def _df_to_table(self, df, max_rows=10):
        header = [html.Tr([html.Th(col) for col in df.columns])]
        body = [
            html.Tr([html.Td(df.iloc[i][col]) for col in df.columns])
            for i in range(min(len(df), max_rows))
        ]
        return html.Table(header + body)

    def _make_datatable(self, df):
        self._n_chart += 1
        return dash_table.DataTable(
            id=f"table-{self._n_chart}",
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
            page_size=10,
        )

    def add(self, kind="div", data=None, **kwargs):
        if kind in CHART_TYPES:
            get_from = dcc
            chart_type = kind
            kind = "graph"
        else:
            chart_type = None
            get_from = MAPPING.get(kind.lower(), html)
        if kind.lower() == "table":
            contents = dict(children=self._df_to_table(data))
        elif kind.lower() == "datatable":
            datatable = self._make_datatable(data)
            self.app.layout.children.append(datatable)
            if self._process and self._process.is_alive():
                self.reload()
            return
        elif kind.lower() == "markdown":
            contents = dict(children=data)
        elif get_from == html:
            contents = dict(
                children=data,
                style={"textAlign": "center", "color": self.colors["text"]},
            )
        elif get_from == dcc:
            contents = self._df_to_plot(data, chart_type)
        else:
            raise ValueError(f'Do not understand component type "{kind}"')

        component = getattr(get_from, kind.title())(**contents, **kwargs)
        self.app.layout.children.append(component)
        if self._process and self._process.is_alive():
            self.reload()

    def _bar_chart(self, row_name, row):
        return dict(x=list(row.index), y=list(row), type="bar", name=row_name)

    def _line_chart(self, row_name, row):
        return go.Scatter(
            x=list(row.index), y=list(row), mode="lines+markers", name=row_name
        )

    def _area_chart(self, row_name, row):
        return go.Scatter(
            x=list(row.index),
            y=list(row),
            hoverinfo="x+y",
            mode="lines",
            stackgroup="one",
            name=row_name,
        )

    def _heatmap(self, df):
        return [go.Heatmap(z=df.T.values, x=list(df.index), y=list(df.columns))]

    def _df_to_plot(self, df, kind):
        self._n_chart += 1
        datapoints = list()
        plotter = self._plotters[kind]
        if kind == "heatmap":
            datapoints = plotter(df)
        else:
            for row_name, row in df.T.iterrows():
                datapoints.append(plotter(row_name, row))
        layout = dict(
            plot_bgcolor=self.colors["background"],
            paper_bgcolor=self.colors["background"],
            font=dict(color=self.colors["text"]),
        )
        if kind == "stacked_bar":
            layout["barmode"] = "stack"
        return dict(
            id=f"chart-{self._n_chart}", figure=dict(data=datapoints, layout=layout)
        )

    def run(self):
        def _flask_thread():
            self.app.run_server(debug=False)

        self._process = Process(target=_flask_thread)
        self._process.start()
        print("* Process running on pid: {}".format(self._process.pid))

    def kill(self):
        self._process.terminate()

    def reload(self):
        self.kill()
        self.run()

    def empty(self):
        self.app.layout.children = [self.app.layout.children[0]]
        self._n_chart = 0
        self.reload()
