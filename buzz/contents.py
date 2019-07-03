import re
from collections import MutableSequence

import pandas as pd

from .utils import _order_df_columns


class Contents(MutableSequence):
    """
    Holder for ordered collections of files or subcorpora
    """

    def __init__(self, data=[]):
        self.list = data

    def __repr__(self):
        return str(self.list)

    def __len__(self):
        return len(self.list)

    def __bool__(self):
        return True if self.list else False

    def _try_to_get_same(self, name):
        return next((i for i in self.list if i.name == name), None)

    def __getattr__(self, attr):
        """
        Attribute style access to subcorpora/files, preferring former
        """
        found = self._try_to_get_same(attr)
        if found:
            return found
        raise AttributeError(f"No such attribute: {attr}")

    def __getitem__(self, i):
        """
        dict style lookup of files
        """

        if isinstance(i, str):
            found = self._try_to_get_same(i)
            if found:
                return found
            raise KeyError(f"No such object: {i}")

        # allow user to pass in a regular expression and get all matching names
        if isinstance(i, type(re.compile("x"))):
            return Contents([s for s in self.list if re.search(i, s.name)])

        # normal indexing and slicing
        if isinstance(i, slice):
            return Contents(self.list[i])

        # for int and potentially anything else?
        return self.list[i]

    def __delitem__(self, i):
        del self.list[i]

    def __setitem__(self, i, v):
        self.list[i] = v

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(f"Not same class: {self.__class__} vs {other.__class__}")
        if len(self) != len(other):
            return False
        return all(a == b for a, b in zip(self, other))

    def insert(self, i, v):
        if self and not isinstance(v, self[0].__class__):
            raise TypeError(f"Not same class: {self[0].__class__} vs {v.__class__}")
        self.list.insert(i, v)

    def load(self, **kwargs):
        loaded = []
        for piece in self:
            loaded.append(piece.load(**kwargs))
        df = pd.concat(loaded)
        df["_n"] = range(len(df))
        return _order_df_columns(df)
