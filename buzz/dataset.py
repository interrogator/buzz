import os

import pandas as pd

from .conc import _concordance
from .search import Searcher
from .slice import Just, Skip, See  # noqa: F401
from .views import _table, _tabview


class Dataset(pd.DataFrame):
    """
    A corpus or corpus subset in memory
    """

    _internal_names = pd.DataFrame._internal_names
    _internal_names_set = set(_internal_names)

    _metadata = ['reference']
    reference = None

    @property
    def _constructor(self):
        return Dataset

    def __init__(self, data, reference=None, **kwargs):
        if isinstance(data, str):
            if os.path.isfile(data):
                from .file import File

                data = File(data).load()
                reference = data
            elif os.path.isdir(data):
                from .corpus import Corpus

                data = Corpus(data).load()
                reference = data
        super().__init__(data, **kwargs)
        self.reference = reference

    def __len__(self):
        """
        Number of rows
        """
        return self.shape[0]

    def tgrep(self, query, **kwargs):
        """
        Search constituency parses using tgrep
        """
        searcher = Searcher(self)
        return searcher.run('t', query, **kwargs)

    def depgrep(self, query, **kwargs):
        """
        Search dependencies using depgrep
        """
        searcher = Searcher(self)
        return searcher.run('d', query, **kwargs)

    def conc(self, *args, **kwargs):
        """
        Generate a concordance for each row
        """
        return _concordance(self, self.reference, *args, **kwargs)

    def table(self, *args, **kwargs):
        return _table(self, *args, **kwargs)

    def view(self, *args, **kwargs):
        """
        View interactvely with tabview

        todo: reference?
        """
        return _tabview(self, *args, **kwargs)
