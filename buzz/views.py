"""
in buzz, searches result in corpus subsets. views represent subsets as stats,
or as concordance lines, or as figures...
"""
import math

import numpy as np
import pandas as pd

from .utils import _auto_window, _make_match_col
from .tabview import view


def _get_widths(df, is_conc, window):
    tot = len(df.columns) + len(df.index.names)
    aligns = [True] * tot
    truncs = [False] * tot
    widths = [5]
    if not is_conc:
        widths = [20] * len(df.index.names)
    for i, col_name in enumerate(df.columns):
        if not is_conc:
            widths.append(8)
        elif is_conc and col_name == "left":
            widths.append(window[0])
            truncs[i + len(df.index.names)] = True
        elif is_conc and col_name == "right":
            widths.append(window[1])
            aligns[i + len(df.index.names)] = False
        elif is_conc and col_name == "match":
            mx = df[col_name].astype(str).str.len().max() + 1
            mx = min(15, mx)
            widths.append(mx)
            aligns[i + len(df.index.names)] = False
        elif is_conc:
            mx = df[col_name].astype(str).str.len().max() + 1
            if mx > 10:
                mx = 10
            widths.append(mx)
    return aligns, truncs, widths


def _tabview(df, reference, window="auto", **kwargs):
    """
    Show concordance in interactive cli view
    """
    from .conc import Concordance

    is_conc = type(df) == Concordance

    # needs review
    if isinstance(df.index, pd.MultiIndex):
        index_as_iterable = list(zip(*df.index.to_series()))
        widths = list()
        for index in index_as_iterable:
            biggest = max([len(str(x)) for x in index])
            if biggest < 10:
                widths.append(biggest)
            else:
                widths.append(10)
    # if index is flat, make into string and find longest
    else:
        widths = [5]

    # expand single window integer to both sides
    if isinstance(window, int):
        window = [window, window]
    elif window == "auto":
        window = _auto_window()
    else:
        window = list(window)

    # make window smaller if it can be
    if is_conc:
        window[0] = max(df["left"].str.len().max(), window[0])
        window[1] = max(df["right"].str.len().max(), window[1])

    aligns, truncs, widths = _get_widths(df, is_conc, window)

    view_style = dict(column_widths=widths, reference=reference, df=df)

    if "align_right" not in kwargs:
        view_style["align_right"] = aligns
    if "trunc_left" not in kwargs:
        view_style["trunc_left"] = truncs
    view(df, **view_style)


def _lingres(ser, index):
    """
    Appliable stats calculation
    """
    from scipy.stats import linregress

    ix = ["_slope", "_intercept", "_r", "_p", "_stderr"]
    return pd.Series(linregress(index, ser.values), index=ix)


def _sort(df, by=False, keep_stats=False, remove_above_p=False):
    """
    Sort results, potentially using scipy's linregress
    """
    # translate options and make sure they are parseable
    stat_field = ["_slope", "_intercept", "_r", "_p", "_stderr"]
    easy_sorts = ["total", "infreq", "name", "most", "least", "reverse"]
    stat_sorts = ["increase", "decrease", "static", "turbulent"]

    options = stat_field + easy_sorts + stat_sorts

    # allow some alternative names
    by_convert = {"most": "total", True: "total", "least": "infreq"}
    by = by_convert.get(by, by)

    if keep_stats or by in stat_field + stat_sorts:
        n_column = list(range(len(df)))
        # quick fix: do not have categorical index, because we might want to do regression on them
        try:
            df.index = df.index.astype(int)
        except Exception:
            try:
                df.index = df.index.astype(object)
            except Exception:
                pass
        stats = df.apply(_lingres, axis=0, index=n_column)
        df = df.append(stats)
        df = df.replace([np.inf, -np.inf], 0.0)

    if by == "name":
        # currently case sensitive
        df = df.reindex(sorted(df.columns), axis=1)

    elif by in {"total", "infreq"}:
        ascending = by != "total"
        df = df[list(df.sum().sort_values(ascending=ascending).index)]

    elif by == "reverse":
        df = df.loc[::, ::-1]

    # sort by slope etc., or search by subcorpus name
    if by in stat_field or by not in options:
        asc = False if by is True or by in {"total", "most"} else True

        df = df.T.sort_values(by=by, ascending=asc).T

    if "_slope" in df.index:
        slopes = df.loc["_slope"]
        if by == "increase":
            std = slopes.sort_values(ascending=False)
            df = df[std.index]
        elif by == "decrease":
            std = slopes.sort_values(ascending=True)
            df = df[std.index]
        elif by == "static":
            std = slopes.abs().sort_values(ascending=True)
            df = df[std.index]
        elif by == "turbulent":
            std = slopes.abs().sort_values(ascending=False)
            df = df[std.index]
        if remove_above_p is not False and remove_above_p > 0:
            df = df.T
            df = df[df["_p"] <= remove_above_p]
            df = df.T

    # remove stats field by default
    if not keep_stats:
        df = df.drop(stat_field, axis=0, errors="ignore")
    else:
        df.index = [i.lstrip("_") if i in stat_field else i for i in list(df.index)]
    return df


