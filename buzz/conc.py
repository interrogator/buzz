import pandas as pd

from .constants import CONLL_COLUMNS
from .views import _make_match_col, _tabview
from .utils import _auto_window


class Concordance(pd.DataFrame):
    """
    A dataframe holding left, match and right columns, plus optional metadata
    """
    def view(self, *args, **kwargs):
        return _tabview(self, *args, **kwargs)


def _apply_conc(line, allwords, window):
    middle, n = line['_match'], line['_n']
    start = max(n - window[0], 0)
    end = min(n + window[1], len(allwords) - 1)
    left = ' '.join(allwords[start:n])[-window[0]:]
    right = ' '.join(allwords[n + 1:end])[:window[1]]
    series = pd.Series([left, middle, right])
    series.names = ['left', 'match', 'right']
    return series


def _concordance(df, reference, show=['w'], n=100, window='auto', metadata=True, **kwargs):
    """
    Generate a concordance
    """
    # max number of lines
    n = max(n, len(df))

    if window == 'auto':
        window = _auto_window()
    if isinstance(window, int):
        window = [window, window]

    df['_match'] = _make_match_col(df, show)

    try:
        df = pd.DataFrame(df).reset_index()
    except ValueError:
        ix = ['file', 's', 'i']
        df = pd.DataFrame(df).drop(ix, axis=1, errors='ignore').reset_index()
    finished = df.apply(_apply_conc, axis=1, allwords=reference['w'].values, window=window)

    finished.columns = ['left', 'match', 'right']
    finished = finished[['left', 'match', 'right']]

    # if showing metadata to the right of lmr, add it here
    cnames = list(df.columns)
    met = [i for i in cnames if i not in CONLL_COLUMNS]
    if metadata is True:
        met_df = df[met]
        finished = pd.concat([finished, met_df], axis=1, sort=False)
    try:
        finished = finished.drop(['_match', '_n', 'sent_len', 'parse'], axis=1, errors='ignore')
    except Exception:  # todo: why?
        pass

    return Concordance(finished)
