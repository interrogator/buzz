import re
from collections import MutableSequence


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

    @staticmethod
    def _no_ext_name(name):
        """
        Get name without extension
        """
        return name.rsplit('.', 1)[0]

    @staticmethod
    def _try_to_get_same(name):
        return next((i for i in self.list if self._no_ext_name(i.name) == attr), None)     

    def __getattr__(self, attr):
        """
        Attribute style access to subcorpora/files, preferring former
        """
        found = self._try_to_get_same(attr)
        if found:
            return found
        raise AttributeError(f'No attribute: {attr}')

    def __getitem__(self, i):
        """
        dict style lookup of files
        """
        if isinstance(i, int):
            return self.list[i]

        if isinstance(i, str):
            found = self._try_to_get_same(i)
            if found:
                return found
            raise KeyError(f'No such file: {i}')

        # allow user to pass in a regular expression and get all matching names
        if isinstance(i, re._pattern_type):
            matches = [s for s in self.list if re.search(i, self._no_ext_name(s.name))]
            return Contents(matches)

        # normal indexing and slicing
        if isinstance(i, slice):
            return Contents(self.list[i])

        return Contents(self.list[i])

    def __delitem__(self, i):
        del self.list[i]

    def __setitem__(self, i, v):
        self.list[i] = v

    def insert(self, i, v):
        self.list.insert(i, v)
