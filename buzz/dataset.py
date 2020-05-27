import os

import numpy as np
import pandas as pd
import scipy

from joblib import Parallel

from . import multi
from .conc import _concordance
from .constants import QUERYSETS, SENT_LEVEL_METADATA
from .exceptions import NoReferenceCorpus
from .search import Searcher
from .slice import Just, See, Skip  # noqa: F401
from .tfidf import _tfidf_model, _tfidf_prototypical, _tfidf_score
from .topology import _topology
from .utils import (
    _fix_datatypes_on_save,
    _get_nlp,
    _make_match_col,
    _make_tree,
    _series_to_wordlist,
    _set_best_data_types,
    _tree_once,
)
from .views import _add_frequencies, _table, _tabview


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

    def __init__(self, data, reference=None, name=None, **kwargs):

        if isinstance(data, str):
            if os.path.isfile(data):
                from .file import File

                data = File(data).load()
                reference = data
            elif os.path.isdir(data):
                from .corpus import Corpus

                data = Corpus(data).load()
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
        if reference is None:
            error = (
                "Reference corpus not available in memory for this data. "
                "This is probably because you didn't load your corpus before "
                "searching. Without a reference corpus, there is no data to "
                "generate the left and right columns of a concordance. To fix, "
                "either load corpus before searching, or pass a reference "
                "Dataset: `conc(reference=loaded_corpus)`"
            )
            raise NoReferenceCorpus(error)
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

    def formality(self, **kwargs):
        """
        Calculate the formality of tokens and sentences. Tokens are added to the
        Dataset as _formality column, and sentences are returned. This will change...
        """
        # import here for faster loading
        from .formality import FormalityScorer

        scorer = FormalityScorer()
        return scorer.sentences(self, **kwargs)

    def describe(
        self,
        depgrep_query,
        queryset="NOUN",
        drop_self=False,
        multiprocess=True,
        **kwargs,
    ):
        """
        Run numerous depgrep queries to get modifiers of a noun/verb

        drop_self will remove results also matching depgrep_query itself.
        """
        queries = [q.format(query=depgrep_query) for q in QUERYSETS[queryset]]
        multiprocess = multi.how_many(multiprocess)
        chunks = np.array_split(queries, multiprocess)
        delay = (multi.search(self, x, i, **kwargs) for i, x in enumerate(chunks))
        nested = Parallel(n_jobs=multiprocess)(delay)
        # unpack the nested list that multiprocessing creates
        results = [item for sublist in nested for item in sublist]

        df = pd.concat(results).sort_index().drop_duplicates()
        if drop_self:
            plain = self.depgrep(depgrep_query)
            df = df.drop(plain.index)
        print("\n" * multiprocess)

        df.reference = self
        return df

    def set(self):
        """
        Set this dataset as a corpus (i.e. reindex _n)
        """
        self["_n"] = range(len(self))
        self.reference = self.copy()
        return self

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

    def save(self, savename=None, use="feather"):
        """
        Save to feather/parquet
        """
        if not savename:
            savename = self._name
        if not savename.endswith(".feather") and use == "feather":
            savename += ".feather"
        elif not savename.endswith(".parquet") and use == "parquet":
            savename += ".parquet"
        print(f"Saving dataset to {savename} ...")
        to_reduce = [i for i in self.columns if i in SENT_LEVEL_METADATA]
        df = self.drop("i", axis=1, errors="ignore").reset_index()
        df = _fix_datatypes_on_save(df, to_reduce)
        if to_reduce:
            # amazing line: make nan in many places, save a lot of memory!
            df.loc[df.i != 1, to_reduce] = np.nan
        df.to_feather(savename) if use == "feather" else df.to_parquet(savename)
        print("Done!")

    @staticmethod
    def load(loadname, multiprocess=True):
        """
        Load from feather
        """
        multiprocess = multi.how_many(multiprocess)
        if loadname.endswith(".feather"):
            df = pd.read_feather(loadname, use_threads=multiprocess)
        elif loadname.endswith(".parquet"):
            df = pd.read_parquet(loadname)  # use_threads??
        name = os.path.splitext(os.path.basename(loadname))[0]
        if name.endswith("-parsed"):
            name = name[:-7]
        df = df.set_index(["file", "s", "i"])
        if "parse" in df.columns:
            tree_once = _tree_once(df)
            df["parse"] = tree_once.apply(_make_tree)
        df = df.ffill()
        df = _set_best_data_types(df)
        return Dataset(df, reference=df, name=name)

    def content_table(
        self,
        show=["w"],
        subcorpora=["file"],
        sort="total",
        top=100,
        relative=False,
        keyness=False,
        preserve_case=False,
        show_entities=False,
        show_frequencies=True,
        **kwargs,
    ):
        """
        Make a table where cells are strings, not frequencies

        Show: how cells will be formatted
        subcorpora: what shall be the columns of the dataset (multiindex ok)
        sort: determine what goes first: total/infreq, name/reverse...
        top: max number of rows
        relative: add relative frequency to cell strings
        keyness: add relative frequency to cell strings and sort by keyness
        preserve case: do cells keep their case
        show_entities: show entire named entity, not just term
        """
        reference = self.reference
        # show and subcorpora must always be a list
        cols_added = set()
        if not isinstance(show, list):
            show = [show]
        if subcorpora and not isinstance(subcorpora, list):
            subcorpora = [subcorpora]

        for bit in show + subcorpora:
            if bit in self.index.names and bit not in list(self.columns):
                self[bit] = self.index.get_level_values(bit)
                cols_added.add(bit)

        form = _make_match_col(
            self,
            show,
            preserve_case,
            reference=self.reference,
            show_entities=show_entities,
        )
        self["_match"] = form
        cols_added.add("_match")
        columns = dict()
        self.drop(["file", "s", "i"], axis=1, inplace=True, errors="ignore")
        # reduced = self[needed]
        for group, data in self.reset_index().groupby(subcorpora):
            # series is fsi index, _match formatted values
            series = data["_match"]
            # same format as _match but formatted correctly
            if show_frequencies:
                series = _add_frequencies(
                    series, relative, keyness, reference=reference
                )
            padded = _series_to_wordlist(series, sort, top)
            columns[group] = padded
        # self.drop(list(cols_added), axis=1, inplace=True, errors="ignore")
        return pd.DataFrame(columns)

    def topology(self, kind="verb", wordlist=None, min_occur=10, *args, **kwargs):
        return _topology(
            self, kind=kind, wordlist=wordlist, min_occur=min_occur, *args, **kwargs
        )
