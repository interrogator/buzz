import os
from functools import total_ordering

from .corpus import Corpus
from .utils import _get_nlp, _to_df


@total_ordering
class File(Corpus):

    def __init__(self, path, **kwargs):
        self.path = path
        self.name = os.path.basename(path)
        self.no_ext, self._ext = os.path.splitext(os.path.basename(self.name))
        self.files = None
        self.subcorpora = None
        self.nlp = None
        self.is_parsed = self.name.strip().endswith(('.conll', '.conllu'))

    def __eq__(self, other):
        self.name == getattr(other, 'name', other)

    def __lt__(self, other):
        self.name < getattr(other, 'name', other)

    def __ne__(self, other):
        return not self == other

    def to_df(self, **kwargs):
        """
        If parsed, return the dataframe with CONLL columns
        """
        if not self.is_parsed:
            raise NotImplementedError('Needs to be parsed.')
        return _to_df(self, **kwargs)

    def load(self, spacy=False, language='en', **kwargs):
        """
        For parsed dataset, get dataframe or spacy object 
        """
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
        """
        Get the file contents as string
        """
        with open(self.path, 'r') as fo:
            data = fo.read()
        return data

    def __repr__(self):
        parsed = 'parsed' if self.is_parsed else 'unparsed'
        rep = super().__repr__().rstrip('>')
        return f'{rep} ({self.no_ext}, {parsed})>'