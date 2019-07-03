from collections import OrderedDict

from .corpus import Corpus


class Workspace:
    """
    Idea: store the corpus once to save memory here, keeping all searches to just indices
    """

    def __init__(self, path_or_corpus):
        if isinstance(path_or_corpus, str):
            path_or_corpus = Corpus(path_or_corpus)
        self.corpus = path_or_corpus.load()
        self.results = OrderedDict()

    def search(self, *args, **kwargs):
        if (args, kwargs) in self.results:
            return self.corpus.loc[self.results[(args, kwargs)]]
        result = self.corpus.search(*args, **kwargs)
        index = result.index
        self.results[(args, kwargs)] = index

    def most_recent(self):
        return self.corpus.loc[self.results[-1]]
