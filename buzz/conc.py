import pandas as pd
from .views import _tabview

class Concordance(pd.DataFrame):
    """
    A dataframe holding left, match and right columns, plus optional metadata
    """
    def view(self, *args, **kwargs):
        return _tabview(self, *args, **kwargs)
