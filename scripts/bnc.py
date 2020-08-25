#!/usr/bin/env python3

"""
Helper script to turn BNC XML into a CONLLU corpus with decent metadata

produces a conllu directory which can be loaded with buzz
"""

import os
from bs4 import BeautifulSoup

# get xml paths
paths = []
for root, directories, filenames in os.walk('.'): 
    for filename in filenames:
        path = os.path.join(root, filename)
        if path.endswith(".xml"):
            paths.append(path)

# add more POS translations here...
fixpos = {"SUBST": "NOUN"}

for path in paths:
    print(f"Doing: {path}")
    with open(path, "r") as fo:
        data = fo.read()
    soup = BeautifulSoup(data, 'html.parser')
    doc = []
    filename = os.path.basename(path).replace(".xml", "")
    if soup.find("sourcedesc").bibl:
        title = soup.find("sourcedesc").bibl.title.text.strip()
        author = getattr(soup.find("sourcedesc").bibl.author, "text", "none").strip()
        year = str(getattr(soup.find("sourcedesc").bibl.imprint.date, "text", "none")).strip()
        publisher = str(getattr(soup.find("sourcedesc").bibl.imprint.publisher, "text", "none")).strip()
        location = str(getattr(soup.find("sourcedesc").bibl.imprint.pubplace, "text", "none")).strip()
    else:
        title = "none"
        author = "none"
        year = "none"
        publisher = "none"
        location = "none"
    for i, sent in enumerate(soup.find_all("s"), start=1):
        sent_lines = []
        sent_text = ""
        words = [i for i in sent.find_all(["w", "c"])]
        meta = [
            f"filename = {filename}",
            f"title = {title}",
            f"year = {year.split('-', 1)[0]}",
            f"location = {location}",
            f"publisher = {publisher}",
            f"texttype = {text_type}"
        ]
        # handle italics sections?
        if sent.get("hi"):
            meta.append(f"formatting = {sent.hi['rend']}")
        for x, word in enumerate(words, start=1):
            # if a token doesn't have c5 we will ignore it
            try:
                c5 = word["c5"]
            except:
                continue
            hw = word.get("hw", word.text)
            pos = word.get("pos", "PUNCT")
            pos = fixpos.get(pos, pos)
            text = word.text
            line = f"{x}\t{text}\t{hw}\t{pos}\t{c5}\t_\t_\t_\t_\t_"
            sent_text += text
            sent_lines.append(line)
        meta.append(f"text = {sent_text.strip()}")
        pieces = [f"sent_id = {i}"] + list(sorted(meta))
        pieces = [f"# {q}" for q in pieces]
        complete_sent = "\n".join(pieces) + "\n" + "\n".join(sent_lines)
        doc.append(complete_sent)
    doc = "\n\n".join(doc).strip() + "\n"

    outfile = filename + ".conllu"
    with open("conllu/" + outfile, "w") as fo:
        fo.write(doc)
