import pandas as pd
from .constants import CONLL_COLUMNS
from .views import make_match_col

"""
Search results are DataFrame like objects
"""


def resize_by_window_size(df, window):
    df.is_copy = False
    if isinstance(window, int):
        df['left'] = df['left'].str.rjust(window)
        df['right'] = df['right'].str.ljust(window)
        df['match'] = df['match'].str.ljust(df['match'].str.len().max())
    else:
        df['left'] = df['left'].str.rjust(window[0])
        df['right'] = df['right'].str.ljust(window[-1])
        df['match'] = df['match'].str.ljust(df['match'].str.len().max())
    return df


def apply_conc(line, allwords, window):

    file, s, i, middle, n = line['file'], line['s'], line['i'], line['_match'], line['_n']
    start = max(n-window[0], 0)
    end = min(n+window[1], len(allwords)-1)

    left = ' '.join(allwords[start:n])[-window[0]:]
    right = ' '.join(allwords[n+1:end])[:window[1]]

    series = pd.Series([left, middle, right])
    series.names = ['left', 'match', 'right']

    return series


def _concordance(self, show=['w'], n=100, window='auto', metadata=True, **kwargs):
    """
    Generate a concordance

    Args:
        kind (str): string, csv or latex
    """
    df = self._df()
    reference = self.reference

    # max number of lines
    if n > len(df):
        n = len(df)

    if window == 'auto':
        from .utils import auto_window
        window = auto_window()
    if isinstance(window, int):
        window = [window, window]

    # shitty thing to hardcode
    pd.set_option('display.max_colwidth', -1)

    df['_match'] = make_match_col(df, show)
    try:
        df = pd.DataFrame(df).reset_index()
    except ValueError:
        ix = ['file', 's', 'i']
        df = pd.DataFrame(df).drop(ix, axis=1, errors='ignore').reset_index()
    finished = df.apply(apply_conc, axis=1, allwords=reference['w'].values, window=window)

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
    except:
        pass

    from .classes import Concordance
    return Concordance(finished, reference)
