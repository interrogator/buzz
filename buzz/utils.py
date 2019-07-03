import os
import re
import shlex
import shutil
from io import StringIO
from typing import List, Optional

import pandas as pd
from nltk.tree import ParentedTree
from tqdm import tqdm, tqdm_notebook

from .constants import COLUMN_NAMES, DTYPES, LONG_NAMES, MAX_SPEAKERNAME_SIZE


def _make_match_col(df, show, preserve_case):
    for s in show:
        if s in df.index.names and s not in df.columns:
            df[s] = df.index.get_level_values(s)
    if len(show) == 1:
        made = df[show[0]].astype(str)
    cats = [df[i].astype(str) for i in show[1:]]
    made = df[show[0]].str.cat(others=cats, sep="/").str.rstrip("/")
    if not preserve_case:
        made = made.str.lower()
    return made


def _get_tqdm():
    """
    Get either the IPython or regular version of tqdm
    """
    try:
        if get_ipython().__class__.__name__ == "ZMQInteractiveShell":  # noqa: F821
            return tqdm_notebook
        return tqdm
    except NameError:
        pass
    return tqdm


def _tree_once(df):
    """
    Get each parse tree once, probably so we can run nltk.ParentedTree on them
    """
    return df["parse"][df.index.get_level_values("i") == 1]


def _tqdm_update(tqdm):
    """
    Try to update tqdm, or do nothing
    """
    if tqdm is not None:
        tqdm.update(1)


def _tqdm_close(tqdm):
    """
    Try to close tqdm, or do nothing
    """
    if tqdm is not None:
        tqdm.close()


def _auto_window():
    """
    Get concordance left and right optimal size
    """
    columns = shutil.get_terminal_size().columns
    size = (columns / 2) * 0.60
    return [int(size), int(size)]


def _set_best_data_types(df):
    """
    Make DF have the best possible column data types
    """
    for c in list(df.columns):
        if c == "g" or df[c].dtype.name.startswith("date"):
            continue
        try:
            df[c] = df[c].astype(DTYPES.get(c, "category"))
            try:
                df[c].cat.add_categories("_")
            except AttributeError:
                pass
        except (ValueError, TypeError):
            pass
    return df


def _make_tree(tree):
    """
    Try to make a tree from this string, or return None
    """
    try:
        return ParentedTree.fromstring(tree)
    except Exception:
        return


def _get_nlp(language="english"):
    """
    Get spaCy
    """
    import spacy

    langs = dict(english="en", german="de")
    lang = langs.get(language, language)

    try:
        return spacy.load(lang)
    except OSError:
        from spacy.cli import download

        download(lang)
        return spacy.load(lang)


def _strip_metadata(text):
    """
    Remove metadata html from a string
    """
    from .constants import MAX_SPEAKERNAME_SIZE

    idregex = re.compile(
        r"(^[A-Za-z0-9-_]{,%d}?):" % MAX_SPEAKERNAME_SIZE, re.MULTILINE
    )
    text = re.sub(idregex, "", text)
    text = re.sub("<metadata.*?>", "", text)
    text = "\n".join([i.strip() for i in text.splitlines()])
    return re.sub(r"\n\s*\n", "\n", text)


def cast(text):
    """
    Attempt to get object from JSON string, or return the string
    """
    import json

    try:
        return json.loads(text)
    except Exception:
        return text


def _get_sentence(row, df):
    """
    Get the sentence for a given pd.Series (i.e. row in Dataset)

    Replace this if a faster way is found, possibly using .loc and reindexing.
    """
    start = row._n - row.name[2] + 1
    end = start + row.sent_len
    return df.iloc[start:end]


