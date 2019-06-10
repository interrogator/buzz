import os
from functools import total_ordering

from .corpus import Corpus
from .utils import _get_nlp, _to_df


@total_ordering
class File(Corpus):

    def __init__(self, path, **kwargs):
        self.path = path
        self.filename = os.path.basename(path)
        self.name = self.filename.split('.txt')[0]
        self.files = None
        self.subcorpora = None
        self.nlp = None
        self.is_parsed = self.filename.endswith(('.conll', '.conllu'))

    def __ne__(self, other):
        return not self == other

    def __iter__(self):
        in_memory = self.load() if self.is_parsed else self.read()
        return in_memory.__iter__()

    def to_spacy(self, language='en'):
        """
        get spaCy model of this file
        """
        self.nlp = _get_nlp(language=language)
        with open(self.path, 'r') as fo:
            text = fo.read().strip()
        # get the raw text from conll. horrible idea but no other way
        if self.is_parsed:
            pre = '# text = '
            lines = [i.replace(pre, '').strip() for i in text.splitlines() if i.startswith(pre)]
            text = ' '.join(i for i in lines)
            text = text.replace('  ', ' ')
        return self.nlp(text)

    def __len__(self):
        raise NotImplementedError('File has no length')

    def __bool__(self):
        return True

    def load(self, **kwargs):
        """
        For parsed dataset, get dataframe or spacy object
        """
        if self.is_parsed:
            return _to_df(self, **kwargs)
        raise NotImplementedError('Cannot load DataFame from unparsed file. Use file.read()')

    def read(self, **kwargs):
        """
        Get the file contents as string
        """
        with open(self.path, 'r') as fo:
            data = fo.read()
        return data
