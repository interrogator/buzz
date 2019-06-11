import pandas as pd
from nltk.tgrep import tgrep_compile

from .query import depgrep_compile

from .utils import _make_tree, _get_tqdm, _tqdm_update, _tqdm_close, _tree_once


class Searcher(object):
    """
    An engine for searching corpora
    """

    def __init__(self, corpus):
        """
        Searcher understands Corpus, File and Dataset
        """
        from .file import File
        from .corpus import Corpus
        from .dataset import Dataset

        self.corpus = corpus
        if type(corpus) == Corpus:
            self.to_search = self.corpus.files
            self.reference = None
        elif type(corpus) == File:
            self.to_search = [self.load()]
            self.corpus = self.load()
            self.reference = self.corpus.refence
        # if it's results, use the reference of that
        elif type(corpus) == Dataset:
            self.to_search = [self.corpus]
            self.reference = self.corpus.reference

    def _tgrep_iteration(self, df):
        """
        Search a DataFrame-like object's parse column using tgrep.
        """
        df['_gram'] = False
        tree_once = _tree_once(df)
        if isinstance(tree_once.values[0], str):
            tree_once = tree_once.apply(_make_tree)

        # results go here
        gram_column_strings, indices_to_keep = list(), dict()

        # progbar when possible
        if isinstance(self.corpus, pd.DataFrame):
            tqdm = _get_tqdm()
            running_count = 0
            t = tqdm(total=len(tree_once), desc='Searching trees', ncols=120, unit='tree')

        for n, tree in tree_once.iteritems():
            if not tree:
                continue
            match_count = 0
            # a tree is a bunch of positions. we iterate over each and check for match there
            root_positions = tree.treepositions(order='leaves')
            positions = tree.treepositions()
            for position in positions:
                if self.query(tree[position]):
                    match_count += 1
                    size = len(tree[position].leaves())  # how long is match for _gram
                    first = tree[position].treepositions('leaves')[0]
                    first = position + first
                    pos = root_positions.index(first)
                    gram = list()
                    form = ','.join([str(x) for x in range(pos + 1, pos + size + 1)])

                    for x in range(pos + 1, pos + size + 1):
                        indices_to_keep[(n[0], n[1], x)] = form

            # progress bar stuff for df
            if isinstance(self.corpus, pd.DataFrame):
                running_count += match_count
                kwa = dict(results=format(running_count, ','))
                t.set_postfix(**kwa)
                t.update()

        _tqdm_close(t)

        # df of _gram
        return pd.Series(indices_to_keep)

    def depgrep(self, df):
        """
        Run query over dependencies
        """
        # create progress bar
        if isinstance(df, pd.DataFrame):
            tqdm = _get_tqdm()
            prog_bar_info = dict(desc='Searching loaded corpus', unit='tokens', ncols=120)
            tqdm.pandas(**prog_bar_info)
            matches = df.progress_apply(self.query, axis=1)
        # when corpus is not loaded, no progress bar?
        else:
            matches = df.apply(self.query, axis=1)

        try:
            matches = matches.fillna(False)
        except Exception:  # todo: why?
            pass

        return [bool(i) for i in matches.values]

    def _depgrep_iteration(self, piece):
        """
        depgrep over one piece of data, returning the matching lines
        """
        # make multiindex and add an _n column, then remove old index
        df = piece.drop(['_n', 'file', 's', 'i'], axis=1, errors='ignore')
        df['_n'] = range(len(df))
        df = df.reset_index()
        # comppile the query against this dataframe
        self.query = depgrep_compile(self.query, df=df, case_sensitive=self.case_sensitive)
        # run the query, returning a boolean index
        bool_ix = self.depgrep(piece)
        # get just the lines matching the bool ix
        return bool_ix

    def run(self, target, query, case_sensitive=True):
        """
        Search either trees or dependencies for query

        Return: Dataset of matching indices
        """
        from .file import File
        from .dataset import Dataset

        self.target = target
        self.query = query
        self.case_sensitive = case_sensitive

        # where we store our results...
        results = list()

        # unlike depgrep, tgrep queries are compiled without the file data, so can be done once
        if target == 't':
            self.query = tgrep_compile(query)

        # progbar stuff
        tqdm = _get_tqdm()
        kwa = dict(total=len(self.to_search), desc='Searching corpus', ncols=120, unit='document')
        t = tqdm(**kwa) if len(self.to_search) > 1 else None

        # iterate over searchable bits, doing query with progbar
        for piece in self.to_search:
            if isinstance(piece, File):
                piece = piece.load()
            # do the dep or tree searches and make a reduced dataset containing just matches
            if self.target == 'd':
                res = piece[self._depgrep_iteration(piece)]
            elif self.target == 't':
                gram_ser = self._tgrep_iteration(piece)
                res = piece.loc[gram_ser.index]
                res['_gram'] = gram_ser

            if not res.empty:
                results.append(res)
            _tqdm_update(t)
        _tqdm_close(t)

        results = Dataset(pd.concat(results, sort=False)) if results else Dataset(pd.DataFrame())
        # if we already had reference corpus, it can stay...
        results.reference = self.reference
        return results
