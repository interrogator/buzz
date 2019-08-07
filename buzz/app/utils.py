"""
buzz webapp: helpers and utilities
"""

from buzz.constants import SHORT_TO_LONG_NAME, SHORT_TO_COL_NAME
import pandas as pd


def _get_from_corpus(from_number, dataset):
    """
    Get the correct dataset from number stored in the dropdown for search_from
    """
    specs, corpus = list(dataset.items())[from_number]
    # load from index to save memory
    if not isinstance(corpus, pd.DataFrame):
        corpus = dataset["corpus"].loc[corpus]
    return specs, corpus


def _translate_relative(inp, corpus):
    """
    Get relative and keyness from two-character input
    """
    assert len(inp) == 2
    mapping = dict(t=True, f=False, n=corpus, l="ll", p="pd")
    return mapping[inp[0]], mapping[inp[1]]


def _get_cols(corpus):
    """
    Make list of dicts of conll columns (for search/show)
    """
    col_order = ["file", "s", "i"] + list(corpus.columns)
    cols = [
        dict(label=SHORT_TO_LONG_NAME.get(i, i.title()).replace("_", " "), value=i)
        for i in col_order
    ]
    return cols


def _update_datatable(corpus, df, conll=True, conc=False):
    """
    Helper for datatables
    """
    if conll:
        col_order = ["file", "s", "i"] + list(corpus.columns)
        col_order = [i for i in col_order if i not in ["parse", "text"]]
    elif conc:
        col_order = ["file", "s", "i", "left", "match", "right"]
        rest = [i for i in list(df.columns) if i not in col_order and i not in ["parse", "text"]]
        col_order += rest
    else:
        df.index.names = [f"_{x}" for x in df.index.names]
        col_order = list(df.index.names) + list(df.columns)
    if not conc:
        df = df.reset_index()
    df = df[col_order]
    if conll:
        columns = [{"name": SHORT_TO_COL_NAME.get(i, i), "id": i, "deletable": i not in ["s", "i"]} for i in df.columns]
    elif conc:
        columns = [{"name": i, "id": i, "deletable": i not in ["left", "match", "right"]} for i in df.columns]
    else:
        columns = [{"name": i, "id": i, "deletable": True} for i in df.columns]
    data = df.to_dict("rows")
    return columns, data
