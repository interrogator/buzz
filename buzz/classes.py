import os
from .search import Searcher
from .parse import Parser
from .constants import CONLL_COLUMNS, LONG_NAMES
from collections import MutableSequence
from .utils import _to_df, _get_nlp, _strip_metadata, _set_best_data_types, _get_tqdm, _tqdm_close, _tqdm_update
from .views import _tabview, _table
from .keys import _keywords
import pandas as pd
import re
from functools import total_ordering
import json

tqdm = _get_tqdm()


class Contents(MutableSequence):
    """
    Holder for ordered collections of files or subcorpora
    """
    def __init__(self, data=[]):
        self.list = data

    def __repr__(self):
        return str(self.list)

    def __len__(self):
        if not self.list:
            return 0
        return len(self.list)

    def __bool__(self):
        return True if self.list else False

    def __getattr__(self, name):
        """
        Attribute style access to subcorpora/files, preferring former
        """
        return next((i for i in self.list if i.no_ext == name), None)

    def __getitem__(self, i):
        to_iter = self.list
        if isinstance(i, str):
            # dict style lookup of files when there are no subcorpora
            return next((s for s in to_iter if s.name.rsplit('.', 1)[0] == i), None)
        # allow user to pass in a regular expression and get all matching names
        if isinstance(i, re._pattern_type):
            it = [s for s in to_iter if re.search(i, s.name.split('.', 1)[0])]
            return Corpus(it, path=self.path, name=self.name)
        # normal indexing and slicing
        if isinstance(i, slice):
            return Corpus(to_iter[i], path=self.path, name=self.name)
        return to_iter[i]

    def __delitem__(self, i):
        del self.list[i]

    def __setitem__(self, i, v):
        self.list[i] = v

    def insert(self, i, v):
        self.list.insert(i, v)


