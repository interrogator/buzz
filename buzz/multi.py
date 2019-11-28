"""
buzz: multiprocessing helpers
"""

import multiprocessing
from .utils import _get_tqdm, _tqdm_update, _tqdm_close

def _get_multiprocess(multiprocess):
    """
    Get number of processes, or False

    Hardest utility ever written.
    """
    if multiprocess is True:
        multiprocess = multiprocessing.cpu_count()
    if multiprocess in {0, 1, False, None}:
        multiprocess = 1
    return multiprocess

def _load_multi(paths, position, **kwargs):
    """
    Picklable loader for multiprocessing
    """
    kwa = dict(
        ncols=120, unit="chunk", desc="Loading", position=position, total=len(paths)
    )
    t = _get_tqdm()(**kwa)
    out = []
    for path in paths:
        out.append(_to_df(corpus=path, _complete=False, **kwargs))
        _tqdm_update(t)
    _tqdm_close(t)
    return out

def _search_multi(corpus, queries, position, **kwargs):
    """
    Picklable searcher for multiprocessing

    No need for progress bar  because it is in depgrep
    """
    out = []
    for query in queries:
        res = corpus.depgrep(query, position=position, **kwargs)
        if res is not None and not res.empty:
            out.append(res)
    return out
