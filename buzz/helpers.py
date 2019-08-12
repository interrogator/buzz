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


def _drop_cols_for_datatable(df, add_governor):
    """
    For CONLL table, remove columns that we don't want:

    - parse, text, etc
    - underscored
    - governor attributes if loaded
    """
    drops = ["parse", "text", "e", "sent_id", "sent_len"]
    drops += [i for i in df.columns if i.startswith("_")]
    if add_governor:
        drops += ["gw", "gl", "gp", "gx", "gf", "gg"]
    drops = [i for i in drops if i in df.columns]
    return df.drop(drops, axis=1)


def _get_cols(corpus, add_governor):
    """
    Make list of dicts of conll columns (for search/show) in good order

    Do it by hand because we want a particular order (most common for search/show)
    """
    # normal good features to show
    col_order = ["w", "l", "p", "x", "f", "g", "file", "s", "i"]
    # speaker is kind of privileged by convention
    if "speaker" in corpus.columns:
        col_order.append("speaker")
    # next is all the governor bits if loaded
    if add_governor:
        col_order += ["gw", "gl", "gp", "gx", "gf", "gg"]
    # never show underscored, and never show parse, text, etc.
    under = [i for i in corpus.columns if i.startswith("_")]
    noshow = ["e", "o", "text", "sent_len", "sent_id", "parse"] + under
    # get only items that are actually in dataset
    possible = list(corpus.index.names) + list(corpus.columns)
    # add anything in dataset not already added (i.e. random metadata)
    col_order += [i for i in possible if i not in col_order + noshow]
    # do the formatting of name and id and return it
    longs = [
        (i, _capitalize_first(SHORT_TO_LONG_NAME.get(i, i)).replace("_", " "))
        for i in col_order
        if i in possible
    ]
    return [dict(value=v, label=l) for v, l in longs]


def _update_datatable(
    corpus, df, conll=True, conc=False, drop_govs=False, deletable=True
):
    """
    Make columns and data for datatable display
    """
    conll = conll if not conc else False
    if conll:
        df = _drop_cols_for_datatable(df, drop_govs)
        col_order = ["file", "s", "i"] + list(df.columns)
    elif conc:
        col_order = ["left", "match", "right", "file", "s", "i"]
        if "speaker" in df.columns:
            col_order.append("speaker")
    # for frequency table: rename index in case 'file' appears in columns
    else:
        df.index.names = [f"_{x}" for x in df.index.names]
        col_order = list(df.index.names) + list(df.columns)
    # concordance doesn't need resetting, because index is unhelpful
    if not conc:
        df = df.reset_index()
    df = df[[i for i in col_order if i is not None]]
    cannot_delete = {"s", "i"} if conll else {"left", "match", "right"}
    if conll or conc:
        columns = [
            {
                "name": _capitalize_first(SHORT_TO_COL_NAME.get(i, i)),
                "id": i,
                "deletable": i not in cannot_delete and deletable,
            }
            for i in df.columns
        ]
    else:
        columns = [
            {"name": i.lstrip("_"), "id": i, "deletable": deletable} for i in df.columns
        ]
    return columns, df.to_dict("rows")


def _preprocess_corpus(corpus, max_dataset_rows, drop_columns, **kwargs):
    """
    Fix corpus if the user wants this on command line
    """
    if max_dataset_rows is not None:
        corpus = corpus.iloc[:max_dataset_rows, :]
    if drop_columns is not None:
        corpus = corpus.drop(drop_columns, axis=1)
    return corpus