class Corpus(MutableSequence):
    """
    Model a collection of plain text or CONLL-U files.
    """
    def __init__(self, data=None, root=None, path=None, name=None, too_large_for_memory=False):
        """
        Initialise the corpus, deteremine if parsed, hook up methods
        """
        self.files = Contents()
        self.subcorpora = Contents()
        self.list = list()
        self.path = path
        self.root = root
        self.name = name
        self.is_conll = None
        self.is_parsed = None
        self.too_large_for_memory = self._check_if_too_large(too_large_for_memory)
        self.parser = Parser(self)
        self._understand_input(data)
        self.extend(self.files)
        self._metadata_path = os.path.join(self.path, '.metadata.json')

    def is_loaded(self):
        return type(self) == LoadedCorpus

    @property
    def metadata(self):
        if not os.path.isfile(self._metadata_path):
            return self._generate_metadata()
        with open(self._metadata_path, 'r') as fo:
            return json.load(fo)

    def _generate_metadata(self):
        meta = dict(language='english',
                    parser='spacy',
                    cons_parser='benepar',
                    copula_head=True,
                    path=self.path,
                    name=self.name,
                    parsed=self.is_parsed,
                    nsents=-1,
                    ntokens=-1,
                    nfiles=len(self.files),
                    desc='')
        self.add_metadata(meta)
        return meta

    def add_metadata(self, value):
        must_exist = {'name',
                      'desc',
                      'parsed',
                      'nfiles',
                      'nsents',
                      'path',
                      'language',
                      'parser',
                      'cons_parser'}
        if not all(i in value for i in must_exist):
            not_there = must_exist - value.keys()
            raise ValueError('Fields must exist: {}'.format(not_there))
        with open(self._metadata_path, 'w') as fo:
            json.dump(value, fo, sort_keys=True, indent=4, separators=(',', ': '))
        return self.metadata

    def concordance(self, target='w', query='.*', show=['w'], subcorpora='file', **kwargs):
        results = Searcher(self).run(target, query, **kwargs)
        return results.conc(show=show, subcorpora=subcorpora, **kwargs)

    def conc(self, *args, **kwargs):
        return self.concordance(*args, **kwargs)

    def _check_if_too_large(self, passed_in):
        if passed_in is False:
            return False
        size = sum(os.path.getsize(os.path.join(dirpath, filename)) for dirpath, dirnames, filenames in os.walk('.') for filename in filenames)
        import psutil
        free_mem = psutil.virtual_memory().free
        return size * 10 > free_mem

    def table(self, *args, **kwargs):
        return _table(self, *args, **kwargs)

    def keywords(self, *args, **kwargs):
        return _keywords(self, *args, **kwargs)

    def __repr__(self):
        if isinstance(self, File):
            form = [super().__repr__().rstrip('>'), os.path.abspath(self.path)]
            return '{}: {}>'.format(*form)
        parsed = ''
        if not isinstance(self, Subcorpus):
            parsed = ', parsed' if self.is_parsed else ', unparsed'

        form = [super().__repr__().rstrip('>'), self.name, parsed, len(self.subcorpora), len(self.files)]
        return '{} ({}{}): {} subcorpora, {} files>'.format(*form)

    def tabview(self, *args, **kwargs):
        return _tabview(self, *args, **kwargs)

    def _understand_input(self, input_data):
        """
        Figure out what was passed in and process it correctly
        """
        if isinstance(input_data, str):
            input_data = os.path.expanduser(input_data)
        # assume a list of files
        if isinstance(input_data, list):
            self.files = input_data
        # a single file
        elif os.path.isfile(input_data):
            self.path = input_data
            self.files.append(input_data)
            self.name = os.path.basename(os.path.splitext(input_data)[0])
            self.is_parsed = input_data.endswith(('conll', 'conllu'))
        # a folder containing either files or subcorpora
        elif os.path.isdir(input_data):
            self.path = input_data
            self.name = os.path.basename(input_data)
            self._get_corpus_contents()

        # if there are any files, figure out if they are parsed
        if self.files:
            if self.files[0].path.endswith(('conll', 'conllu')):
                self.is_parsed = True
            else:
                self.is_parsed = False

        # get a list of each filepath
        self.filepaths = Contents([i.path for i in self.files])

    def _prepare_spacy(self, language='en'):
        self.nlp = _get_nlp(language=language)

    def spacy(self, language='en', **kwargs):
        return self.load(spacy=True, language=language, **kwargs)

    def __len__(self):
        return len(self.list)

    def __getitem__(self, i):
        """
        Customise what indexing/loopup does for Corpus objects
        """
        to_iter = self.list
        if isinstance(i, str):
            # dict style lookup of files when there are no subcorpora
            return next((s for s in to_iter if s.name.split('.', 1)[0] == i), None)
        # allow user to pass in a regular expression and get all matching names
        try:
            pattern_type = re._pattern_type
        except:
            pattern_type = re.Pattern
        if isinstance(i, pattern_type):
            return Corpus([s for s in to_iter if re.search(i, s.name.split('.', 1)[0])], path=self.path, name=self.name)
        # normal indexing and slicing
        if isinstance(i, slice):
            return Corpus(to_iter[i], path=self.path, name=self.name)
        return to_iter[i]

    def __delitem__(self, i):
        del self.list[i]

    def __setitem__(self, i, v):
        self.list[i] = v

    def insert(self, i, v):
        self.list.insert(i, v)

    def __getattr__(self, name):
        """
        Attribute style access to subcorpora/files, preferring former
        """
        if self.subcorpora:
            return next((i for i in self.subcorpora if i.name == name), None)
        gen = (i for i in self.files if os.path.splitext(i.name)[0] == name)
        return next(gen, None)

    def get_container(self, subcorpus_path, corpus_path):
        if os.path.samefile(subcorpus_path, corpus_path):
            return self
        else:
            return Subcorpus(subcorpus_path)

    def _get_corpus_contents(self):
        """
        Helper to set subcorpora and files
        """
        subcorpora = list()
        files = list()
        for root, dirnames, filenames in os.walk(self.path):
            for filename in sorted(filenames):
                if not filename.endswith(('conll', 'conllu', 'txt')):
                    continue
                fpath = os.path.join(root, filename)
                container = self.get_container(root, self.path)
                fpath = File(fpath, root=self.path, container=container)
                files.append(fpath)
            for directory in dirnames:
                if directory.startswith('.'):
                    continue
                directory = os.path.join(root, directory)
                directory = Subcorpus(directory, root=self.path)
                subcorpora.append(directory)
        self.subcorpora = Contents(list(sorted(subcorpora)))
        self.files = Contents(list(sorted(files)))
        if not self.files:
            self.is_parsed = self.name.endswith('-parsed')
        else:
            self.is_parsed = self.files[0].name.endswith(('conll', 'conllu'))

    def search(self, target, query, *args, **kwargs):
        """
        Search for a linguistic feature
        """
        return Searcher(self).run(target, query, *args, **kwargs)

    def words(self, query, *args, **kwargs):
        """
        Search corpus for words
        """
        return Searcher(Searcher(self)).run('d', query, *args, **kwargs)

    def lemmata(self, query, *args, **kwargs):
        """
        Search corpus for lemmata
        """
        return Searcher(Searcher(self)).run('l', query, *args, **kwargs)

    def pos(self, query, *args, **kwargs):
        """
        Search corpus for POS tag
        """
        return Searcher(Searcher(self)).run('p', query, *args, **kwargs)

    def roles(self, query, *args, **kwargs):
        """
        Search corpus for dependency role
        """
        return Searcher(Searcher(self)).run('f', query, *args, **kwargs)

    def deps(self, query, *args, **kwargs):
        """
        Search dependencies
        """
        return Searcher(Searcher(self)).run('d', query, *args, **kwargs)

    def trees(self, query, *args, **kwargs):
        """
        Search parse trees
        """
        return Searcher(Searcher(self)).run('t', query, *args, **kwargs)

    def tree_once(self, df):
        """
        Get just each tree once --- can try to optimise
        """
        return _tree_once(df)

    def load(self, spacy=False, combine=False, load_trees=False, **kwargs):
        """
        Load a Corpus into memory
        """
        kwa = dict(ncols=120,
                   unit='file',
                   desc='Loading',
                   total=len(self))

        t = tqdm(**kwa) if len(self) > 1 else None

        loaded = list()
        for file in self.files:
            if not combine:
                loaded_file = file.load(spacy=spacy, notype=True, **kwargs)
                loaded.append(loaded_file)
            else:
                loaded.append(file.read())

            _tqdm_update(t)
        _tqdm_close(t)

        if combine and not self.nlp:
            self._prepare_spacy()
            loaded = _strip_metadata('\n'.join(loaded))
            return self.nlp(loaded)

        if self.is_parsed:
            df = pd.concat(loaded, sort=False)
            if load_trees:
                tree_once = self.tree_once(df)
                if isinstance(tree_once.values[0], str):
                    from nltk.tree import ParentedTree
                    from .utils import maketree
                    df['parse'] = tree_once.apply(maketree)

            df = df.drop('_n', axis=1, errors='ignore')
            col_order = list(df.columns)
            df['_n'] = range(len(df))
            df = df[col_order + ['_n']]
            df = _set_best_data_types(df)
            return LoadedCorpus(self.order_columns(df))
        else:
            from collections import OrderedDict
            return OrderedDict(sorted(zip(self.filepaths, loaded)))

    @staticmethod
    def order_columns(df):
        proper_order = CONLL_COLUMNS[1:]
        fixed = [i for i in proper_order if i in list(df.columns)]
        met = list(sorted([i for i in list(df.columns) if i not in proper_order]))
        met.remove('_n')
        if met:
            fixed += met
        return df[fixed + ['_n']]

    def parse(self, parser='spacy', cons_parser='benepar', language='english', multiprocess=False, **kwargs):
        """
        Parse a plaintext corpus

        Keyword Args:
            parser (str): name of the parser (only 'corenlp' accepted so far)
            lang (str): language for parser (`english`, `arabic`, `chinese`,
                        `german`, `french` or `spanish`)
            multiprocess (int): number of parallel threads to start
            memory_mb (int): megabytes of memory to use per thread (default 2024)

        Returns:
            :class:`buzz.corpus.Corpus`: parsed corpus

        """
        parsed_path = self.path + '-parsed'
        if os.path.isdir(parsed_path):
            raise ValueError('Corpus is already parsed.')
            return Corpus(parsed_path)
        if self.path.endswith(('-parsed', 'conll', 'conllu')):
            raise ValueError('Corpus is already parsed.')
        self.parser = Parser(self, parser=parser, cons_parser=cons_parser, language=language)
        return self.parser.run(self, multiprocess=multiprocess, **kwargs)


