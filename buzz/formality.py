"""
buzz: attempting to measure token/sentence formality
"""

import pandas as pd

from .utils import _get_tqdm

try:
    from pattern.en.wordlist import ACADEMIC, BASIC, PROFANITY
except ImportError:
    print("patttern.en not found. Install it for more precision here!")
    ACADEMIC, BASIC, PROFANITY = set(), set(), set()


tqdm = _get_tqdm()

# here are all the different scores within formality, and how important
# they should be for the final score. adjust them to prioritise things until it works
WEIGHTS = dict(
    length=1,
    formality_of_wordclass=0.2,
    formality_of_word=0.5,
    is_common=-0.3,
    is_academic=0.9,
    is_profane=-0.8,
)

# here are where we add our own data, in order to deal with outliers
LEMMA_FORMALITY = {"be": 0.3, "have": 0.2}  # {"shit": -1, "fuck": -1, "discourse": 0.9}

# here we can judge the relative formality of wordclasses in general.
# because scientific text is heavily nominal, it follows that we can score
# nouns higher than verbs...
WORDCLASS_FORMALITY = {"NOUN": 1, "VERB": -1, "ADJ": -0.3, "ADV": 0.5, "PROPN": 0.8}

# here is the total override; if we encounter something very specific,
# just return score with no further analysis
OVERRIDE = {("shitty", "ADJ"): -0.99}


class FormalityScorer:
    def __init__(self):
        """
        We use a class here so we can save on overhead when calling formality over many many tokens
        """
        self.weights = WEIGHTS
        self.lemma_formality = LEMMA_FORMALITY
        self.wordclass_formality = WORDCLASS_FORMALITY
        self.override = OVERRIDE
        self.wsum = sum([abs(v) for v in WEIGHTS.values()])
        self.max_word_length = 12  # any letters beyond this don't count
        self.max_sent_length = 100

    def token(self, lemma, xpos=None):
        """
        Score a token for formality
        """
        # allow a pandas series (i.e. dataset row) to be passed in
        if isinstance(lemma, pd.Series):
            xpos = lemma[0]
            lemma = lemma[1]
        if not xpos:
            msg = "For token formality, either pass a Series, or lemma and XPOS"
            raise ValueError(msg)

        if (lemma, xpos) in self.override:
            return self.override[(lemma, xpos)]

        scores = dict()

        # add any score we can figure out
        small = min(self.max_word_length, len(lemma))
        scores["length"] = (small - self.max_word_length / 2) / (
            self.max_word_length / 2
        )
        scores["formality_of_wordclass"] = WORDCLASS_FORMALITY.get(xpos, 0)
        scores["formality_of_word"] = LEMMA_FORMALITY.get(lemma, 0)
        scores["is_common"] = 1 if lemma in BASIC else -1
        scores["is_profane"] = 1 if lemma in PROFANITY else -1
        scores["is_academic"] = 1 if lemma in ACADEMIC else -1
        return sum(
            [score * self.weights[name] / self.wsum for name, score in scores.items()]
        )

    def _formality_by_sent_length(self, length):
        """
        A score between -1 and 1 for sent length
        """
        sent_len = min(length, self.max_sent_length)
        return (sent_len - self.max_sent_length / 2) / (self.max_sent_length / 2)

    def _sent_formality(self, group):
        sent_score = self._formality_by_sent_length(len(group))
        token_score = group.mean()
        return ((sent_score / 2) + (token_score * 2)) / 2

    def sentences(self, df):
        """
        Score each sentence in a dataset

        Right now, the score from sentence length is just as important as the averaged tokens score
        """
        kwa = dict(ncols=120, unit="token", desc="Calculating tokens")
        tqdm.pandas(**kwa)
        df["_formality"] = (
            df[["l", "x"]].astype(str).progress_apply(self.token, axis=1, raw=True)
        )
        kwa = dict(ncols=120, unit="sentence", desc="Calculating sentences")
        tqdm.pandas(**kwa)
        groups = df["_formality"].astype(float).groupby(["file", "s"])
        df["_sent_formality"] = groups.progress_apply(self._sent_formality)
        return df[["_formality", "_sent_formality"]]

    def text(self, df):
        """
        Average sentence scores
        """
        scores = self.sentences(df)
        return scores["_formality"].mean()
