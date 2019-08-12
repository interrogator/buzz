# flake8: noqa

"""
buzz webapp: helpers and utilities
"""

import pandas as pd

from buzz.constants import SHORT_TO_COL_NAME, SHORT_TO_LONG_NAME
from buzz.strings import _capitalize_first

def _get_from_corpus(from_number, dataset):
    """
    Get the correct dataset from number stored in the dropdown for search_from
    """
    specs, corpus = list(dataset.items())[from_number]
    # load from index to save memory
    if not isinstance(corpus, pd.DataFrame):
        corpus = next(iter(dataset.values())).loc[corpus]
    return specs, corpus


def _translate_relative(inp, corpus):
    """
    Get relative and keyness from two-character input
    """
    if not inp:
        return False, False
    mapping = dict(t=True, f=False, n=corpus, l="ll", p="pd")  # noqa: E741
    return mapping[inp[0]], mapping[inp[1]]


def _get_cols(corpus, add_governor):
    """
    Make list of dicts of conll columns (for search/show)

    Do it by hand because we want a particular order (most common for search/show)
    """
    col_order = ["w", "l", "p", "x", "f", "g", "speaker", "file", "s", "i"]
    if add_governor:
        col_order += ["gw", "gl", "gp", "gx", "gf", "gg"]
    noshow = ["e", "o", "text", "sent_len", "parse", "_n"]
    col_order += [i for i in list(corpus.columns) if i not in col_order + noshow]
    longs = [(i, _capitalize_first(SHORT_TO_LONG_NAME.get(i, i))) for i in col_order]
    return [dict(value=v, label=l.replace("_", " ")) for v, l in longs]


def _update_datatable(corpus, df, conll=True, conc=False, drop_govs=False, deletable=True):
    """
    Helper for datatables
    """
    if conc:
        conll = False
    if conll:
        if drop_govs:
            govs = ["gw", "gl", "gp", "gx", "gf", "gg"]
            cols = [i for i in corpus.columns if i not in govs]
        else:
            cols = list(corpus.columns)
        col_order = ["file", "s", "i"] + cols
        col_order = [i for i in col_order if i not in ["parse", "text", "e"]]
    elif conc:
        col_order = ["file", "s", "i", "left", "match", "right"]
        rest = [
            i
            for i in list(df.columns)
            if i not in col_order and i not in ["parse", "text"]
        ]
        col_order += rest
    else:
        # df.index.names = [f"_{x}" for x in df.index.names]
        col_order = list(df.index.names) + list(df.columns)
    if not conc:
        df = df.reset_index()
    df = df[col_order]
    if conll:
        columns = [
            {
                "name": SHORT_TO_COL_NAME.get(i, i),
                "id": i,
                "deletable": i not in ["s", "i"] and deletable,
            }
            for i in df.columns
        ]
    elif conc:
        columns = [
            {"name": i, "id": i, "deletable": i not in ["left", "match", "right"]}
            for i in df.columns
        ]
    else:
        columns = [
            {"name": i.lstrip("_"), "id": i, "deletable": deletable} for i in df.columns
        ]
    data = df.to_dict("rows")
    return columns, data


def _preprocess_corpus(corpus, max_dataset_rows, drop_columns, **kwargs):
    """
    Fix corpus if the user wants this on command line
    """
    if max_dataset_rows is not None:
        corpus = corpus.iloc[:max_dataset_rows, :]
    if drop_columns is not None:
        corpus = corpus.drop(drop_columns, axis=1)
    return corpus