def _tree_once(df):
    return df['parse'][df.index.get_level_values('i')==1]


class Subcorpus(Corpus):
    """
    Simply a renamed Corpus, fancy indeed!
    """
    def __init__(self, path, **kwargs):
        super().__init__(path, **kwargs)


@total_ordering
class File(Corpus):

    def __init__(self, path, root=None, container=None, **kwargs):
        self.path = path
        self.name = os.path.basename(path)
        self.no_ext, self._ext = os.path.splitext(os.path.basename(self.name))
        self.files = None
        self.subcorpora = None
        self.container = container
        self.root = root
        self.nlp = None
        self.is_parsed = self.name.strip().endswith(('.conll', '.conllu'))

    def __eq__(self, other):
        self.name == getattr(other, 'name', other)

    def __lt__(self, other):
        self.name < getattr(other, 'name', other)

    def __ne__(self, other):
        return not self == other

    def to_df(self, **kwargs):
        if not self.is_parsed:
            raise NotImplementedError('Needs to be parsed.')
        return _to_df(self, **kwargs)

    def load(self, spacy=False, language='en', **kwargs):
        if spacy:
            self.nlp = _get_nlp(language=language)
        if self.is_parsed and not spacy:
            return self.to_df(**kwargs)
        with open(self.path, 'r') as fo:
            text = fo.read()
        # get the raw text from conll
        if self.is_parsed:
            output = list()
            for line in text.splitlines():
                if not line.startswith('# text = '):
                    continue
                line = line.replace('# text = ', '')
                output.append(line)
            text = '\n'.join(i for i in output)
        if not spacy:
            return text
        return self.nlp(text)

    def read(self, **kwargs):
        return open(self.path, 'r').read()

    def __repr__(self):
        parsed = 'parsed' if self.is_parsed else 'unparsed'
        form = [super().__repr__().rstrip('>'), self.no_ext, parsed]
        return '{} ({}, {})>'.format(*form)


