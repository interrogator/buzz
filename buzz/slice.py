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
from .utils import _ensure_list_of_short_names, _get_short_name_from_long_name


class Filter(object):
    """
    Filterer for DF like objects
    """

    def __init__(self, corpus, column, inverse=False):
        """
        Unlike other slices, we can't have multiple columns here
        """
        if isinstance(column, (list, set)):
            problem = "Can only past str/length 1 iterable here: {}".format(column)
            assert len(column) == 1, problem
            column = list(column)[0]
        self.column = _get_short_name_from_long_name(column)
        self.inverse = inverse
        self._corpus = corpus

    def _make_column_to_match_against(self, case):
        """
        Get a stringified column from the dataset
        """
        if self.column in self._corpus.columns:
            strung = self._corpus[self.column].astype(str)
        else:
            index_data = self._corpus.index.get_level_values(self.column).astype(str)
            strung = pd.Series(index_data, index=self._corpus.index)
        if not case:
            strung = strung.str.lower()
        return strung

    @staticmethod
    def _normalise_entry(entry, case):
        """
        Lowercase the search text and normalise to set if need be
        """
        if case:
            return entry
        if isinstance(entry, (set, list)):
            return {i.lower() for i in entry}
        else:
            return entry.lower()

    def _make_bool_index(self, entry, strung, exact_match, **kwargs):
        """
        Get a boolean index of matches for this entry over strung
        """
        if isinstance(entry, (set, list)):
            if exact_match:
                return strung.isin(entry)
            return strung.apply(lambda x: any(i in x for i in entry))
        if not kwargs.get("regex") and exact_match:
            return strung == entry
        search_method = strung.str.match if exact_match else strung.str.contains
        return search_method(entry, **kwargs)

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

        strung = self._make_column_to_match_against(case)
        entry = self._normalise_entry(entry, case)
        bool_ix = self._make_bool_index(entry, strung, kwargs)

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
            except Exception:
                raise NotImplementedError("Not done yet.")
        else:
            entry = _ensure_list_of_short_names(entry)
        if not isinstance(self._corpus, pd.DataFrame):
            if isinstance(self.column, str):
                self.column = [self.column]
            self.column = (
                self.column if isinstance(self.column, list) else [self.column]
            )
            usecols = entry + self.column
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
        show = _ensure_list_of_short_names(show)
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
        col = _ensure_list_of_short_names(col)
        for i in col:
            if i not in self._valid:
                raise ValueError(f"Invalid name(s): {col}")
        # use the custom data grabber for this kind of slicer.
        return self._grab(col)

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
