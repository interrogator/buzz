import pandas as pd
from typing import Optional

from .views import _tabview, _sort


class Table(pd.DataFrame):
    """
    A dataframe with numerical datapoints
    """
    _internal_names = pd.DataFrame._internal_names + ['reference']
    _internal_names_set = set(_internal_names)

    _metadata = ['reference', 'path', 'name']

    def __init__(self, data, reference=None, **kwargs):
        super().__init__(data, **kwargs)
        self.reference = reference

    @property
    def _constructor(self):
        return Table

    def view(self, *args, **kwargs):
        return _tabview(self, *args, **kwargs)

    def sort(self, *args, **kwargs):
        return _sort(self, *args, **kwargs)

    def plot(self, *args, **kwargs):
        """
        Visualise this table
        """
        pass

    def relative(self, sort: Optional[str] = 'total'):
        """
        Give a relative frequency version of this
        """
        rel = (self.T * 100.0 / self.sum(axis=1)).T
        if self[list(self.columns)].equals(rel[list(self.columns)]):
            raise ValueError('This operation did not change the DataFrame. Already relative?')
        return _sort(rel, by=sort) if sort else rel
