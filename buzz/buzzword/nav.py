import dash_core_components as dcc
import dash_html_components as html
from buzz.buzzword import style

navbar = html.Div(
    [
        html.Img(
            src="../assets/bolt.jpg", height=42, width=38, style=style.BLOCK_MIDDLE_35
        ),
        dcc.Link("buzzword", href="/", style=style.NAV_HEADER),
        html.Div(
            html.Ul(
                [
                    html.Li([dcc.Link("User guide", href="/guide")]),
                    html.Li([dcc.Link("About", href="/about")]),
                ],
                className="nav navbar-nav",
            ),
            className="pull-right",
        ),
    ],
    className="navbar navbar-default navbar-static-top",
)
