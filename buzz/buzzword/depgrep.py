import dash_core_components as dcc
import dash_html_components as html
from buzz.buzzword.nav import navbar

with open("docs/depgrep.md", "r") as fo:
    text = fo.read()

layout = html.Div([navbar, dcc.Markdown(text)])