def get_short_name_from_long_name(longname):
    revers = dict()
    for k, vs in LONG_NAMES.items():
        for v in vs:
            revers[v] = k
    return revers.get(longname, longname)


class Value(object):

    def __init__(self, corpus, column, inverse=False):
        self.corpus = corpus
        self.column = get_short_name_from_long_name(column)
        self.inverse = inverse
        self.all = set(self.corpus[self.column].unique())

    def __call__(self, entry):
        bool_ix = self.corpus[self.column].astype(object).str.lower() == entry.lower()
        return self.corpus[bool_ix] if not self.inverse else self.corpus[~bool_ix]

    def __getattr__(self, entry):
        return Value(self.corpus, self.column)(entry=entry)


class Slicer(object):

    def __init__(self, corpus, inverse=False):
        self.corpus = corpus
        self.inverse = inverse

    def __getattr__(self, attrib):
        return Value(self.corpus, attrib, inverse=self.inverse)


class Grouper(object):

    def __init__(self, corpus, value_mode=False):
        self.corpus = corpus
        self.value_mode = value_mode

    def __call__(self, attr):
        if attr in ['file', 's', 'i']:
            if self.value_mode:
                kwa = dict(self.corpus.get_level_values(attr))
            else:
                kwa = dict(level=[attr])
        else:
            if self.value_mode:
                kwa = dict(self.corpus[attr])
            else:
                kwa = dict(by=[attr])
        return self.corpus.groupby(**kwa)

    def __getattr__(self, attr):
        if attr == 'values':
            return Grouper(self.corpus, value_mode=True)
        return self(attr)

    def sentences(self):
        return self.corpus.groupby(level=['file', 's'])


