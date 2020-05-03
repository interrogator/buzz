"""
in buzz, searches result in corpus subsets. views represent subsets as stats,
or as concordance lines, or as figures...
"""
import math

import numpy as np
import pandas as pd

from .utils import _auto_window, _make_match_col


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

    try:
        from .tabview import view
    except Exception:  # windows, ModuleNotFoundError?
        raise OSError("Not available on Windows, sorry.")

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


def _log_likelihood(data, target_sum, ref_sum):
    """
    Calculate log likelihood keyness
    """
    word_in_target, word_in_ref = data
    neg = (word_in_target / float(target_sum)) < (word_in_ref / float(ref_sum))
    ref_targ = float(word_in_ref) + float(word_in_target)
    ref_targ_sum = float(ref_sum) + float(target_sum)

    E1 = float(ref_sum) * (ref_targ / ref_targ_sum)
    E2 = float(target_sum) * (ref_targ / ref_targ_sum)

    logaE1 = 0 if not word_in_ref else math.log(word_in_ref / E1)
    logaE2 = 0 if not word_in_target else math.log(word_in_target / E2)
    score = float(2 * ((word_in_ref * logaE1) + (word_in_target * logaE2)))
    if neg:
        score = -score
    return score


def _perc_diff(data, target_sum, ref_sum):
    """
    Calculate using perc diff measure :/
    """
    word_in_target, word_in_ref = data
    norm_target = float(word_in_target) / target_sum
    norm_ref = float(word_in_ref) / ref_sum
    # Gabrielatos and Marchi (2012) do it this way!
    if norm_ref == 0:
        norm_ref = 0.00000000000000000000000001
    score = ((norm_target - norm_ref) * 100.0) / norm_ref
    return 0 if score == -100.0 else score


def _make_keywords(subcorpus, reference, ref_sum, measure):
    """
    Apply function for getting keyness calculations

    subcorpus: Series of tokens and their counts for this subcorpus
    """
    # how many words are there in this subcorpus
    target_sum = subcorpus.sum()
    # make series with counts in reference
    df = pd.DataFrame(subcorpus)
    df["_ref_counts"] = reference
    return df.apply(measure, axis=1, raw=True, args=(target_sum, ref_sum))


def _table(
    df,
    subcorpora=["file"],
    show=["w"],
    preserve_case=False,
    sort="total",
    relative=False,
    keyness=False,
    remove_above_p=False,
    multiindex_columns=False,
    keep_stats=False,
    show_entities=False,
    **kwargs,
):
    """
    Generate a result table view from Results, or a Results-like DataFrame
    """
    from .table import Table

    if relative is not False and keyness:
        raise ValueError("Either relative or keyness, not both.")

    # we need access to reference corpus for freq calculation
    reference = getattr(df, "_reference", df)

    # show and subcorpora must always be a list
    if not isinstance(show, list):
        show = [show]
    if subcorpora and not isinstance(subcorpora, list):
        subcorpora = [subcorpora]

    # showing next or previous words -- add the cols
    for to_show in show:
        if not to_show.startswith(("+", "-")):
            continue
        df[to_show] = reference[to_show[2:]].shift(-int(to_show[1]))

    # create a default for remove_above_p
    remove_above_p = 0.05 if remove_above_p is True else remove_above_p

    # make a column representing the 'show' info
    needs_format = df if not keyness else reference
    kwa = dict(show_entities=show_entities, reference=reference)
    match = _make_match_col(needs_format, show, preserve_case, **kwa)
    df["_match"] = match
    reference["_match"] = match

    # make the matrix
    if subcorpora:
        df["_count"] = 1
        pivot = dict(index=subcorpora, columns="_match", values="_count", aggfunc=sum)
        table = df.pivot_table(**pivot)
    else:
        table = pd.DataFrame(df["_match"].value_counts()).T

    table = table.fillna(0)

    # make table now so we can relative/sort
    table = Table(table, reference=reference)

    table = table.astype(int)

    # relative frequency if user wants that
    if relative is not False:
        table = table.relative(relative)
    # keyness calculations
    elif keyness is not False:
        table = table.keyness(keyness, reference=reference)

    # sort if the user wants that. do not sort keyness because it is different
    if sort and not keyness:
        sorts = dict(by=sort, keep_stats=keep_stats, remove_above_p=remove_above_p)
        table = table.sort(**sorts)

    # make columns into multiindex if the user wants that
    if multiindex_columns and len(show) > 1:
        table.columns = table.columns.str.split("/", n=len(show) - 1, expand=True)
        table.columns.names = show
    else:
        table.columns.name = "/".join(show)

    df.drop(["_match", "_count"], axis=1, inplace=True, errors="ignore")
    if reference is not None:
        reference.drop("_match", axis=1, inplace=True, errors="ignore")

    return table


def _keyness(table, keyness, reference=None):
    """
    Need a freq table, keyness measure and a reference corpus
    """
    if reference is None:
        warn = "Warning: no reference corpus supplied. Using result frame as reference corpus"
        print(warn)
        reference = table
    # get the total counts for match column in reference, sorted
    ref = reference["_match"].value_counts()[table.iloc[0].index]
    measures = dict(ll=_log_likelihood, pd=_perc_diff)
    measure = measures.get(keyness, _log_likelihood)
    # kwargs for apply func. ref sum is number of words in reference, which is its shape
    kwa = dict(axis=1, reference=ref, measure=measure, ref_sum=reference.shape[0])
    # keywords runs over every subcorpus and then every match.
    # first, for each row (subcorpus) in the table, we apply _make_keywords
    applied = table.apply(_make_keywords, **kwa)
    top = applied.abs().sum().sort_values(ascending=False)
    table = applied[top.index]
    return table


def _add_frequencies(series, relative, keyness, reference):
    """
    Series should be the _match column (for a subcorpus)

    Return the formatted words as list
    """
    # keyness needs its own calculation.
    if keyness:
        raise NotImplementedError()
        res = _keyness(pd.DataFrame(series), keyness, reference)
        return res

    valcounts = series.value_counts()
    absolute = series.map(valcounts)

    # just absolute frequencies
    if relative is False or relative is None:
        absolute = absolute.map(" (N={:})".format)
        return series.str.cat(absolute)

    # absolute/relative
    rel_data = valcounts * 100 / valcounts.sum()
    relative = series.map(rel_data)
    absolute = absolute.map(" (N={:}/".format)
    relative = relative.map("{:.2f}%)".format)
    return series.str.cat([absolute, relative])
