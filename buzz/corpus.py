import json
import os
from collections import MutableSequence
from functools import total_ordering

from . import utils
from .contents import Contents
from .parse import Parser
from .search import Searcher
from .slice import Filter, Interim

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
        path = os.path.expanduser(path)
        self.is_feather = os.path.isfile(path) and path.endswith(".feather")
        if not os.path.isdir(path) and not self.is_feather:
            raise FileNotFoundError(f"Not a valid path: {path}")
        self.path = path
        meta = ".metadata.json"
        self._metadata_path = (
            os.path.join(self.path, meta)
            if not self.is_feather
            # where else should meta go for feather corpora?!
            else os.path.join(os.path.dirname(self.path), meta)
        )
        self.name = os.path.basename(path)
        if self.name.endswith("-parsed"):
            self.name = self.name[:-7]  # lol
        self.subcorpora, self.files, self.is_parsed = self._get_subcorpora_and_files()
        self.filepaths = Contents(
            [i.path for i in self.files], is_parsed=self.is_parsed, name=self.name
        )
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

        with open(f"{dirname}{os.sep}{fname}", "w") as fo:
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
            language="en",
            parser="spacy",
            cons_parser="benepar",
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
        }
        if not all(i in pairs for i in must_exist):
            not_there = must_exist - pairs.keys()
            raise ValueError("Fields must exist: {}".format(not_there))
        with open(self._metadata_path, "w") as fo:
            json.dump(pairs, fo, sort_keys=True, indent=4, separators=(",", ": "))
        return self.metadata

    def parse(
        self, language="en", multiprocess=False, constituencies=False, speakers=True
    ):
        """
        Parse a plaintext corpus
        """
        parsed_path = self.path + "-parsed"
        if os.path.isdir(parsed_path) or self.path.endswith(
            ("-parsed", "conll", "conllu")
        ):
            msg = f"Parsed data found at {parsed_path}. Move or delete the folder before parsing again."
            raise ValueError(msg)
        self.parser = Parser(
            language=language,
            multiprocess=multiprocess,
            constituencies=constituencies,
            speakers=speakers,
        )
        return self.parser.run(self)

    def load(self, **kwargs):
        """
        Load a Corpus into memory

        If it's parsed, a Dataset is returned.
        If unparsed, return a dict mapping paths to strings (the file content)

        Multiprocessing is a bit complex here. You can pass in a keyword arg,
        `multiprocess`, which can be True (use your machine's number of cores),
        an integer (use that many processes), or false/None/0/1, which mean
        just one process.

        Multiprocess is not specified in the call signature, because the default
        should change based on whether or not your corpus is parsed. For parsed
        corpora, multiprocessing is switched on by default. For unparsed, it is
        switched off. This is for performance in both cases --- your unparsed
        corpus needs to be pretty huge to be loaded quicker via multiprocess.
        """
        if self.is_feather:
            return self.files[0].load()
        return utils._load_corpus(self, **kwargs)

    @property
    def vector(self):
        """
        Grab the spacy vector for this document
        """
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
            # TODO: constituencies?
            self.nlp = utils._get_nlp(language=language)
            return self.nlp(" ".join(file_datas))

        models = list()
        for file in self.files:
            models.append(file.to_spacy(language=language))
        return models

    def _get_subcorpora_and_files(self):
        """
        Helper to set subcorpora and files
        """
        from .file import File

        is_parsed = self.path.rstrip(os.sep).endswith(("-parsed", ".feather"))
        info = dict(is_parsed=is_parsed, name=self.name)
        subcorpora = list()
        files = list()
        fullpaths = list()
        if self.is_feather:
            return Contents([], **info), Contents([File(self.path)], **info), True
        for root, dirnames, filenames in os.walk(self.path):
            for directory in sorted(dirnames):
                if directory.startswith("."):
                    continue
                directory = os.path.join(root, directory)
                directory = Subcorpus(directory)
                subcorpora.append(directory)
            for filename in filenames:
                if not filename.endswith(("conll", "conllu", "txt")):
                    continue
                if filename.startswith("."):
                    continue
                fpath = os.path.join(root, filename)
                fullpaths.append(fpath)

        for path in sorted(fullpaths):
            fpath = File(path)
            files.append(fpath)
        subcorpora = Contents(subcorpora, **info)
        files = Contents(files, **info)
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
    """
    This connects corpus.py and slice.py, so that Corpus and Dataset work the same way
    """

    def __init__(self, corpus, inverse=False, see=False):
        self._corpus = corpus
        self.inverse = inverse
        self.see = see

    def __getattr__(self, attr):
        use = Filter if not self.see else Interim
        return use(self._corpus, attr, inverse=self.inverse)

    def __call__(self, column, *args, **kwargs):
        column = utils._ensure_list_of_short_names(column)
        # duplicated because we can't pass list to getattr
        use = Filter if not self.see else Interim
        return use(self._corpus, column, inverse=self.inverse)
