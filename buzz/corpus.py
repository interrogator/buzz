import json
import os
from collections import MutableSequence
from functools import total_ordering

import pandas as pd

from . import utils
from .constants import CONLL_COLUMNS
from .contents import Contents
from .dataset import Dataset
from .parse import Parser
from .search import Searcher
from .slice import Filter, Interim
from .utils import _ensure_list_of_short_names

tqdm = utils._get_tqdm()


@total_ordering
class Corpus(MutableSequence):
    """
    Model a collection of plain text or CONLL-U files.
    """

    def __init__(self, path=None):
        """
        Initialise the corpus, deteremine if parsed, hook up methods
        """
        self.files = Contents()
        self.subcorpora = Contents()
        path = os.path.expanduser(path)
        if not os.path.isdir(path):
            raise FileNotFoundError(f"Not a valid path: {path}")
        self.path = path
        self._metadata_path = os.path.join(self.path, ".metadata.json")
        self.filename = os.path.basename(path)
        self.name = self.filename
        if self.name.endswith("-parsed"):
            self.name = self.name[:-7]
        self.subcorpora, self.files, self.is_parsed = self._get_subcorpora_and_files()
        self.filepaths = Contents([i.path for i in self.files])
        self.nlp = None
        self.iterable = self.subcorpora if self.subcorpora else self.files

    def __len__(self):
        return len(self.iterable)

    @staticmethod
    def from_string(data: str, save_as: str):
        """
        Turn string into corpus and save it as direcoty with name `save_as`
        """
        from .corpus import Corpus

        guess_parsed = "# text = " in data or "-parsed" in save_as
        # if user gave us conll as string and doesn't want to save, just load it.
        if guess_parsed:
            return utils._to_df(data, usename="str")

        if guess_parsed:
            dirname, fname = f"{save_as}-parsed", f"{save_as}.txt.conllu"
        else:
            dirname, fname = f"{save_as}", f"{save_as}.txt"

        if os.path.exists(dirname):
            raise ValueError(f"Already exists: {dirname}")
        os.makedirs(dirname)

        with open(f"{dirname}/{fname}", "w") as fo:
            fo.write(data.strip() + "\n")
        return Corpus(dirname)

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(f"Not same class: {self.__class__} vs {other.__class__}")
        return self.name < other.name

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(f"Not same class: {self.__class__} vs {other.__class__}")
        return self.path == other.path

    def __repr__(self):
        parsed = "parsed" if self.is_parsed else "unparsed"
        form = [super().__repr__().rstrip(">"), self.path, parsed]
        return "{} ({}, {})>".format(*form)

    def __getitem__(self, i):
        """
        Customise what indexing/loopup does for Corpus objects
        """
        return self.iterable[i]

    def __delitem__(self, i):
        del self.iterable[i]

    def __setitem__(self, i, v):
        self.iterable[i] = v

    def insert(self, i, v):
        self.iterable.insert(i, v)

    def tgrep(self, query, **kwargs):
        """
        Search constituency parses using tgrep
        """
        return Searcher().run(self, "t", query, **kwargs)

    def table(self, show=["w"], subcorpora=["file"], **kwargs):
        """
        Generate a frequency table from the whole corpus
        """
        if isinstance(show, str):
            show = [show]
        if isinstance(subcorpora, str):
            subcorpora = [subcorpora]
        needed = show + subcorpora
        usecols = kwargs.pop("usecols", needed)
        loaded = self.load(usecols=usecols)
        return loaded.table(show=show, subcorpora=subcorpora, **kwargs)

    def depgrep(self, query, **kwargs):
        """
        Search dependencies using depgrep
        """
        return Searcher().run(self, "d", query, **kwargs)

    @property
    def metadata(self):
        """
        Metadata dict for this corpus. Generate if it's not there
        """
        if not os.path.isfile(self._metadata_path):
            return self._generate_metadata()
        with open(self._metadata_path, "r") as fo:
            return json.load(fo)

    def _generate_metadata(self):
        """
        Create, store and return the metadata for this corpus
        """
        meta = dict(
            language="english",
            parser="spacy",
            cons_parser="bllip",
            path=self.path,
            name=self.name,
            parsed=self.is_parsed,
            nsents=-1,
            ntokens=-1,
            nfiles=len(self.files),
            desc="",
        )
        self.add_metadata(**meta)
        return meta

    def add_metadata(self, **pairs):
        """
        Add key-value pairs to metadata for this corpus

        Return the complete metadata dict
        """
        must_exist = {
            "name",
            "desc",
            "parsed",
            "nfiles",
            "nsents",
            "path",
            "language",
            "parser",
            "cons_parser",
        }
        if not all(i in pairs for i in must_exist):
            not_there = must_exist - pairs.keys()
            raise ValueError("Fields must exist: {}".format(not_there))
        with open(self._metadata_path, "w") as fo:
            json.dump(pairs, fo, sort_keys=True, indent=4, separators=(",", ": "))
        return self.metadata

    def parse(self, cons_parser: str = "bllip", language: str = "english", **kwargs):
        """
        Parse a plaintext corpus
        """
        parsed_path = self.path + "-parsed"
        if os.path.isdir(parsed_path) or self.path.endswith(
            ("-parsed", "conll", "conllu")
        ):
            raise ValueError("Corpus is already parsed.")
        self.parser = Parser(cons_parser=cons_parser, language=language)
        return self.parser.run(self)

    def load(self, load_trees: bool = False, **kwargs):
        """
        Load a Corpus into memory.
        """
        # progress indicator
        kwa = dict(ncols=120, unit="file", desc="Loading", total=len(self))
        t = tqdm(**kwa) if len(self.files) > 1 else None

        # load each file and add to list, indicating progress
        loaded = list()
        prsd = self.is_parsed
        for file in self.files:
            loaded.append(
                file.load(load_trees=load_trees, **kwargs) if prsd else file.read()
            )
            utils._tqdm_update(t)
        utils._tqdm_close(t)

        # for parsed corpora, we merge each file contents into one huge dataframe as LoadedCorpus
        if self.is_parsed:
            df = pd.concat(loaded, sort=False)
            if load_trees:
                tree_once = utils._tree_once(df)
                if isinstance(tree_once.values[0], str):
                    df["parse"] = tree_once.apply(utils._make_tree)

            df = df.drop("_n", axis=1, errors="ignore")
            col_order = list(df.columns)
            df["_n"] = range(len(df))
            df = df[col_order + ["_n"]]
            df = utils._set_best_data_types(df)
            fixed = self._order_columns(df)
            return Dataset(fixed, reference=fixed, name=self.name)
        # for unparsed corpora, we give a dict of {path: text}
        else:
            from collections import OrderedDict

            return OrderedDict(sorted(zip(self.filepaths, loaded)))

    @property
    def vector(self):
        spac = self.to_spacy(concat=True)
        return spac.vector

    def to_spacy(self, language="en", concat=False):
        """
        Get spacy's model of the Corpus

        If concat is True, model corpus as one spacy Document, rather than a list
        """
        if concat:
            file_datas = [f.read() for f in self.files]
            # for parsed corpora, we have to pull out the "# text = " lines...
            if self.is_parsed:
                out = list()
                for data in file_datas:
                    out.append(utils._get_texts(data))
                file_datas = out
            self.nlp = utils._get_nlp(language=language)
            return self.nlp(" ".join(file_datas))

        models = list()
        for file in self.files:
            models.append(file.to_spacy(language=language))
        return models

    @staticmethod
    def _order_columns(df):
        """
        Put Corpus columns in best possible order. This means, follow CONLL-U, then metadata.
        At the end we add _n, a helper column that is just a range index
        """
        proper_order = CONLL_COLUMNS[1:]
        fixed = [i for i in proper_order if i in list(df.columns)]
        met = list(sorted([i for i in list(df.columns) if i not in proper_order]))
        met.remove("_n")
        if met:
            fixed += met
        return df[fixed + ["_n"]]

    def _get_subcorpora_and_files(self):
        """
        Helper to set subcorpora and files
        """
        from .file import File

        subcorpora = list()
        files = list()
        for root, dirnames, filenames in os.walk(self.path):
            for filename in sorted(filenames):
                if not filename.endswith(("conll", "conllu", "txt")):
                    continue
                if filename.startswith("."):
                    continue
                fpath = os.path.join(root, filename)
                fpath = File(fpath)
                files.append(fpath)
            for directory in dirnames:
                if directory.startswith("."):
                    continue
                directory = os.path.join(root, directory)
                directory = Subcorpus(directory)
                subcorpora.append(directory)
        subcorpora = Contents(list(sorted(subcorpora)))
        files = Contents(list(sorted(files)))
        is_parsed = self.path.endswith("-parsed")
        return subcorpora, files, is_parsed

    @property
    def just(self):
        """
        Allow corpus.just.word.the without loading everything into memory
        """
        return SliceHelper(self)

    @property
    def skip(self):
        """
        Allow corpus.skip.word.the without loading everything into memory
        """
        return SliceHelper(self, inverse=True)

    @property
    def see(self):
        """
        Allow corpus.see.word.by.speaker
        """
        return SliceHelper(self, inverse=True, see=True)


class Subcorpus(Corpus):
    """
    Simply a renamed Corpus, fancy indeed!
    """

    def __init__(self, path, **kwargs):
        super().__init__(path, **kwargs)


class SliceHelper(object):
    def __init__(self, corpus, inverse=False, see=False):
        self._corpus = corpus
        self.inverse = inverse
        self.see = see

    def __getattr__(self, attr):
        use = Filter if not self.see else Interim
        return use(self._corpus, attr, inverse=self.inverse)

    def __call__(self, column, *args, **kwargs):
        column = _ensure_list_of_short_names(column)
        # duplicated because we can't pass list to getattr
        use = Filter if not self.see else Interim
        return use(self._corpus, column, inverse=self.inverse)