def _uncomma(row, df, df_show_col, gram_ix):
    n = row.name
    gramsize = str(row[gram_ix]).count(",") + 1
    try:
        rel = df[n : n + gramsize, df_show_col]
        # todo: if df_show_col is list, do slash sep
        form = " ".join(rel)
        return form
    except Exception:  # todo: why?
        return str()


def _relativise(df, denom=None):
    denom = denom if denom is not None else df
    if not isinstance(denom, pd.Series):
        denom = denom.sum(axis=1)
    return (df.T * 100.0 / denom).T


def _log_likelihood(word_in_ref, word_in_target, ref_sum, target_sum):
    """
    calculate log likelihood keyness
    """

    neg = (word_in_target / float(target_sum)) < (word_in_ref / float(ref_sum))

    E1 = float(ref_sum) * (
        (float(word_in_ref) + float(word_in_target))
        / (float(ref_sum) + float(target_sum))
    )
    E2 = float(target_sum) * (
        (float(word_in_ref) + float(word_in_target))
        / (float(ref_sum) + float(target_sum))
    )

    if word_in_ref == 0:
        logaE1 = 0
    else:
        logaE1 = math.log(word_in_ref / E1)
    if word_in_target == 0:
        logaE2 = 0
    else:
        logaE2 = math.log(word_in_target / E2)
    score = float(2 * ((word_in_ref * logaE1) + (word_in_target * logaE2)))
    if neg:
        score = -score
    return score


def _perc_diff(word_in_ref, word_in_target, ref_sum, target_sum):
    """calculate using perc diff measure"""

    norm_target = float(word_in_target) / target_sum
    norm_ref = float(word_in_ref) / ref_sum
    # Gabrielatos and Marchi (2012) do it this way!
    if norm_ref == 0:
        norm_ref = 0.00000000000000000000000001
    return ((norm_target - norm_ref) * 100.0) / norm_ref


def _make_keywords(subcorpus, reference, ref_sum, target_sum, measure):
    points = [
        (reference.get(name, 0), count, ref_sum, target_sum)
        for name, count in subcorpus.iteritems()
    ]
    return [measure(*arg) for arg in points]


def _table(
    dataset,
    subcorpora=["file"],
    show=["w"],
    preserve_case=False,
    sort="total",
    relative=False,
    keyness=False,
    remove_above_p=False,
    multiindex_columns=False,
    keep_stats=False,
    **kwargs
):
    """
    Generate a result table view from Results, or a Results-like DataFrame
    """
    from .table import Table

    # we need access to reference corpus for freq calculation
    df, reference = dataset, dataset.reference

    # show and subcorpora must always be a list
    if not isinstance(show, list):
        show = [show]
    if not isinstance(subcorpora, list):
        subcorpora = [subcorpora]

    # showing next or previous words -- add the cols
    for to_show in show:
        if not to_show.startswith(("+", "-")):
            continue
        df[to_show] = reference[to_show[2:]].shift(-int(to_show[1]))

    if remove_above_p is True:
        remove_above_p = 0.05

    # make a column representing the 'show' info
    df["_match"] = _make_match_col(df, show, preserve_case)
    if reference is not None:
        reference["_match"] = df["_match"]

    # need a column of ones for summing, yuck
    df["_count"] = 1

    # make the matrix
    table = df.pivot_table(
        index=subcorpora, columns="_match", values="_count", aggfunc=sum
    )
    table = table.fillna(0)

    # make table now so we can relative/sort
    table = Table(table, reference=reference)

    # relative frequency if user wants that
    table = table.relative(relative) if relative is not False else table.astype(int)
    if keyness:
        if reference is None:
            warn = "Warning: no reference corpus supplied. Using result frame as reference corpus"
            print(warn)
            reference = df
        ref = reference["_match"].value_counts()
        kwa = dict(
            axis=0,
            reference=ref,
            measure=dict(ll=_log_likelihood, pd=_perc_diff).get(
                keyness, _log_likelihood
            ),
            ref_sum=reference.shape[0],
            target_sum=table.shape[0],
        )
        applied = table.T.apply(_make_keywords, **kwa).T
        top = applied.abs().sum().sort_values(ascending=False)
        table = applied[top.index]

    # sort if the user wants that
    if sort and not keyness:
        sorts = dict(by=sort, keep_stats=keep_stats, remove_above_p=remove_above_p)
        table = table.sort(**sorts)

    # make columns into multiindex if the user wants that
    if multiindex_columns and len(show) > 1:
        table.columns = [i.split("/") for i in table.columns.names]
        table.columns.names = table.columns.names[0].split("/")
    else:
        table.columns.name = "/".join(show)

    df.drop(["_match", "_count"], axis=1, inplace=True, errors="ignore")
    if reference is not None:
        reference.drop("_match", axis=1, inplace=True, errors="ignore")

    return table
