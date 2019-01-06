import pandas as pd
from nltk.tgrep import tgrep_compile

from .query import depgrep_compile

from .utils import maketree, _get_tqdm, _tqdm_update, _tqdm_close


class Searcher(object):
    """
    An engine for searching corpora
    """
    def __init__(self, corpus):
        # really hate this code...
        from .classes import File, Results, Corpus
        self.corpus = corpus
        # if we can't bring corpus into memory, we will use files
        if type(corpus) == Corpus and self.corpus.too_large_for_memory:
            print('Warning: corpus too large for memory!')
            self.to_search = corpus.files
            self.reference = None
            return
        # if corpus is unloaded or a file, load it
        if type(corpus) in {File, Corpus}:
            self.corpus = corpus.load()
            self.reference = self.corpus  # .copy()
        # if it's results, use the reference of that
        elif type(corpus) == Results:
            self.corpus = corpus._df()
            self.reference = corpus.reference
        # if it's just a dataframe, we can guess...
        elif isinstance(corpus, pd.DataFrame):
            self.reference = corpus
        self.to_search = [self.corpus]

    def tgrep_searcher(self, countmode=False, multiprocess=0):
        """
        Search a DataFrame using tgrep.
        """
        df = self.corpus
        df['_gram'] = False

        if isinstance(self.query, (str, bool)):
            self.query = tgrep_compile(self.query)

        if self.corpus.is_loaded():
            tqdm = _get_tqdm()

        tree_once = self.corpus.tree_once()
        if isinstance(tree_once.values[0], str):
            tree_once = tree_once.apply(maketree)

        ser = list()
        six = list()

        if self.corpus.is_loaded():
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
            if self.corpus.is_loaded():
                running_count += match_count
                kwa = dict(results=format(running_count, ','))
                t.set_postfix(**kwa)
                t.update()

        if self.corpus.is_loaded():
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
        Return bool index for match/no match for each token in this piece
        """
        if not isinstance(piece, pd.DataFrame):
            piece = piece.load()

        if self.target in piece.index.names:
            piece[self.target] = piece.index.get_level_values(self.target)

        num_query = self.target in {'i', 'g', 'sent_len'}

        # dependency search
        if self.target == 'd':
            # make multiindex and add an _n column, then remove old index
            df = piece.drop(['_n', 'file', 's', 'i'], axis=1, errors='ignore')
            df['_n'] = range(len(df))
            df = df.reset_index()
            self.query = depgrep_compile(self.query, df=df, case_sensitive=self.case_sensitive)
            bool_ix = self.depgrep(piece)
        # tree search
        elif self.target == 't':
            bool_ix = self.tgrep_searcher()
        # numerical query
        elif num_query:
            bool_ix = self.number_query(piece, self.target, self.query)['w']
        # anything else
        else:
            bool_ix = piece[self.target].str.contains(self.query, case=self.case_sensitive, regex=self.regex)
            # invert if we want to
            if self.inverse:
                bool_ix = ~bool_ix
        return piece['_n'][bool_ix]

    def depgrep(self, df):
        """
        Run query over dependencies
        """
        from .classes import LoadedCorpus, Results
        # get the full dataframe
        if type(self.corpus) == Results:
            df = self._df()
        elif type(self.corpus) == LoadedCorpus:
            df = self.corpus

        # create progress bar
        if self.corpus.is_loaded():
            tqdm = _get_tqdm()
            prog_bar_info = dict(desc='Searching loaded corpus',
                                 unit='tokens',
                                 ncols=120)
            tqdm.pandas(**prog_bar_info)

            matches = df.progress_apply(self.query, axis=1)
        # when corpus is not loaded, no progress bar?
        else:
            matches = df.apply(self.query, axis=1)

        try:
            matches = matches.fillna(False)
        except:
            pass

        bools = [bool(i) for i in matches.values]
        return bools

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

        # just load the target column coz we are bad ass
        usecols = ['file', 's', 'i', target]

        tqdm = _get_tqdm()
        kwa = dict(total=len(self.to_search),
                   desc='Searching corpus',
                   position=multiprocess,
                   ncols=120,
                   unit='document')
        simple = self.target not in {'t', 'd'}
        t = tqdm(**kwa) if len(self.to_search) > 1 and simple else None

        for piece in self.to_search:
            if isinstance(piece, File):
                piece = piece.load()
            res = self.query_a_piece(piece, usecols)
            if not res.empty:
                results.append(res)
            _tqdm_update(t)
        _tqdm_close(t)

        from .classes import Results
        if not results:
            print('No results, sorry.')
            results = Results()
        else:
            results = pd.concat(results, sort=False)
            results = Results(results)
        results.reference = self.reference
        return results
