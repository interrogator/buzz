import pandas as pd

from .constants import CONLL_COLUMNS
from .utils import _auto_window, _make_match_col
from .views import _tabview


class Concordance(pd.DataFrame):
    """
    A dataframe holding left, match and right columns, plus optional metadata
    """

    _internal_names = pd.DataFrame._internal_names
    _internal_names_set = set(_internal_names)

    _metadata = ["reference"]
    reference = None

    def __init__(self, data, reference=None):
        super().__init__(data)
        self.reference = reference

    @property
    def _constructor(self):
        return Concordance

    def view(self, *args, **kwargs):
        return _tabview(self, self.reference, *args, **kwargs)


def _get_right(n, allwords, window, multiword=0):
    """
    For df.apply(), generate right

    This needs to be performant.
    """
    # get smallest out of: this index+window_right, or last index
    end = min(multiword + n + window[1], multiword + len(allwords) - 1)
    return " ".join(allwords[n + 1 + multiword : end])[: window[1] + multiword]


def _get_left(n, allwords, window, multiword=0):
    """
    For df.apply(), generate left

    This needs to be performant.
    """
    return " ".join(allwords[max(n - window[0], 0) : n])[-window[0] :]


def multiword_matches(matches, multiword, preserve_case):
    """
    Shift matches to make match column for multiword

    matches is the match column, formatted
    """
    # get just the first word (may not handle -1 etc)
    # match_indices = data_in[data_in.["_position"] == 0]["_n"]
    # this will become a new df
    out = {0: matches.values}
    for i in range(1, multiword+1):
        # shift df so index aligns with the next token in the gram
        shifted = matches.shift(-i)
        out[i] = shifted.values
    # this should give us normal index with 3 cols, word 0, 1, 2
    df = pd.DataFrame(out, index=matches.index)
    made = df.iloc[:,0].str.cat(others=df.iloc[:,1:], sep=" ").str.rstrip("/")
    if not preserve_case:
        made = made.str.lower()
    return made


def _concordance(
    data_in,
    reference,
    show=["w"],
    n=-1,
    window="auto",
    metadata=True,
    preserve_case=True,
    preserve_index=False,
):
    """
    Generate a concordance
    """
    # cut dataset down
    if n and n > 0:
        data_in = data_in.iloc[:n]

    if window == "auto":
        window = _auto_window()
    if isinstance(window, int):
        window = [window, window]

    if not preserve_index:
        data_in = data_in.reset_index()

    # multiword mode, for ngrams and so on
    multiword = "_position" in data_in.columns
    if multiword:
        # error happens on refreshing web interface, not sure why
        try:
            data_in["_position"] = data_in["_position"].astype(int)
        except ValueError:
            pass
        multiword = data_in["_position"].max()
    # get series of matches, fsi index
    matches = _make_match_col(data_in, show, preserve_case=preserve_case)
    match_indices = data_in["_n"]
    # for multiword results, we now need to join the matches with space
    # and potentially change the i-index to a span
    if multiword:
        matches = multiword_matches(matches, multiword, preserve_case)
        matches = matches[data_in["_position"] == 0]
        match_indices = match_indices[data_in["_position"] == 0]

    words = reference["w"].values
    apply_data = dict(allwords=words, window=window, multiword=multiword)
    left = match_indices.apply(_get_left, **apply_data)
    right = match_indices.apply(_get_right, **apply_data)

    left.name, matches.name, right.name = "left", "match", "right"

    ignores = ["_match", "_n", "sent_len", "parse", "text", "_position"]

    conc = pd.concat([left, matches, right], axis=1)

    if metadata is True:  # add all meta cols
        skips = CONLL_COLUMNS + ignores
        metadata = [i for i in list(data_in.columns) if i not in skips]

    if metadata:
        conc = conc.join(data_in[metadata])


    return Concordance(conc, reference=data_in)
