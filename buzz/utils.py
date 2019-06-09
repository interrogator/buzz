import re
import os
import shlex
import shutil

from io import StringIO

import pandas as pd
from nltk.tree import ParentedTree
from tqdm import tqdm, tqdm_notebook

from .constants import DTYPES, LONG_NAMES, MAX_SPEAKERNAME_SIZE


def _get_tqdm():
    """
    Get either the IPython or regular version of tqdm
    """
    try:
        if get_ipython().__class__.__name__ == 'ZMQInteractiveShell':  # noqa: F821
            return tqdm_notebook
        return tqdm
    except NameError:
        pass
    return tqdm


def _tree_once(df):
    """
    Get each parse tree once, probably so we can run nltk.ParentedTree on them
    """
    return df['parse'][df.index.get_level_values('i') == 1]


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
        if c == 'g' or df[c].dtype.name.startswith('date'):
            continue
        try:
            df[c] = df[c].astype(DTYPES.get(c, 'category'))
            try:
                df[c].cat.add_categories('_')
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


def _get_nlp(language='english'):
    """
    Get spaCy
    """
    import spacy
    langs = dict(english='en', german='de')
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
    idregex = re.compile(r'(^[A-Za-z0-9-_]{,%d}?):' % MAX_SPEAKERNAME_SIZE, re.MULTILINE)
    text = re.sub(idregex, '', text)
    text = re.sub('<metadata.*?>', '', text)
    text = '\n'.join([i.strip() for i in text.splitlines()])
    return re.sub(r'\n\s*\n', '\n', text)


def cast(text):
    """
    Attempt to get object from JSON string, or return the string
    """
    import json
    try:
        return json.loads(text)
    except Exception:
        return text


def _make_csv(raw_lines, fname, meta, lt=True):
    """
    Take one CONLL-U file and add all metadata to each row
    Return: str (CSV data) and list of dicts (sent level metadata)
    """
    fname = os.path.basename(fname)
    meta_dicts = list()
    sents = raw_lines.strip() + '\n'
    # make list of sentences
    sents = sents.strip().split('\n\n')
    # split into metadata and csv
    splut = [re.split('\n([0-9])', s, 1) for s in sents]
    meta_dicts = list()
    csvdat = list()
    for s, (metastring, one, text) in enumerate(splut, start=1):
        text = one + text
        metadata = dict()
        for key, value in re.findall('^# (.*?) = (.*?)$', metastring, re.MULTILINE):
            metadata[key.strip()] = cast(value.strip())
        text = '\n'.join('{}\t{}\t{}'.format(fname, s, line) for line in text.splitlines())
        csvdat.append(text)
        meta_dicts.append(metadata)

    return '\n'.join(csvdat), meta_dicts


def _to_df(corpus,
           corpus_name=False,
           skip_morph=True,
           add_gov=False,
           usecols=None,
           notype=False,
           load_trees=True):
    """
    Optimised CONLL-U reader for v2.0 data

    Returns:
        pd.DataFrame: 3d array representation of file data

    """
    with open(corpus.path, 'r') as fo:
        data = fo.read().strip('\n')

    # metadata that applies filewide
    file_meta = dict(f=corpus.name)

    subcorpus = None
    file_meta['subcorpus'] = subcorpus

    cname = corpus.path.split('.')[0].split('/', 1)[-1]

    data, metadata = _make_csv(data, cname, file_meta, lt=load_trees)
    data = StringIO(data)

    col_names = ['file', 's', 'i', 'w', 'l', 'x', 'p', 'm', 'g', 'f', 'e', 'o']
    if usecols is not None:
        usecols = list(usecols)
        for i in ['file', 's', 'i']:
            if i not in usecols:
                usecols.append(i)

        col_names = [i for i in col_names if i in usecols]

    df = pd.read_csv(data,
                     sep='\t',
                     header=None,
                     names=col_names,
                     quoting=3,
                     memory_map=True,
                     index_col=['file', 's', 'i'],
                     engine='c',
                     na_filter=False,
                     usecols=usecols)

    # make and join the meta df
    metadata = {i: d for i, d in enumerate(metadata, start=1)}
    metadata = pd.DataFrame(metadata).T
    metadata.index.name = 's'
    df = metadata.join(df, how='inner')
    col_order = col_names[3:] + list(sorted(metadata))
    if usecols is not None:
        col_order = [i for i in col_order if i in usecols]
    df = df[col_order]

    badcols = ['o', 'm']
    df = df.drop(badcols, axis=1, errors='ignore')

    # some evil code to handle conll-u files where g col could be a string
    if 'g' in df.columns:
        df['g'] = df['g'].fillna(0)
        if df['g'].dtype in [object, str]:
            df['g'] = df['g'].str.replace('_|^$', '0').astype(int)
        df['g'] = df['g'].astype(int)
    df = df.fillna('_')

    if not notype:
        df = _set_best_data_types(df)

    if add_gov:
        raise NotImplementedError('Not done yet')

    return df


def _get_short_name_from_long_name(longname):
    revers = dict()
    for k, vs in LONG_NAMES.items():
        for v in vs:
            revers[v] = k
    return revers.get(longname, longname)


def _make_meta_dict_from_sent(text):
    from .utils import cast
    metad = dict()
    if '<metadata' in text:
        relevant = text.strip().rstrip('>').rsplit('<metadata ', 1)
        try:
            shxed = shlex.split(relevant[-1])
        except Exception:  # what is it?
            shxed = relevant[-1].split("' ")
        for m in shxed:
            try:
                k, v = m.split('=', 1)
                v = v.replace(u"\u2018", "'").replace(u"\u2019", "'")
                v = v.strip("'").strip('"')
                metad[k] = cast(v)
            except ValueError:
                continue
    # speaker seg part
    regex = r'(^[a-zA-Z0-9-_]{,%d}?):..+' % MAX_SPEAKERNAME_SIZE
    speaker_regex = re.compile(regex)
    match = re.search(speaker_regex, text)
    if not match:
        return metad
    speaker = match.group(1)
    metad['speaker'] = speaker
    return metad


def _get_metadata(stripped,
                  original,
                  sent_offsets,
                  first_line=False,
                  has_fmeta=False):
    """
    Take offsets and get a speaker ID or metadata from them
    """
    if not stripped and not original:
        return dict()

    # are we getting file or regular metadata?
    if not first_line:
        start, end = sent_offsets
    else:
        start = 0

    # get all stripped text before the start of the sent we want
    cut_old_text = stripped[:start].strip()
    # count how many newlines are in the preceding text
    line_index = cut_old_text.count('\n')
    if has_fmeta and not first_line:
        line_index += 1
    if first_line:
        line_index = 0
    text_with_meta = original.splitlines()[line_index]
    return _make_meta_dict_from_sent(text_with_meta)
