# flake8: noqa

import re
with open('una.txt', 'r') as fo:
    data = fo.read()
plut = data.split('\n\n')
titles = []
texts = []
for i, piece in enumerate(plut):
    if i % 2 == 0:
        titles.append(piece)
    else:
        texts.append(piece)
for title, text in zip(titles, texts):
    with open(title+'.txt', 'w') as fo:
        fo.write(text.strip())