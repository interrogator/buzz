import json
import os
import re
import shutil

from collections import MutableSequence
from functools import total_ordering

from . import utils
from .constants import FORMATS, VALID_EXTENSIONS
from .contents import Contents
from .extract import _extract
from .parse import Parser
from .search import Searcher
from .slice import Filter, Interim

tqdm = utils._get_tqdm()


class Collection(object):
    """
    Model new-style corpus structure, with attributes for each data type

    todo: we can add parse methods here for example
    """

    def __init__(self, path=None, **data_paths):
        path = os.path.expanduser(path)
        self.path = os.path.abspath(path)
        self.name = os.path.basename(os.path.abspath(path).rstrip("/"))
        for form in FORMATS:
            subpath = os.path.join(path, form)
            if os.path.isdir(subpath) and len(os.listdir(subpath)):
                corpus = Corpus(subpath, in_collection=self)
            else:
                corpus = None
            setattr(self, form, corpus)

    def __repr__(self):
        sup = super().__repr__().rstrip(">")
        return f"{sup} ({self.name})>"

    @classmethod
    def new(cls, path, **data_paths):
        """
        Create a new collection. Provide a path for it, and the data to ingest

        coll = Collection.new("my-data", source="./source-files")
        """
        path = os.path.expanduser(path)
        os.makedirs(path)
        for kind, subpath in data_paths.items():
            if kind not in FORMATS:
                err = f"{kind} not recognised. Must be one of: {','.join(FORMATS)}"
                raise ValueError(err)
            format_path = os.path.join(path, kind)
            print(f"Adding {subpath} --> {format_path} ...")
            shutil.copytree(subpath, format_path)
        return cls(path)

    def parse(
        self,
        language="en",
        multiprocess=False,
        constituencies=False,
        speakers=True,
        just_missing=False,
    ):
        language = language.split("_", 1)[0]  # de_frak to de
        parsed_path = os.path.join(self.path, "conllu")
        if self.conllu or os.path.isdir(parsed_path):
            if not just_missing:
                msg = f"Parsed data found at {parsed_path}. Move or delete the folder before parsing again, or parse with just_missing==True."
                raise ValueError(msg)
        self.parser = Parser(
            language=language,
            multiprocess=multiprocess,
            constituencies=constituencies,
            speakers=speakers,
            just_missing=just_missing,
        )
        parsed = self.parser.run(self)
        self.conllu = parsed
        return parsed

    def load(self, **kwargs):
        """
        Sensible helper for loading
        """
        if self.conllu:
            return self.conllu.load(**kwargs)
        return self.txt.load(**kwargs)

    def extract(self, language="en", multiprocess=False, coordinates=True, page_numbers=False):

        return _extract(
            self,
            language=language,
            multiprocess=multiprocess,
            coordinates=coordinates,
            page_numbers=page_numbers
        )


@total_ordering
class Corpus(MutableSequence):
    """
    Model a collection of plain text or CONLL-U files.
    """

    def __init__(self, path=None, in_collection=None):
        """
        Initialise the corpus, deteremine if parsed, hook up methods
        """
        path = os.path.expanduser(path)
        self.format = os.path.basename(path)
        # this is a temporary measure while corpora are being restructured.
        # self.format should eventually be one of a finite set of formats...
        if self.format not in FORMATS:
            if path.endswith("-parsed"):
                self.format = "conllu"
            else:
                self.format = "txt"
        self.in_collection = in_collection

        if not os.path.isdir(path):
            raise NotADirectoryError(f"Not a valid path: {path}")

        self.path = path
        self.name = os.path.basename(os.path.dirname(path))
        self.is_parsed = os.path.basename(path) in {"conllu", "feather"} or path.endswith("-parsed")
        self.subcorpora, self.files = self._get_subcorpora_and_files()
        self.filepaths = Contents(
            [i.path for i in self.files], is_parsed=self.is_parsed, name=self.name
        )
        self.nlp = None
        self.iterable = self.subcorpora if self.subcorpora else self.files

    def __len__(self):
        return len(self.iterable)

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(f"Not same class: {self.__class__} vs {other.__class__}")
        return self.name < other.name

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(f"Not same class: {self.__class__} vs {other.__class__}")
        return self.path == other.path

    def __repr__(self):
        sup = super().__repr__().rstrip(">")
        form = getattr(self, "format", os.path.splitext(self.path)[-1])
        return f"{sup} ({self.path}, {form})>"

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

    def parse(self, language="en", multiprocess=False, constituencies=False, speakers=True):
        """
        Parse a plaintext corpus
        """
        from buzz.file import File
        language = language.split("_", 1)[0]  # de_frak to de
        files = []
        if isinstance(self, File):
            parsed_path = self.path.split("/txt/", 1)[0] + "/conllu"
            files.append(self)
        else:
            parsed_path = os.path.join(os.path.dirname(self.path), "conllu")
        if os.path.isdir(parsed_path):
            msg = f"Parsed data found at {parsed_path}. Move or delete the folder before parsing again."
            raise ValueError(msg)

        self.parser = Parser(
            language=language,
            multiprocess=multiprocess,
            constituencies=constituencies,
            speakers=speakers,
        )
        return self.parser.run(self, files=files)

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
        if self.format == "feather":
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

        info = dict(is_parsed=self.is_parsed, name=self.name)
        subcorpora = list()
        files = list()
        fullpaths = list()
        for root, dirnames, filenames in os.walk(self.path):
            for directory in sorted(dirnames):
                if directory.startswith("."):
                    continue
                directory = os.path.join(root, directory)
                directory = Subcorpus(directory)
                subcorpora.append(directory)
            for filename in filenames:
                allowed = VALID_EXTENSIONS[self.format]
                if allowed and not filename.endswith(tuple(allowed)):
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
        return subcorpora, files

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
