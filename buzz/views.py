"""
in buzz, searches result in corpus subsets. views represent subsets as stats,
or as concordance lines, or as figures...
"""
import pandas as pd
import numpy as np
from tabview import view

from .utils import _auto_window


def _make_match_col(df, show):
    if len(show) == 1:
        return df[show[0]]
    cats = [df[i].astype(str) for i in show[1:]]
    return df[show[0]].str.cat(others=cats, sep='/').str.rstrip('/')


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
        elif is_conc and col_name == 'left':
            widths.append(window[0])
            truncs[i + len(df.index.names)] = True
        elif is_conc and col_name == 'right':
            widths.append(window[1])
            aligns[i + len(df.index.names)] = False
        elif is_conc and col_name == 'match':
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


def _tabview(df, reference, window='auto', **kwargs):
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
    elif window == 'auto':
        window = _auto_window()
    else:
        window = list(window)

    # make window smaller if it can be
    if is_conc:
        window[0] = max(df['left'].str.len().max(), window[0])
        window[1] = max(df['right'].str.len().max(), window[1])

    aligns, truncs, widths = _get_widths(df, is_conc, window)

    view_style = dict(column_widths=widths, reference=reference, df=df)

    if 'align_right' not in kwargs:
        view_style['align_right'] = aligns
    if 'trunc_left' not in kwargs:
        view_style['trunc_left'] = truncs
    view(pd.DataFrame(df), **view_style)


def _lingres(ser, index):
    """
    Appliable stats calculation
    """
    from scipy.stats import linregress

    ix = ['_slope', '_intercept', '_r', '_p', '_stderr']
    return pd.Series(linregress(index, ser.values), index=ix)


def _sort(df, by=False, keep_stats=False, remove_above_p=False):
    """
    Sort results, potentially using scipy's linregress
    """
    # translate options and make sure they are parseable
    stat_field = ['_slope', '_intercept', '_r', '_p', '_stderr']
    easy_sorts = ['total', 'infreq', 'name', 'most', 'least', 'reverse']
    stat_sorts = ['increase', 'decrease', 'static', 'turbulent']

    options = stat_field + easy_sorts + stat_sorts

    # allow some alternative names
    by_convert = {'most': 'total', True: 'total', 'least': 'infreq'}
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

    if by == 'name':
        # currently case sensitive
        df = df.reindex_axis(sorted(df.columns), axis=1)

    elif by in {'total', 'infreq'}:
        ascending = by != 'total'
        df = df[list(df.sum().sort_values(ascending=ascending).index)]

    elif by == 'reverse':
        df = df.loc[::, ::-1]

    # sort by slope etc., or search by subcorpus name
    if by in stat_field or by not in options:
        asc = False if by is True or by in {'total', 'most'} else True

        df = df.T.sort_values(by=by, ascending=asc).T

    if '_slope' in df.index:
        slopes = df.loc['_slope']
        if by == 'increase':
            std = slopes.sort_values(ascending=False)
            df = df[std.index]
        elif by == 'decrease':
            std = slopes.sort_values(ascending=True)
            df = df[std.index]
        elif by == 'static':
            std = slopes.abs().sort_values(ascending=True)
            df = df[std.index]
        elif by == 'turbulent':
            std = slopes.abs().sort_values(ascending=False)
            df = df[std.index]
        if remove_above_p is not False and remove_above_p > 0:
            df = df.T
            df = df[df['_p'] <= remove_above_p]
            df = df.T

    # remove stats field by default
    if not keep_stats:
        df = df.drop(stat_field, axis=0, errors='ignore')
    else:
        df.index = [i.lstrip('_') if i in stat_field else i for i in list(df.index)]
    return df


def _uncomma(row, df, df_show_col, gram_ix):
    n = row.name
    gramsize = str(row[gram_ix]).count(',') + 1
    try:
        rel = df[n : n + gramsize, df_show_col]
        # todo: if df_show_col is list, do slash sep
        form = ' '.join(rel)
        return form
    except Exception:  # todo: why?
        return str()


def _simple_relative(df, denom=None):
    denom = denom if denom is not None else df
    return (df.T * 100.0 / df.sum(axis=1)).T


