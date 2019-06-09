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
        if not self.list:
            return 0
        return len(self.list)

    def __bool__(self):
        return True if self.list else False

    def __getattr__(self, name):
        """
        Attribute style access to subcorpora/files, preferring former
        """
        return next((i for i in self.list if i.no_ext == name), None)

    def __getitem__(self, i):
        to_iter = self.list
        if isinstance(i, str):
            # dict style lookup of files when there are no subcorpora
            return next((s for s in to_iter if s.name.rsplit('.', 1)[0] == i), None)

        from .corpus import Corpus
        # allow user to pass in a regular expression and get all matching names
        if isinstance(i, re._pattern_type):
            it = [s for s in to_iter if re.search(i, s.name.split('.', 1)[0])]
            return Corpus(it, path=self.path, name=self.name)
        # normal indexing and slicing
        if isinstance(i, slice):
            return Corpus(to_iter[i], path=self.path, name=self.name)
        return to_iter[i]

    def __delitem__(self, i):
        del self.list[i]

    def __setitem__(self, i, v):
        self.list[i] = v

    def insert(self, i, v):
        self.list.insert(i, v)
