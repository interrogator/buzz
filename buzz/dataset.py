import os

import pandas as pd

from .conc import _concordance
from .search import Searcher
from .slice import Just, See, Skip  # noqa: F401
from .tfidf import _tfidf_model, _tfidf_prototypical, _tfidf_score
from .utils import _get_nlp
from .views import _table, _tabview


class Dataset(pd.DataFrame):
    """
    A corpus or corpus subset in memory
    """

    _internal_names = pd.DataFrame._internal_names
    _internal_names_set = set(_internal_names)

    _metadata = ["reference", "_tfidf"]
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
        return Searcher().run(self, "t", query, **kwargs)

    def depgrep(self, query, **kwargs):
        """
        Search dependencies using depgrep
        """
        return Searcher().run(self, "d", query, **kwargs)

    def conc(self, *args, **kwargs):
        """
        Generate a concordance for each row
        """
        reference = kwargs.pop("reference", self.reference)
        return _concordance(self, reference, *args, **kwargs)

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
        return self[self.index.get_level_values("i") == 1]

    def sent(self, n):
        """
        Helper: get nth sentence as DataFrame with all index levels intact
        """
        # order of magnitude faster than groupby:
        return self.iloc[self.index.get_loc(self.index.droplevel("i").unique()[n])]

    def tfidf_by(self, column, n_top_members=-1, show=["w"]):
        """
        Generate tfidf vectors for the given column

        I.e. one model for each speaker, setting, whatever
        """
        vectors = _tfidf_model(self, column, n_top_members=n_top_members, show=show)
        self._tfidf[(column, tuple(show))] = vectors

    def tfidf_score(self, column, show, text):
        """
        Score input text against tdif models for this column

        text is a DataFrame representing one sentence
        """
        return _tfidf_score(self, column, show, text)

    def prototypical(self, column, show, n_top_members=-1, only_correct=True, top=-1):
        """
        Get prototypical instances over bins segmented by column
        """
        return _tfidf_prototypical(
            self,
            column,
            show,
            n_top_members=n_top_members,
            only_correct=only_correct,
            top=top,
        )

    def to_spacy(self, language="en"):
        sents = self.sentences()
        text = " ".join(sents["text"])
        self.nlp = _get_nlp(language=language)
        return self.nlp(text)
