import dash_core_components as dcc
import dash_html_components as html
from buzz.buzzword.nav import navbar
import os
import buzz

root = os.path.dirname(os.path.dirname(buzz.__file__))

with open(os.path.join(root, "docs/building.md"), "r") as fo:
    text = fo.read()

layout = html.Div([navbar, dcc.Markdown(text)])