def _make_relative_df(df, relative, reference, subcorpora, show, sort, remove_above_p, **kwargs):

    from .dataset import Dataset

    if relative is False:
        return df

    if remove_above_p is True:
        remove_above_p = 0.05

    # default case, use self...
    if relative is True:
        df = _simple_relative(df)

    # if user passed in the reference corpus as relative, table it
    elif relative.shape == reference.shape:
        relative = relative.table(subcorpora=subcorpora, show=show)
        df = _simple_relative(df, relative)

    # if it is results, let us try to table it
    elif isinstance(relative, Dataset):
        relative = relative.table(subcorpora=subcorpora)
        df = _simple_relative(df, relative)

    if sort:
        ks = kwargs.get('keep_stats', False)
        df = _sort(df, by=sort, keep_stats=ks, remove_above_p=remove_above_p)

    # recast to int if possible
    # todo: add dtype check, or only do when
    try:
        if (
            isinstance(df, pd.DataFrame)
            and df.dtypes.all() == float
            and df.applymap(lambda x: x.is_integer()).all().all()
        ):
            df = df.astype(int)
    except AttributeError:
        pass

    return df


def _table(
    dataset,
    subcorpora='default',
    show=['w'],
    preserve_case=False,
    sort='total',
    relative=None,
    ngram=False,
    df=False,
    top=-1,
    remove_above_p=False,
    multiindex_columns=False,
    **kwargs
):
    """
    Generate a result table view from Results, or a Results-like DataFrame
    """
    from .table import Table

    # we need access to reference corpus for freq calculation
    df, reference = dataset, dataset.reference

    # user needs something to have as columns
    if subcorpora == 'default' or subcorpora is False:
        subcorpora = 'file'

    # show and subcorpora must always be a list
    if not isinstance(show, list):
        show = [show]
    if not isinstance(subcorpora, list):
        subcorpora = [subcorpora]

    # showing next or previous words -- add the cols
    for to_show in show:
        if not to_show.startswith(('+', '-')):
            continue
        df[to_show] = reference[to_show[2:]].shift(-int(to_show[1]))

    if remove_above_p is True:
        remove_above_p = 0.05

    # do we have multiword unit information?
    comma_ix = '_gram' in list(df.columns) and df._gram.values[0] is not False
    # if everything is very simple, add _match column
    if all(i in df.columns for i in show) and ngram is False and not comma_ix:
        df['_match'] = _make_match_col(df, show)
    else:
        # make a minimal df for formatting
        # this bit of the code is performace critical, so it's really evil
        if ngram:
            # map column to position
            raise NotImplementedError
        elif comma_ix:
            df['_match'] = df.apply(
                _uncomma,
                axis=1,
                raw=True,
                df=reference.values,
                df_show_col=list(reference.columns).index(show[0]),
                gram_ix=list(df.columns).index('_gram'),
            )

    # do casing
    if not preserve_case:
        df['_match'] = df['_match'].astype(str).str.lower()

    # if only showing top n, cut down to this number?
    if top:
        tops = df['_match'].str.lower().value_counts().head(top)
        df = df[df['_match'].isin(set(tops.index))]

    df['_count'] = 1

    df = df.pivot_table(index=subcorpora, columns='_match', values='_count', aggfunc=sum)

    df.fillna(0, inplace=True)

    if relative is False or relative is None:
        df = df.astype(int)
        ks = kwargs.get('keep_stats', False)
        df = _sort(df, by=sort, keep_stats=ks, remove_above_p=remove_above_p)
    else:
        reference['_match'] = _make_match_col(reference, show)
        df = _make_relative_df(
            df, relative, reference, subcorpora, show, sort, remove_above_p, **kwargs
        )

    df.fillna(0, inplace=True)

    # make columns into multiindex if the user wants
    if multiindex_columns and len(show) > 1:
        df.columns = [i.split('/') for i in df.columns.names]
        df.columns.names = df.columns.names[0].split('/')
    else:
        df.columns.name = '/'.join(show)

    return Table(df, reference=reference)
