import pandas as pd
from pandas import option_context

from .constants import CONLL_COLUMNS
from .utils import _auto_window, _make_match_col
from .views import _tabview

# setting with copy error for setting ['_match']
pd.options.mode.chained_assignment = None


class Concordance(pd.DataFrame):
    """
    A dataframe holding left, match and right columns, plus optional metadata
    """

    _internal_names = pd.DataFrame._internal_names
    _internal_names_set = set(_internal_names)

    _metadata = ["reference"]
    reference = None

    def __init__(self, data, reference=None, *args, **kwargs):
        super().__init__(data, **kwargs)
        self.reference = reference

    @property
    def _constructor(self):
        return Concordance

    def view(self, *args, **kwargs):
        return _tabview(self, self.reference, *args, **kwargs)

    def __repr__(self):
        cols = ["left", "match", "right"]
        if "speaker" in self.columns and self["speaker"][0]:
            cols.append("speaker")
        with option_context("display.max_colwidth", 200):
            return str(self[cols])


def _apply_conc(line, allwords, window):
    middle, n = line["_match"], line["_n"]
    start = max(n - window[0], 0)
    end = min(n + window[1], len(allwords) - 1)
    left = " ".join(allwords[start:n])[-window[0] :]
    right = " ".join(allwords[n + 1 : end])[: window[1]]
    series = pd.Series([left, middle, right])
    series.names = ["left", "match", "right"]
    return series


def _concordance(
    data_in,
    reference,
    show=["w"],
    n=100,
    window="auto",
    metadata=True,
    preserve_case=True,
):
    """
    Generate a concordance
    """
    # max number of lines
    n = max(n, len(data_in))

    if window == "auto":
        window = _auto_window()
    if isinstance(window, int):
        window = [window, window]

    data_in["_match"] = _make_match_col(data_in, show, preserve_case=preserve_case)

    df = pd.DataFrame(data_in).reset_index()
    finished = df.apply(
        _apply_conc, axis=1, allwords=reference["w"].values, window=window
    )
    finished.columns = ["left", "match", "right"]
    finished = finished[["left", "match", "right"]]

    # if showing metadata to the right of lmr, add it here
    cnames = list(df.columns)
    if metadata is True:
        metadata = [i for i in cnames if i not in CONLL_COLUMNS]
    if metadata:
        met_df = df[metadata]
        finished = pd.concat([finished, met_df], axis=1, sort=False)
    finished = finished.drop(
        ["_match", "_n", "sent_len", "parse"], axis=1, errors="ignore"
    )

    return Concordance(finished, reference=data_in)
