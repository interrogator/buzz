"""
buzz: attempting to measure token/sentence formality
"""

from pattern.en.wordlist import ACADEMIC, BASIC, PROFANITY
import pandas as pd

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
        if not isinstance(lemma, str):
            xpos = lemma["x"]
            lemma = lemma["l"]
        elif not xpos:
            raise ValueError(
                "For token formality, either pass a Series, or lemma and XPOS"
            )

        scores = dict()

        if (lemma, xpos) in self.override:
            return self.override[(lemma, xpos)]

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
        return sum(self._adjust_by_weights(scores))

    def _adjust_by_weights(self, scores):
        """
        adjust each score by how important we think it is, relatively
        """
        return [
            score * self.weights[name] / self.wsum for name, score in scores.items()
        ]

    def _formality_by_sent_length(self, length):
        """
        A score between -1 and 1 for sent length
        """
        sent_len = min(length, self.max_sent_length)
        return (sent_len - self.max_sent_length / 2) / (self.max_sent_length / 2)

    def sentences(self, df, ignore_sent_length=False):
        """
        Score each sentence in a dataset

        Right now, the score from sentence length is just as important as the averaged tokens score
        """
        sent_scores = dict()
        df["_formality"] = df.apply(self.token, axis=1)
        for fs, sent in df.groupby(level=["file", "s"]):
            average_token_score = sent["_formality"].sum() / len(sent)
            sent_score = self._formality_by_sent_length(len(sent))
            if ignore_sent_length:
                sent_scores[fs] = average_token_score
            else:
                # assume sent and tokens are equally important. how to improve?
                sent_scores[fs] = (sent_score + average_token_score) / 2
        ser = pd.Series(sent_scores)
        df['_sent_formality'] = ser
        return ser

    def text(self, df):
        """
        Average sentence scores
        """
        scores = self.sentences(df)
        return scores.sum() / len(scores)