class LoadedCorpus(pd.DataFrame, Corpus):
    """
    A corpus in memory
    """
    _internal_names = pd.DataFrame._internal_names
    _internal_names_set = set(_internal_names)

    _metadata = ['reference', 'just', 'skip', 'storage']
    reference = None
    storage = dict()
    extra = []

    @property
    def _constructor(self):
        return LoadedCorpus

    def __init__(self, data, **kwargs):
        if isinstance(data, str):
            if os.path.isfile(data):
                data = File(data).load()
            elif os.path.isdir(data):
                data = Corpus(data).load()
        super().__init__(data, **kwargs)
        # ???
        LoadedCorpus.reference = self

        self.just = Slicer(self)
        self.skip = Slicer(self, inverse=True)
        self.by = Grouper(self)

    def __len__(self):
        return self.shape[0]

    def load(self, *args, **kwargs):
        return self


class Results(pd.Series, LoadedCorpus):
    """
    Search results, a record of matching tokens in a Corpus
    """
    patched = ['table', 'conc', 'concordance', '_df']
    _internal_names = pd.Series._internal_names
    _internal_names_set = set(_internal_names)

    _metadata = ['reference']

    @property
    def _constructor(self):
        return Results

    @property
    def _constructor_expanddim(self):
        return Frequencies

    def __getitem__(self, item):
        try:
            row = pd.Series.__getitem__(self, item)
            return self.reference.loc[row.index]
        except (ValueError, KeyError):  # the series doesn't have it
            return self.reference.loc[self.index][item]

    def __getattr__(self, attr):
        try:
            row = pd.Series.__getattr__(self, attr)
            return self.reference.loc[row.index]
        except ValueError:  # the series doesn't have it
            return getattr(self.reference.loc[self.index], attr)

    def __repr__(self):
        return pd.DataFrame(self._df()).__repr__()

    def __bool__(self):
        return bool(len(self))

    def __nonzero__(self):
        return bool(len(self))

    def _df(self):
        try:
            return self.reference.loc[self.index]
        except:
            pass
        self = self.astype(object)
        return _set_best_data_types(self)

    def keywords(self, *args, **kwargs):
        return _keywords(self, *args, **kwargs)

    def conc(self, *args, **kwargs):
        """
        short name only
        """
        return self.concordance(*args, **kwargs)

    def table(self, *args, **kwargs):
        """
        Table view of results
        """
        return _table(self, *args, **kwargs)

    def tabview(self, *args, **kwargs):
        return _tabview(self, *args, **kwargs)

    def sort(self, *args, **kwargs):
        from .views import _sort
        return _sort(self, *args, **kwargs)

    def concordance(self, *args, **kwargs):
        from .results import _concordance
        return _concordance(self, *args, **kwargs)


class Frequencies(pd.DataFrame):
    """
    A corpus in memory
    """
    _internal_names = pd.DataFrame._internal_names + ['reference']
    _internal_names_set = set(_internal_names)

    _metadata = ['reference', 'path', 'name']

    def __init__(self, data, reference=None, **kwargs):
        super().__init__(data, **kwargs)
        self.reference = reference

    @property
    def _constructor(self, **kwargs):
        return Frequencies

    def keywords(self, *args, **kwargs):
        return _keywords(self, *args, **kwargs)

    def tabview(self, *args, **kwargs):
        return _tabview(self, *args, **kwargs)

    def sort(self, *args, **kwargs):
        from .views import _sort
        return _sort(self, *args, **kwargs)


class Concordance(pd.DataFrame):
    """
    A corpus in memory
    """
    _internal_names = pd.DataFrame._internal_names + ['reference']
    _internal_names_set = set(_internal_names)

    _metadata = ['reference', 'path', 'name']

    def __init__(self, data, reference=None, **kwargs):
        super().__init__(data, **kwargs)
        self.reference = reference

    @property
    def _constructor(self, **kwargs):
        return Concordance

    def keywords(self, *args, **kwargs):
        return _keywords(self, *args, **kwargs)

    def tabview(self, *args, **kwargs):
        return _tabview(self, *args, **kwargs)

    def sort(self, *args, **kwargs):
        from .views import _sort
        return _sort(self, *args, **kwargs)
