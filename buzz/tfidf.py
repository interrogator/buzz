from collections import Counter, defaultdict

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from .utils import _get_tqdm, _make_match_col, _tqdm_close, _tqdm_update

tqdm = _get_tqdm()


def _tfidf_prototypical(df, column, show, n_top_members=-1, only_correct=True, top=-1):
    """
    Get prototypical instances over bins segmented by column
    """
    # make the language models
    if not isinstance(show, list):
        show = [show]

    if (column, tuple(show)) not in df._tfidf:
        df.tfidf_by(column, show=show, n_top_members=n_top_members)

    if n_top_members > 0:
        top_members = list(getattr(df, column).value_counts().index[:n_top_members])
        df = df[getattr(df, column).isin(top_members)]

    df["_formatted"] = _make_match_col(df, show, preserve_case=False)

    index = list()
    results = list()

    groupby = df.groupby(column)

    kwa = dict(ncols=120, unit="bin", desc="Scoring against models", total=len(groupby))
    t = tqdm(**kwa) if len(groupby) > 1 else None

    for _column_value, df_by_attr in groupby:
        for fsi, sent in df_by_attr.groupby(level=["file", "s"]):
            # note, the actions below are probably done twice. bad.
            text = sent.iloc[0].text
            form = " ".join(sent["_formatted"])
            scores = df.tfidf_score(column, show, sent)
            if column in sent.columns:
                actual = getattr(sent.iloc[0], column)
            else:
                actual = sent.index.get_level_values(column)[0]
            for binn, score in scores.items():
                if only_correct and binn != actual:
                    continue
                index.append((fsi[0], fsi[1], form, text, actual, binn))
                results.append(score)

        _tqdm_update(t)
    _tqdm_close(t)

    show = "/".join(show)
    names = ["file", "s", show, "text", "actual " + column, "guess " + column]
    index = pd.MultiIndex.from_tuples(index, names=names)
    results = pd.Series(results, index=index)
    if only_correct:
        reset = results.reset_index()
        bool_ix = reset["guess " + column] == reset["actual " + column]
        results = results[bool_ix.values]
        results.index = results.index.droplevel(-1)
        results.index.names = [i.replace("actual ", "") for i in results.index.names]
    results.name = "similarity"
    if top < 1:
        return results

    def _group_apply_sort_head(group):
        return group.sort_values(ascending=False).head(top)

    grouped = results.groupby(column, sort=False).apply(_group_apply_sort_head)
    grouped.index = grouped.index.droplevel(-1)
    return grouped


def _tfidf_score(df, column, show, text):
    key = (column, tuple(show))
    if key not in df._tfidf:
        df.tfidf_by(column, show=show)

    scores = dict()
    for k, (vec, features, show) in df._tfidf[key].items():
        if isinstance(text, str):
            if show != ["w"]:
                err = f'Input text can only be string when vector is ["w"], not {show}'
                raise ValueError(err)
            sents = [text]
        elif isinstance(text, list):
            sents = text
        else:
            sents = list()
            series = _make_match_col(text, show, preserve_case=False)
            for _, sent in series.groupby(level=["file", "s"]):
                sents.append(" ".join(sent))
        new_features = vec.transform(sents)
        scored = (features * new_features.T).A
        scores[k] = scored
        scores[k] = (sum(scored) / len(scored))[0]
    return Counter(scores)


def _tfidf_model(df, column, n_top_members=-1, show=["w"]):

    attr_sents = defaultdict(list)
    sents = list()

    if n_top_members > 0:
        top_members = list(getattr(df, column).value_counts().index[:n_top_members])
        df = df[getattr(df, column).isin(top_members)]

    # get dict of attr: [list, of, sents]
    df["_formatted"] = _make_match_col(df, show, preserve_case=False)

    groupby = (
        df.groupby(column) if column else df["_formatted"].groupby(level=["file", "s"])
    )

    kwa = dict(
        ncols=120, unit="bin", desc=f"Building {column} model", total=len(groupby)
    )
    t = tqdm(**kwa) if len(groupby) > 1 else None

    if column:
        for attr, df_by_attr in df.groupby(column):
            for _, sent in df_by_attr.groupby(level=["file", "s"]):
                attr_sents[attr].append(" ".join(sent["_formatted"]))
            _tqdm_update(t)

    else:
        for _, sent in df["_formatted"].groupby(level=["file", "s"]):
            sents.append(" ".join(sent))
            _tqdm_update(t)
        attr_sents["_base"] = sents

    _tqdm_close(t)

    # for each database, make a vector
    vectors = dict()
    for attr, sents in attr_sents.items():
        vec = TfidfVectorizer()
        vec.fit(sents)
        features = vec.transform(sents)
        vectors[attr] = (vec, features, show)

    # little hack when there are no columns
    if not column:
        vectors = vectors["_base"]

    return vectors
