import pandas as pd
from nltk.tgrep import tgrep_compile

from .query import depgrep_compile

from .utils import maketree

from tqdm import tqdm, tqdm_notebook
try:
    if get_ipython().__class__.__name__ == 'ZMQInteractiveShell':
        tqdm = tqdm_notebook
except:
    pass


class Searcher(object):
    """
    An engine for searching corpora
    """
    def __init__(self, corpus):
        # really hate this code...
        from .classes import File, Results, Corpus
        self.corpus = corpus
        if type(corpus) == Corpus and self.corpus.too_large_for_memory:
            self.to_search = corpus.files
            self.reference = None
            self.corpus.is_loaded = False
            return
        if type(corpus) in {File, Corpus}:
            self.corpus = corpus.load()
            self.reference = corpus.copy()
        elif type(corpus) == Results:
            self.corpus = corpus._df()
            self.reference = corpus.reference
        elif isinstance(corpus, pd.DataFrame):
            self.reference = corpus.copy()
        self.to_search = [corpus]
        self.corpus.is_loaded = True

    def tgrep_searcher(self, countmode=False, multiprocess=0):
        """
        Search a DataFrame using tgrep.
        """
        df = self.corpus
        df['_gram'] = False

        if isinstance(self.query, (str, bool)):
            self.query = tgrep_compile(self.query)

        if self.corpus.is_loaded:
            from tqdm import tqdm, tqdm_notebook
            try:
                if get_ipython().__class__.__name__ == 'ZMQInteractiveShell':
                    tqdm = tqdm_notebook
            except:
                pass

        tree_once = self.corpus.tree_once()
        if isinstance(tree_once.values[0], str):
            tree_once = tree_once.apply(maketree)

        ser = list()
        six = list()

        if self.corpus.is_loaded:
            running_count = 0
            t = tqdm(total=len(tree_once),
                     desc='Searching trees',
                     position=multiprocess,
                     ncols=120,
                     unit='tree')

        # broken
        # should do dropna or whatever on this
        for n, tree in tree_once.iteritems():
            if not tree:
                continue
            match_count = 0
            root_positions = tree.treepositions(order='leaves')
            positions = tree.treepositions()
            for position in positions:
                if self.query(tree[position]):
                    match_count += 1
                    size = len(tree[position].leaves())
                    first = tree[position].treepositions('leaves')[0]
                    first = position + first
                    pos = root_positions.index(first)
                    form = ','.join([str(x) for x in range(pos+1, pos+size+1)])
                    ser.append(form)
                    six.append(n+pos)
            if self.corpus.is_loaded:
                running_count += match_count
                kwa = dict(results=format(running_count, ','))
                t.set_postfix(**kwa)
                t.update()

        if self.corpus.is_loaded:
            t.close()

        df = df.iloc[six].copy()
        df['_gram'] = ser
        return df[['w', '_gram']]
        return df

    @staticmethod
    def number_query(df, target, query):
        op, x = getattr(query, 'pattern', query).strip().split(' ', 1)
        op_no_negation = op.lstrip('!')
        try:
            x = float(x)
        except:
            pass
        if op_no_negation in {'=', '=='}:
            crit = df[target] == x
        if op_no_negation == '<':
            crit = df[target] < x
        if op_no_negation == '<=':
            crit = df[target] <= x
        if op_no_negation == '>':
            crit = df[target] > x
        if op_no_negation == '>=':
            crit = df[target] >= x
        # invert if negation
        if op.startswith('!'):
            return ~crit
        return crit

    def query_a_piece(self, piece, usecols):
        """
        Return bool index
        """
        if not isinstance(piece, pd.DataFrame):
            piece = piece.load(usecols=usecols)

        if self.target in piece.index.names:
            piece[self.target] = piece.index.get_level_values(self.target)

        num_query = self.target in ['i', 'g', 'sent_len']

        # build dep searcher if need be
        if self.target == 'd':
            self.query = depgrep_compile(self.query, df=piece, case_sensitive=self.case_sensitive)
            bool_ix = self.depgrep(piece) #piece=piece

        # do tgrep
        if self.target == 't':
            bool_ix = self.tgrep_searcher()

        elif num_query:
            bool_ix = self.number_query(piece, self.target, self.query)['w']
        else:
            bool_ix = piece[self.target].str.contains(self.query, case=self.case_sensitive, regex=self.regex)
            if self.inverse:
                bool_ix = ~bool_ix
        bool_ix = bool_ix.fillna(False)
        return piece['w'][bool_ix]

    def depgrep(self, df):
        from .classes import LoadedCorpus, Results
        if type(self.corpus) == Results:
            df = self._df()
        elif type(self.corpus) == LoadedCorpus:
            df = self.corpus

        df = self.corpus

        if isinstance(self.query, str):
            self.query = depgrep_compile(self.query, df=df, case_sensitive=self.case_sensitive)

        # make multiindex and add an _n column, then remove old index
        if not isinstance(df.index, pd.MultiIndex):
            df = df.set_index(['file', 's', 'i'])
            df = df.drop('_n', axis=1, errors='ignore')
            df['_n'] = range(len(df))
            df = df.drop('index', axis=1, errors='ignore')

        # create progress bar
        if self.corpus.is_loaded:
            try:
                if get_ipython().__class__.__name__ == 'ZMQInteractiveShell':
                    tqdm = tqdm_notebook()
            except:
                pass
            prog_bar_info = dict(desc="Searching loaded corpus",
                                 unit="tokens",
                                 ncols=120)
            tqdm.pandas(**prog_bar_info)

            matches = df.progress_apply(self.query, axis=1)
        # when corpus is not loaded, no progress bar?
        else:
            matches = df.apply(self.query, axis=1)

        # if we got a boolean index from our search, drop false
        if matches.dtypes.name == 'bool':
            try:
                return df[matches.values]
            except:
                return df.loc[matches]
        # if if wasn't boolean, it has nans to drop
        else:
            import numpy as np
            matches = matches.fillna(value=np.nan)
            return df.loc[matches.dropna().index]

    def run(self,
            target,
            query=False,
            multiprocess=False,
            case_sensitive=False,
            load=True,
            regex=True,
            inverse=False):

        from .classes import File

        if target.startswith('t') and inverse:
            raise NotImplementedError('Cannot do this yet')

        self.inverse = inverse
        self.regex = regex
        self.target = target
        self.case_sensitive = case_sensitive
        self.query = query

        reg = query.startswith('/') and query.endswith('/')
        sim = query.startswith(('"', "'")) and query.endswith(('"', "'"))

        if sim or reg:
            self.query = self.query[1:-1]

        if regex is not True:
            regex = True if reg else False

        if target == 't':
            self.query = tgrep_compile(query)

        results = list()
        pieces = list()

        # just load the target column coz we are bad ass
        usecols = ['file', 's', 'i', target]

        t = None
        if len(self.to_search) > 1 and self.target not in {'t', 'd'}:
            t = tqdm(total=len(self.to_search),
                     desc='Searching corpus',
                     position=multiprocess,
                     ncols=120,
                     unit='document')

        for piece in self.to_search:
            if isinstance(piece, File):
                piece = piece.load()
            pieces.append(piece)
            res = self.query_a_piece(piece, usecols)
            if not res.empty:
                results.append(res)
            if t is not None:
                t.update()
        if t is not None:
            t.close()

        from .classes import Results
        results = pd.concat(results, sort=False)
        results = Results(results)
        results.reference = self.reference
        return results