def _make_csv(raw_lines, fname):
    """
    Turn raw CONLL-U file data into something pandas' CSV reader can easily and quickly read.

    The main thing to do is to add the [file, sent#, token#] index, and transform the metadata
    stored as comments into additional columns

    Return: str (CSV data) and list of dicts (metadata for each discovered sentence)
    """
    csvdat = list()  # a list of csv strings as we make them
    meta_dicts = list()  # our sent-level metadata will go in here
    fname = os.path.basename(fname)
    # make list of sentence strings
    sents = raw_lines.strip().split("\n\n")
    # split into metadata and csv parts by getting first numbered row. probably but not always 1
    splut = [re.split("\n([0-9])", s, 1) for s in sents]
    for sent_id, (raw_sent_meta, one, text) in enumerate(splut, start=1):
        text = one + text  # rejoin it as it was
        sent_meta = dict()
        # get every metadata row, split into key//value
        for key, value in re.findall("^# (.*?) = (.*?)$", raw_sent_meta, re.MULTILINE):
            # turn the string into an object if it's valid json
            sent_meta[key.strip()] = cast(value.strip())
        # add the fsi part to every row
        text = "\n".join(f"{fname}\t{sent_id}\t{line}" for line in text.splitlines())
        # add csv and meta to our collection
        csvdat.append(text)
        meta_dicts.append(sent_meta)

    # return the csv without the double newline so it can be read all at once. add meta_dicts later.
    return "\n".join(csvdat), meta_dicts


def _order_df_columns(df, metadata=None):
    if metadata is None:
        metadata = [i for i in list(df.columns) if i not in COLUMN_NAMES]
    good_names = [i for i in COLUMN_NAMES if i in df.columns]
    df = df[good_names + list(sorted(metadata))]
    return df


def _to_df(
    corpus,
    load_trees: bool = True,
    subcorpus: Optional[str] = None,
    usecols: List[str] = COLUMN_NAMES,
):
    """
    Turn buzz.corpus.Corpus into a Dataset (i.e. pd.DataFrame-like object)
    """
    from .dataset import Dataset

    with open(corpus.path, "r") as fo:
        data = fo.read().strip("\n")

    data, metadata = _make_csv(data, corpus.name)

    df = pd.read_csv(
        StringIO(data),
        sep="\t",
        header=None,
        names=usecols,
        quoting=3,
        memory_map=True,
        index_col=["file", "s", "i"],
        engine="c",
        na_filter=False,
        usecols=usecols,
    )

    # make a dataframe containing sentence level metadata, then join it to main df
    metadata = {i: d for i, d in enumerate(metadata, start=1)}
    metadata = pd.DataFrame(metadata).T
    metadata.index.name = "s"
    df = metadata.join(df, how="inner")

    # fix the column order
    df = _order_df_columns(df, metadata)

    # remove columns whose value was interpeted or for which nothing is ever availablr
    badcols = ["o", "m"]
    df = df.drop(badcols, axis=1, errors="ignore")

    df["g"] = df["g"].fillna(0)
    if df["g"].dtype in {object, str}:
        df["g"] = df["g"].str.replace("_|^$", "0").astype(int)
    df["g"] = df["g"].astype(int)
    df = df.fillna("_")
    return Dataset(_set_best_data_types(df))


def _get_short_name_from_long_name(longname):
    revers = dict()
    for k, vs in LONG_NAMES.items():
        for v in vs:
            revers[v] = k
    return revers.get(longname, longname)


def _make_meta_dict_from_sent(text):
    from .utils import cast

    metad = dict()
    if "<metadata" in text:
        relevant = text.strip().rstrip(">").rsplit("<metadata ", 1)
        try:
            shxed = shlex.split(relevant[-1])
        except Exception:  # what is it?
            shxed = relevant[-1].split("' ")
        for m in shxed:
            try:
                k, v = m.split("=", 1)
                v = v.replace("\u2018", "'").replace("\u2019", "'")
                v = v.strip("'").strip('"')
                metad[k.replace("-", "_")] = cast(v)
            except ValueError:
                continue
    # speaker seg part
    regex = r"(^[a-zA-Z0-9-_]{,%d}?):..+" % MAX_SPEAKERNAME_SIZE
    speaker_regex = re.compile(regex)
    match = re.search(speaker_regex, text)
    if not match:
        return metad
    speaker = match.group(1)
    metad["speaker"] = speaker
    return metad
