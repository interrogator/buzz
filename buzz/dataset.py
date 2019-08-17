import os

import pandas as pd
import scipy

from .conc import _concordance
from .search import Searcher
from .slice import Just, See, Skip  # noqa: F401
from .tfidf import _tfidf_model, _tfidf_prototypical, _tfidf_score
from .utils import _get_nlp, _make_tree, _tree_once
from .views import _table, _tabview


class Dataset(pd.DataFrame):
    """
    A corpus or corpus subset in memory
    """

    _internal_names = pd.DataFrame._internal_names
    _internal_names_set = set(_internal_names)

    _metadata = ["reference", "_tfidf", "_name"]
    reference = None
    _tfidf = dict()

    @property
    def _constructor(self):
        return Dataset

    def __init__(self, data, reference=None, load_trees=False, name=None, **kwargs):

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
        self._name = name

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

    @property
    def vector(self):
        return self.to_spacy().vector

    def similarity(self, other, save_as=None, **kwargs):
        """
        Get vector similarity between this df and other.

        Other can be a df, a corpus, a corpus path or a text str
        """
        from .corpus import Corpus
        from .parse import Parser

        if isinstance(other, str):
            # if it is a path, load it
            if os.path.exists(other):
                other = Corpus(other)
            # if it is a text string, make a corpus and compare that
            elif save_as:
                other = Corpus.from_string(other, save_as=save_as)
                if not other.is_parsed:
                    other = other.parse()
                other = other.load()
            else:
                parser = Parser(**kwargs)
                other = parser.run(other, save_as=False)

        # the getattr will work on corpus or dataset objects by this point
        vector = getattr(other, "vector", other)
        return scipy.spatial.distance.cosine(self.vector, vector)

    def site(self, title=None, **kwargs):
        """
        Make a website with this dataset as a datatable
        """
        from .dashview import DashSite

        site = DashSite(title)
        height, width = self.shape
        if height > 100 or width > 100:
            warn = f"Warning: shape of data is large ({self.shape}). Performance may be slow."
            print(warn)
        dataset = self.to_frame() if isinstance(self, pd.Series) else self
        site.add("datatable", dataset)
        site.run()
        return site

    def save(self, savename):
        """
        Save to feather
        """
        if "parse" in self.columns:
            par = list()
            for (f, s, i), data in self["parse"].iteritems():
                if i == 1:
                    par.append(data)
                else:
                    par.append(None)
            self["parse"] = par
        self.reset_index().to_feather(savename)

    @staticmethod
    def load(loadname):
        """
        Load from feather
        """
        df = pd.read_feather(loadname)
        name = os.path.splitext(os.path.basename(loadname))[0]
        if name.endswith("-parsed"):
            name = name[:-7]
        df = df.set_index(["file", "s", "i"])
        tree_once = _tree_once(df)
        if isinstance(tree_once.values[0], str):
            df["parse"] = tree_once.apply(_make_tree)
        return Dataset(df, reference=df, name=name)
