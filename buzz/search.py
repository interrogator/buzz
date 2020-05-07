import pandas as pd
from nltk.tgrep import tgrep_compile

from depgrep import depgrep_compile

from .utils import _get_tqdm, _make_tree, _tqdm_close, _tqdm_update, _tree_once


class Searcher(object):
    """
    An engine for searching corpora
    """

    def _understand_input_data(self, corpus):
        """
        Searcher understands Corpus, File and Dataset
        """
        from .file import File
        from .corpus import Corpus
        from .dataset import Dataset

        if type(corpus) == Corpus:
            to_search = corpus.files
            reference = None
        elif type(corpus) == File:
            corpus = corpus.load()
            to_search = [corpus]
            reference = corpus.reference
        # if it's results, use the reference of that
        elif type(corpus) == Dataset:
            to_search = [corpus]
            reference = corpus.reference

        return to_search, reference

    def _tgrep_iteration(self, df):
        """
        Search a DataFrame-like object's parse column using tgrep.
        """
        df["_gram"] = False
        tree_once = _tree_once(df)
        if isinstance(tree_once.values[0], str):
            tree_once = tree_once.apply(_make_tree)

        # results go here
        indices_to_keep = dict()

        # progbar when possible
        t = None
        if isinstance(self.corpus, pd.DataFrame):
            tqdm = _get_tqdm()
            running_count = 0
            t = tqdm(
                total=len(tree_once), desc="Searching trees", ncols=120, unit="tree"
            )

        for n, tree in tree_once.items():
            if not tree:
                continue
            match_count = 0
            # a tree is a bunch of positions. we iterate over each and check for match there
            root_positions = tree.treepositions(order="leaves")
            positions = tree.treepositions()
            for position in positions:
                if self.query(tree[position]):
                    match_count += 1
                    size = len(tree[position].leaves())  # how long is match for _gram
                    first = tree[position].treepositions("leaves")[0]
                    first = position + first
                    pos = root_positions.index(first)
                    form = ",".join([str(x) for x in range(pos + 1, pos + size + 1)])
                    for x in range(pos + 1, pos + size + 1):
                        indices_to_keep[(n[0], n[1], x)] = form

            # progress bar stuff for df
            if isinstance(self.corpus, pd.DataFrame):
                running_count += match_count
                kwa = dict(results=format(running_count, ","))
                t.set_postfix(**kwa)
                t.update()

        _tqdm_close(t)

        # df of _gram
        return pd.Series(indices_to_keep)

    def depgrep(self, df, positions, position=0):
        """
        Run query over dependencies
        """
        # create progress bar
        if isinstance(self.corpus, pd.DataFrame) and position is not None:
            tqdm = _get_tqdm()
            prog_bar_info = dict(
                desc="Searching loaded corpus",
                unit="tokens",
                ncols=120,
                position=position,
            )
            tqdm.pandas(**prog_bar_info)
            matches = df.progress_apply(self.query, axis=1, raw=True)
        # when corpus is not loaded, no progress bar
        else:
            matches = df.apply(self.query, axis=1, raw=True)

        try:
            matches = matches.fillna(False)
        except Exception:  # todo: why?
            pass

        return [bool(i) for i in matches.values]

    def _depgrep_iteration(self, piece, query, position):
        """
        depgrep over one piece of data, returning the matching lines
        """
        # make multiindex and add an _n column, then remove old index
        df = piece.drop(["_n", "file", "s", "i"], axis=1, errors="ignore")
        df["_n"] = range(len(df))
        df = df.reset_index(level=df.index.names)
        positions = {y: x for x, y in enumerate(list(df.columns))}
        values = df.values
        # compile the query against this dataframe
        self.query = depgrep_compile(
            query,
            values=values,
            positions=positions,
            case_sensitive=self.case_sensitive,
        )
        # run the query, returning a boolean index
        bool_ix = self.depgrep(df, positions, position=position)
        # get just the lines matching the bool ix
        return bool_ix

    def run(
        self, corpus, target, query, case_sensitive=True, inverse=False, position=0
    ):
        """
        Search either trees or dependencies for query

        Return: Dataset of matching indices
        """
        from .file import File
        from .dataset import Dataset

        self.corpus = corpus
        self.to_search, self.reference = self._understand_input_data(corpus)
        self.target = target
        self.query = query
        self.case_sensitive = case_sensitive

        name = getattr(corpus, "name", None)

        # where we store our results...
        results = list()

        # unlike depgrep, tgrep queries are compiled without the file data, so can be done once
        if target == "t":
            self.query = tgrep_compile(query)

        # progbar stuff
        tqdm = _get_tqdm()
        kwa = dict(
            total=len(self.to_search),
            desc="Searching corpus",
            ncols=120,
            unit="document",
        )
        t = tqdm(**kwa) if len(self.to_search) > 1 else None

        # iterate over searchable bits, doing query with progbar
        n = 0
        for piece in self.to_search:
            if isinstance(piece, File):
                piece = piece.load()
                piece["_n"] = list(range(n, len(piece) + n))
                n += len(piece)
            # do the dep or tree searches and make a reduced dataset containing just matches
            if self.target == "d":
                depg = self._depgrep_iteration(piece, query, position=position)
                res = piece[depg] if not inverse else piece[~depg]
            elif self.target == "t":
                gram_ser = self._tgrep_iteration(piece)
                res = piece.loc[gram_ser.index]
                res["_gram"] = gram_ser

            if not res.empty:
                results.append(res)
            _tqdm_update(t)
        _tqdm_close(t)

        results = (
            Dataset(pd.concat(results, sort=False), name=name)
            if results
            else Dataset(pd.DataFrame(), name=name)
        )
        # if we already had reference corpus, it can stay...
        results.reference = self.reference
        return results
