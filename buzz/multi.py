"""
buzz: multiprocessing helpers
"""
import multiprocessing
import os

from joblib import delayed

from .utils import _get_tqdm, _to_df, _tqdm_close, _tqdm_update


def how_many(multiprocess):
    """
    Get number of processes, or False

    Hardest utility ever written.
    """
    # silently disable multiprocessing for windows because it fails?
    if os.name == "nt":
        return 1
    if multiprocess is True:
        multiprocess = multiprocessing.cpu_count()
    if multiprocess in {0, 1, False, None}:
        multiprocess = 1
    return multiprocess


@delayed
def load(files, position, **kwargs):
    """
    Picklable loader for multiprocessing
    """
    kwa = dict(
        ncols=120, unit="chunk", desc="Loading", position=position, total=len(files)
    )
    t = _get_tqdm()(**kwa)
    out = []
    for file in files:
        out.append(_to_df(corpus=file, _complete=False, **kwargs))
        _tqdm_update(t)
    _tqdm_close(t)
    return out


@delayed
def read(files, position):
    """
    Picklable reader for multiprocessing (for unparsed corpora)
    """
    kwa = dict(
        ncols=120, unit="chunk", desc="Reading", position=position, total=len(files)
    )
    t = _get_tqdm()(**kwa)
    out = []
    for file in files:
        with open(file.path, "r") as fo:
            out.append(fo.read())
        _tqdm_update(t)
    _tqdm_close(t)
    return out


@delayed
def search(corpus, queries, position, **kwargs):
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


@delayed
def parse(paths, position, save_as, corpus_name, language, constituencies, speakers):
    """
    Parse using multiprocessing, chunks of paths
    """
    from .parse import _process_string

    kwa = dict(
        ncols=120, unit="file", desc="Parsing", position=position, total=len(paths)
    )
    t = _get_tqdm()(**kwa)
    for path in paths:
        with open(path, "r") as fo:
            plain = fo.read().strip()
        _process_string(
            plain, path, save_as, corpus_name, language, constituencies, speakers
        )
        _tqdm_update(t)
    _tqdm_close(t)
