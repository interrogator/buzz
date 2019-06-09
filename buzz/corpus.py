import os
from collections import MutableSequence

import pandas as pd

from .parse import Parser
from .dataset import Dataset
from .utils import (_to_df,
                    _get_nlp,
                    _strip_metadata,
                    _set_best_data_types,
                    _get_tqdm,
                    _tqdm_close,
                    _tqdm_update,
                    _tree_once,
                    _make_tree)


tqdm = _get_tqdm()



class Corpus(MutableSequence):
    """
    Model a collection of plain text or CONLL-U files.
    """
    def __init__(self, path=None):
        """
        Initialise the corpus, deteremine if parsed, hook up methods
        """
        path = os.path.expanduser(path)
        if not os.path.isdir(path):
            raise ValueError(f'Not a valid path: {path}')
        self.path = path
        self._metadata_path = os.path.join(self.path, '.metadata.json')
        self.name = os.path.basename(path)
        self.subcorpora, self.files, self.is_parsed = self._get_subcorpora_and_files()
        self.filepaths = Contents([i.path for i in self.files])
        self.nlp = None

    def is_loaded(self):
        """
        Return whether or not the corpus is loaded in memory
        """
        return type(self) == Dataset

    @property
    def metadata(self):
        """
        Metadata dict for this corpus. Generate if it's not there
        """
        if not os.path.isfile(self._metadata_path):
            return self._generate_metadata()
        with open(self._metadata_path, 'r') as fo:
            return json.load(fo)

    def _generate_metadata(self):
        """
        Create, store and return the metadata for this corpus
        """
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
        self.add_metadata(**meta)
        return meta

    def add_metadata(self, **pairs):
        """
        Add key-value pairs to metadata for this corpus

        Return the complete metadata dict
        """
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
            not_there = must_exist - pairs.keys()
            raise ValueError('Fields must exist: {}'.format(not_there))
        with open(self._metadata_path, 'w') as fo:
            json.dump(pairs, fo, sort_keys=True, indent=4, separators=(',', ': '))
        return self.metadata

    def parse(self,
              parser: str = 'spacy',
              cons_parser: str = 'benepar',
              language: str = 'english',
              **kwargs):
        """
        Parse a plaintext corpus
        """
        parsed_path = self.path + '-parsed'
        if os.path.isdir(parsed_path) or self.path.endswith(('-parsed', 'conll', 'conllu')):
            raise ValueError('Corpus is already parsed.')
        self.parser = Parser(self, parser=parser, cons_parser=cons_parser, language=language)
        return self.parser.run(self, **kwargs)

    def load(self, spacy: bool = False, combine: bool = False, load_trees: bool = False, **kwargs):
        """
        Load a Corpus into memory.

        spacy: also load the spacy model
        """

        # progress indicator
        kwa = dict(ncols=120,
                   unit='file',
                   desc='Loading',
                   total=len(self))
        t = tqdm(**kwa) if len(self) > 1 else None

        # load each file and add to list, indicating progress
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
            self.nlp = _get_nlp(language='en')
            loaded = _strip_metadata('\n'.join(loaded))
            return self.nlp(loaded)

        # for parsed corpora, we merge each file contents into one huge dataframe as LoadedCorpus
        if self.is_parsed:
            df = pd.concat(loaded, sort=False)
            if load_trees:
                tree_once = _tree_once(df)
                if isinstance(tree_once.values[0], str):
                    df['parse'] = tree_once.apply(_make_tree)

            df = df.drop('_n', axis=1, errors='ignore')
            col_order = list(df.columns)
            df['_n'] = range(len(df))
            df = df[col_order + ['_n']]
            df = _set_best_data_types(df)
            return Dataset(self._order_columns(df))
        # for unparsed corpora, we give a dict of {path: text}
        else:
            from collections import OrderedDict
            return OrderedDict(sorted(zip(self.filepaths, loaded)))

    def _prepare_spacy(self, language='en'):
        """
        Load NLP analysis component
        """
        

    def spacy(self, language='en', **kwargs):
        """
        Get spacy's model of the Corpus
        """
        return self.load(spacy=True, language=language, **kwargs)

    @staticmethod
    def _order_columns(df):
        """
        Put Corpus columns in best possible order. This means, follow CONLL-U, then metadata.
        At the end we add _n, a helper column that is just a range index
        """
        proper_order = CONLL_COLUMNS[1:]
        fixed = [i for i in proper_order if i in list(df.columns)]
        met = list(sorted([i for i in list(df.columns) if i not in proper_order]))
        met.remove('_n')
        if met:
            fixed += met
        return df[fixed + ['_n']]

    def _get_subcorpora_and_files(self):
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
                fpath = File(fpath)
                files.append(fpath)
            for directory in dirnames:
                if directory.startswith('.'):
                    continue
                directory = os.path.join(root, directory)
                directory = Subcorpus(directory)
                subcorpora.append(directory)
        subcorpora = Contents(list(sorted(subcorpora)))
        files = Contents(list(sorted(files)))
        if not files:
            is_parsed = self.name.endswith('-parsed')
        else:
            is_parsed = files[0].name.endswith(('conll', 'conllu'))
        return subcorpora, files, is_parsed



class Subcorpus(Corpus):
    """
    Simply a renamed Corpus, fancy indeed!
    """
    def __init__(self, path, **kwargs):
        super().__init__(path, **kwargs)

