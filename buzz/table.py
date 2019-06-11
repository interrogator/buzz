import pandas as pd
from typing import Optional

from .views import _tabview, _sort, _simple_relative


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
        return _tabview(self, self.reference, *args, **kwargs)

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
        rel = _simple_relative(self)
        return _sort(rel, by=sort) if sort else rel
