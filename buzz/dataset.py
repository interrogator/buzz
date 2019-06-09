import os

import pandas as pd

from .slice import Just, Skip, See
from .views import _tabview

class Dataset(pd.DataFrame):
    """
    A corpus or corpus subset in memory
    """
    _internal_names = pd.DataFrame._internal_names
    _internal_names_set = set(_internal_names)

    _metadata = ['reference', '_metadata_path']
    reference = None

    @property
    def _constructor(self):
        return Dataset

    def __init__(self, data, **kwargs):
        if isinstance(data, str):
            if os.path.isfile(data):
                data = File(data).load()
            elif os.path.isdir(data):
                from .corpus import Corpus
                data = Corpus(data).load()
        super().__init__(data, **kwargs)

    def __len__(self):
        """
        Number of rows
        """
        return self.shape[0]

    def tgrep(self, *args, **kwargs):
        """
        Search constituency parses using tgrep
        """
        pass

    def depgrep(self, *args, **kwargs):
        """
        Search dependenciess using depgrep
        """
        pass

    def conc(self, *args, **kwargs):
        """
        Generate a concordance for each row
        """
        pass

    def view(self, *args, **kwargs):
        """
        View interactvely with tabview
        """
        return _tabview(self, *args, **kwargs)
