import os
from collections import defaultdict, Counter

import pandas as pd

from .conc import _concordance
from .search import Searcher
from .slice import Just, Skip, See  # noqa: F401
from .views import _table, _tabview, _make_match_col


class Dataset(pd.DataFrame):
    """
    A corpus or corpus subset in memory
    """

    _internal_names = pd.DataFrame._internal_names
    _internal_names_set = set(_internal_names)

    _metadata = ['reference', '_tfidf']
    reference = None
    _tfidf = dict()

    @property
    def _constructor(self):
        return Dataset

    def __init__(self, data, reference=None, load_trees=False, **kwargs):

        if isinstance(data, str):
            if os.path.isfile(data):
                from .file import File

                data = File(data).load(load_trees=load_trees)
                reference = data
            elif os.path.isdir(data):
                from .corpus import Corpus

                data = Corpus(data).load(load_trees=load_trees)
                reference = data

        super().__init__(data, **kwargs)
        self.reference = reference
        self._tfidf = dict()

    def __len__(self):
        """
        Number of rows
        """
        return self.shape[0]

    def tgrep(self, query, **kwargs):
        """
        Search constituency parses using tgrep
        """
        searcher = Searcher(self)
        return searcher.run('t', query, **kwargs)

    def depgrep(self, query, **kwargs):
        """
        Search dependencies using depgrep
        """
        searcher = Searcher(self)
        return searcher.run('d', query, **kwargs)

    def conc(self, *args, **kwargs):
        """
        Generate a concordance for each row
        """
        return _concordance(self, self.reference, *args, **kwargs)

    def table(self, *args, **kwargs):
        return _table(self, *args, **kwargs)

    def view(self, *args, **kwargs):
        """
        View interactvely with tabview
        """
        return _tabview(self, reference=self.reference, *args, **kwargs)

    def sentences(self):
        """
        Get unique sentences
        """
        return self[self.index.get_level_values('i') == 1]

    def tfidf_by(self, column, show=['w']):
        """
        Generate tfidf vectors for the given column

        I.e. one model for each speaker, setting, whatever
        """
        from sklearn.feature_extraction.text import TfidfVectorizer

        attr_sents = defaultdict(list)
        sents = list()

        # get dict of attr: [list, of, sents]
        self['_formatted'] = _make_match_col(self, show, preserve_case=False)
        if column:
            for attr, df_by_attr in self.groupby(column):
                for fsi, sent in df_by_attr.groupby(level=['file', 's']):
                    attr_sents[attr].append(' '.join(sent['_formatted']))
        else:
            for fsi, sent in self['_formatted'].groupby(level=['file', 's']):
                sents.append(' '.join(sent))
            attr_sents['_base'] = sents

        # for each database, make a vector
        vectors = dict()
        for attr, sents in attr_sents.items():
            vec = TfidfVectorizer()
            vec.fit(sents)
            features = vec.transform(sents)
            vectors[attr] = (vec, features, show)

        # little hack when there are no columns
        if not column:
            vectors = vectors['_base']

        self._tfidf[column] = vectors

    def tfidf_score(self, column, text):
        """
        Score input text against tdif models for this ccolumn
        """
        if column not in self._tfidf:
            self.tfidf_by(column)

        scores = dict()
        for k, (vec, features, show) in self._tfidf[column].items():
            if isinstance(text, str):
                if show != ['w']:
                    err = f'Input text can only be string when vector is ["w"], not {show}'
                    raise ValueError(err)
                sents = [text]
            elif isinstance(text, list):
                sents = text
            else:
                sents = list()
                series = _make_match_col(text, show, preserve_case=False)
                for fsi, sent in series.groupby(level=['file', 's']):
                    sents.append(' '.join(sent))
            new_features = vec.transform(sents)
            scored = (features * new_features.T).A
            scores[k] = scored
            scores[k] = (sum(scored) / len(scored))[0]
        return Counter(scores)

    def sent(self, n):
        """
        Helper: get nth sentence as DataFrame with all index levels intact
        """
        # order of magnitude faster than groupby:
        return self.iloc[self.index.get_loc(self.index.droplevel('i').unique()[n])]
