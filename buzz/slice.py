"""
DataFrame namespace additions

df can usually be LoadedCorpus or Results
column is short or long name like l, lemma, lemmata

df.find.column.name: very simple search, same as 'just'
df.find.column(regex): search column by regex
df.see.column(): value_counts for this column
df.see.column.by.column: make table
df.just.column.name: filter a df to just matching
df.just.column(regex): same as above but allow regex, kwargs
df.skip.column.name: remove matching rows
df.skip.column(regex); same as above but allow regex

You can string these together however you like:

corpus.just.speaker.MOOKIE.skip.xpos.PUNCT.see.lemma.by.wordclass

"""

from abc import ABC, abstractmethod
import pandas as pd
from .utils import _get_short_name_from_long_name
from .search import Searcher


class Filter(object):
    """
    Filterer for DF like objects
    """
    def __init__(self, df, column, inverse=False):
        self._df = df
        self.column = column
        self.inverse = inverse

    def __call__(self, entry, *args, **kwargs):
        strung = self._df[self.column].astype(str)
        bool_ix = strung.str.match(entry, *args, **kwargs)
        if self.inverse:
            bool_ix = ~bool_ix
        return self._df[bool_ix]

    def __getattr__(self, entry):
        return self.__call__(entry)


class Interim(Filter):
    """
    Interim getter

    result.view.column
    """
    @property
    def by(self):
        """
        result.view.x.by.y
        """
        return Interim(self._df, self.column)

    def __call__(self, entry=None, *args, **kwargs):
        if not entry:
            return self._df[self.column].value_counts()
        return self._df.table(self.column, entry, *args, **kwargs)


class Finder(Filter):
    """
    Interim for searching

    corpus.find.lemmata('^[abc]')
    """
    def __call__(self, *args, **kwargs):
        return Searcher(self._df).run(self.column, *args, **kwargs)


class Slice(ABC):

    def __init__(self, df):
        self._df = df
        self._valid = list(self._df.columns)
        self._validate()

    def __getattr__(self, col):
        short = _get_short_name_from_long_name(col)
        if short not in self._valid:
            raise ValueError(f'Invalid name: {col}')
        return self._grab(short)

    @abstractmethod
    def _grab(self, *args, **kwargs):
        raise NotImplementedError()

    def _validate(self):
        # todo: ensure correct type?
        return


@pd.api.extensions.register_dataframe_accessor('just')
class Just(Slice):
    """
    LoadedCorpus.just.speakers.MOOKIE -- filter df
    """

    def _grab(self, colname, *args):
        return Filter(self._df, colname)

@pd.api.extensions.register_dataframe_accessor('skip')
class Skip(Slice):
    """
    LoadedCorpus.skip.speakers.MOOKIE -- filter df
    """

    def _grab(self, colname, *args):
        return Filter(self._df, colname, inverse=True)

@pd.api.extensions.register_dataframe_accessor('see')
class See(Slice):
    """
    results.see.lemma.by.speaker: make table
    """
    def _grab(self, colname):
        return Interim(self._df, colname)


@pd.api.extensions.register_dataframe_accessor('find')
class Find(Slice):
    """
    corpus.find('l', regex)
    corpus.find.lemmata(regex)
    """
    def _grab(self, target):
        return Finder(self._df, target)

