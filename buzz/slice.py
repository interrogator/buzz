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

from .search import Searcher
from .utils import _get_short_name_from_long_name


class Filter(object):
    """
    Filterer for DF like objects
    """

    def __init__(self, corpus, column, inverse=False):
        self.column = _get_short_name_from_long_name(column)
        self.inverse = inverse
        self._corpus = corpus

    def __call__(self, entry, case=True, exact_match=False, **kwargs):
        """
        Accepts pd.series.str.contains kwargs: case, regex, etc.

        exact_match: match whole word, or just part of it
        """
        # if it's a corpus, do this in a loop over files
        if not isinstance(self._corpus, pd.DataFrame) and self._corpus.files:
            results = []
            for file in self._corpus.files:
                self._corpus = file.load()
                res = self.__call__(entry, case=case, exact_match=exact_match, **kwargs)
                results.append(res)
            return pd.concat(results)
        # if it's a file, load it now
        elif not isinstance(self._corpus, pd.DataFrame):
            self._corpus = self._corpus.load()

        # the remaining stuff
        if self.column in self._corpus.columns:
            strung = self._corpus[self.column].astype(str)
        else:
            index_data = self._corpus.index.get_level_values(self.column).astype(str)
            strung = pd.Series(index_data, index=self._corpus.index)

        if not case:
            if isinstance(entry, (set, list)):
                entry = {i.lower() for i in entry}
            else:
                entry = entry.lower()
            strung = strung.str.lower()

        if isinstance(entry, (set, list)):
            if exact_match:
                bool_ix = strung.isin(entry)
            else:
                bool_ix = strung.apply(lambda x: any(i in x for i in entry))
        else:
            # get the correct method --- if user wants exact match
            search_method = strung.str.match if exact_match else strung.str.contains
            if not kwargs.get("regex") and exact_match:
                bool_ix = strung == entry
            else:
                bool_ix = search_method(entry, **kwargs)

        if self.inverse:
            bool_ix = ~bool_ix

        return self._corpus[bool_ix]

    def __getattr__(self, entry):
        """
        data.just/skip.column.<entry>
        """
        return self.__call__(entry, regex=False, exact_match=True)


class Interim(Filter):
    """
    Interim getter

    df.see.column
    """

    @property
    def by(self):
        """
        df.see.x.by.y
        """
        return Interim(self._corpus, self.column)

    def __call__(self, entry=None, *args, **kwargs):
        if not entry:
            try:
                return self._corpus[self.column].value_counts()
            except:
                raise NotImplementedError("Not done yet.")
        else:
            entry = _get_short_name_from_long_name(entry)
        if not isinstance(self._corpus, pd.DataFrame):
            usecols = [entry, self.column]
            self._corpus = self._corpus.load(usecols=usecols)
        return self._corpus.table(subcorpora=self.column, show=entry, *args, **kwargs)


class Proto(Filter):
    """
    Interim getter

    dataset.prototypical.text.by.speaker
    """

    @property
    def by(self):
        """
        df.see.x.by.y
        """
        return Proto(self._corpus, self.column)

    @property
    def showing(self):
        return Proto(self._corpus, self.column)

    def __call__(self, show=["w"], top=10, n_top_members=-1, only_correct=True):
        if not isinstance(show, list):
            show = [show]
        show = [_get_short_name_from_long_name(i) for i in show]
        return self._corpus.prototypical(
            self.column,
            show=show,
            top=top,
            n_top_members=n_top_members,
            only_correct=only_correct,
        )


class Finder(Filter):
    """
    Interim for searching

    corpus.find.lemmata('^[abc]')
    """

    def __call__(self, *args, **kwargs):
        return Searcher(self._corpus).run(self.column, *args, **kwargs)


class Slice(ABC):
    def __init__(self, corpus):
        self._corpus = corpus
        self._valid = list(self._corpus.columns) + list(self._corpus.index.names)
        self._validate()

    def __getattr__(self, col):
        """
        <operation:> just, skip, see...
        gets ATTRIB in df.<operation>.ATTRIB
        """
        short = _get_short_name_from_long_name(col)
        if short not in self._valid:
            raise ValueError(f"Invalid name: {col}")
        # use the custom data grabber for this kind of slicer.
        return self._grab(short)

    @abstractmethod
    def _grab(self, *args, **kwargs):
        raise NotImplementedError()  # noqa

    def _validate(self):
        # todo: ensure correct type?
        return


@pd.api.extensions.register_dataframe_accessor("just")
class Just(Slice):
    """
    LoadedCorpus.just.speakers.MOOKIE -- filter df
    """

    def _grab(self, colname, *args):
        return Filter(self._corpus, colname)


@pd.api.extensions.register_dataframe_accessor("proto")
class Prototypical(Slice):
    """
    LoadedCorpus.just.speakers.MOOKIE -- filter df
    """

    def _grab(self, colname, *args):
        return Proto(self._corpus, colname)


@pd.api.extensions.register_dataframe_accessor("skip")
class Skip(Slice):
    """
    LoadedCorpus.skip.speakers.MOOKIE -- filter df
    """

    def _grab(self, colname, *args):
        return Filter(self._corpus, colname, inverse=True)


@pd.api.extensions.register_dataframe_accessor("see")
class See(Slice):
    """
    results.see.lemma.by.speaker: make table
    """

    def _grab(self, colname):
        return Interim(self._corpus, colname)
