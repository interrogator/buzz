"""
buzz's topology method
"""

from collections import defaultdict
import pandas as pd
import numpy as np
from joblib import Parallel
from .constants import TOPOLOGY_QUERIES
from . import multi
from .utils import _get_tqdm, _tqdm_update, _tqdm_close

from scipy.spatial.distance import cosine

tqdm = _get_tqdm()


def _cos_unit(row, df=None):
    """
    appliable
    """
    return cosine(row, pd.Series([1] * len(df.columns), index=df.columns))


def _create_cos(word, df):
    """
    appliable
    """

    def cos_word(row):
        return cosine(row, df.loc[word])

    return cos_word


class TopologyData(pd.DataFrame):
    """
    A corpus or corpus subset in memory
    """

    _internal_names = pd.DataFrame._internal_names
    _internal_names_set = set(_internal_names)

    @property
    def _constructor(self):
        return TopologyData

    def __init__(self, data, *args, **kwargs):
        super().__init__(data, *args, **kwargs)

    def _make_axis_data(self, word):
        if word == "euclid":
            return self.pow(2).sum(axis=1).pow(0.5)
        if word == "taxi":
            return self.sum(axis=1)
        if word == "cos_unit":
            return self.apply(_cos_unit, df=self, axis=1)

        return self.apply(_create_cos(word, self), df=self, axis=1)

    def word_axis(self, word1, word2):
        import matplotlib.pyplot as plt

        drops = ["axeuclid", "axtaxi", "axcos_unit"]
        self = self.drop(drops, errors="ignore")
        w1_data = self._make_axis_data(word1)
        w2_data = self._make_axis_data(word2)
        key1 = "ax" + word1
        key2 = "ax" + word2
        self[key1] = w1_data
        self[key2] = w2_data

        fig, ax = plt.subplots()
        self.plot(x=key1, y=key2, style="o", ax=ax, legend=None)
        for index, row in self.iterrows():
            ax.annotate(index, (row[key1], row[key2]))
        plt.show()

    def euclid(self):
        return self.T.word_axis("taxi", "euclid")

    def cosine(self):
        return self.T.word_axis("euclid", "cos_unit")


def _process_chunk(dataset, word, name, query, is_bool, features_of_interest, counts):
    # dataset = pd.read_pickle(dataset)
    results = dict()
    if not isinstance(query, str):
        # lambda query can be done as an apply, no depgrep
        result = dataset[dataset.apply(query, axis=1)]
    else:
        # put the lemma into the unformatted query
        query = query.format(query=f'l"{word}"')
        result = dataset.depgrep(query, position=None)
    if result.empty:
        # or return df
        return
    # if we have not specified which particular features to count,
    # e.g. {w, l, x}, we just count the result row itself
    if not features_of_interest:
        count = len(result) / counts[word]
        if count > 0:
            return word, {name.lower(): count}
        else:
            return

    # this is almost certainly if we want the index of the word (i)
    if any(i in {"file", "s", "i"} for i in features_of_interest):
        result = result.reset_index()
    for col in features_of_interest:
        # in our search result, count tokens (rows) by feature of interest
        valcount = result[col].value_counts()
        # this could be an apply, but we need both key and value
        # so we would need to make it into a DataFrame... annoying
        for realisation, subc in valcount.items():
            # make the feature name
            bits = [name, col, str(realisation)]
            # the replace is for -pron- lemma mostly
            feature_name = "_".join(bits).lower().replace("-", "")
            # divide occurrences by length of corpus
            # a value of 1 would indicate that all that occurred in the
            # corpus was this feature??
            count = subc / len(dataset)
            if count > 0:
                # not sure if we should divide by corpus length instead?
                results[feature_name] = subc / counts[word]
        return word, results


def _topology(dataset, kind="verb", wordlist=None, min_occur=10, *args, **kwargs):
    queries = TOPOLOGY_QUERIES[kind.upper()].copy()
    queries.update(TOPOLOGY_QUERIES["GENERAL"])
    relevant = getattr(dataset.just.wordclass, kind.upper())
    relevant = relevant[relevant["l"].str.isalnum()]
    if wordlist:
        relevant = relevant.just.lemma(wordlist, regex=False, exact_match=True)
    # counts is referred to in the main loop
    counts = relevant.l.value_counts()
    min_occur = 1 if not min_occur else min_occur
    to_search = list(counts[counts >= min_occur].index)
    n_tok = len(to_search)
    n_search = n_tok * len(queries)
    formatted = ", ".join(to_search)
    print(f"To be analysed ({n_tok} tokens, {n_search} searches): {formatted}\n\n")
    # all the results end up in this huge dict
    huge = defaultdict(dict)
    searches = list()
    multiprocess = multi.how_many(kwargs.pop("multiprocess", True))
    for word in to_search:
        for name, (query, is_bool, features_of_interest) in queries.items():
            # todo: remove when there are no more lambdas
            if isinstance(query, str):
                searches.append(
                    [word, name, query, is_bool, features_of_interest, counts.copy()]
                )

    if multiprocess and multiprocess > 1:
        # multiprocess does not work with lambda queries!
        chunks = np.array_split(searches, multiprocess)
        delay = (multi.topology(dataset, x, i) for i, x in enumerate(chunks))
        results = Parallel(n_jobs=multiprocess)(delay)
        results = [item for sublist in results for item in sublist]
        out = defaultdict(dict)
        for result in results:
            if result is None:
                continue
            term, freq = result
            out[term].update(freq)
        top = TopologyData(out)
        return top.fillna(0.0)

    t = tqdm(ncols=120, unit="query", desc=f"Counting {kind.lower()}s", total=n_search)
    for word, name, query, _is_bool, features_of_interest, _ in searches:
        huge[word] = dict()
        if not isinstance(query, str):
            # lambda query can be done as an apply, no depgrep
            result = dataset[dataset.apply(query, axis=1)]
        else:
            # put the lemma into the unformatted query
            query = query.format(query=f'l"{word}"')
            result = dataset.depgrep(query, position=None)
        if result.empty:
            _tqdm_update(t, postfix=word)
            continue
        # if we have not specified which particular features to count,
        # e.g. {w, l, x}, we just count the result row itself
        if not features_of_interest:
            count = len(result) / counts[word]
            if count > 0:
                huge[word][name.lower()] = count
            _tqdm_update(t, postfix=word)
            continue
        # this is almost certainly if we want the index of the word (i)
        if any(i in {"file", "s", "i"} for i in features_of_interest):
            result = result.reset_index()
        for col in features_of_interest:
            # in our search result, count tokens (rows) by feature of interest
            valcount = result[col].value_counts()
            # this could be an apply, but we need both key and value
            # so we would need to make it into a DataFrame... annoying
            for realisation, subc in valcount.items():
                # make the feature name
                bits = [name, col, str(realisation)]
                # the replace is for -pron- lemma mostly
                feature_name = "_".join(bits).lower().replace("-", "")
                # divide occurrences by length of corpus
                # a value of 1 would indicate that all that occurred in the
                # corpus was this feature??
                count = subc / len(dataset)
                if count > 0:
                    # not sure if we should divide by corpus length instead?
                    huge[word][feature_name] = subc / counts[word]
            _tqdm_update(t, postfix=word)
    _tqdm_close(t)
    top = TopologyData(huge)
    return top.fillna(0.0)
