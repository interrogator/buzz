import re
import os

from io import StringIO
import pandas as pd
from nltk.tree import ParentedTree

from .constants import CONLL_COLUMNS, DTYPES


def auto_window():
    import shutil
    columns = shutil.get_terminal_size().columns
    size = (columns / 2) * 0.60
    return [int(size), int(size)]


def _set_best_data_types(df):
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


def maketree(tree):
    try:
        return ParentedTree.fromstring(tree)
    except:
        return


def _get_nlp(language='english'):
    try:
        import spacy
    except ImportError:
        raise NotImplementedError('spaCy not installed')

    langs = dict(english='en', german='de')
    lang = langs.get(language, language)
    try:
        return spacy.load(lang)
    except OSError:
        from spacy.cli import download
        download(lang)
        return spacy.load(lang)


def _strip_metadata(text):
    from .constants import MAX_SPEAKERNAME_SIZE
    idregex = re.compile(r'(^[A-Za-z0-9-_]{,%d}?):' % MAX_SPEAKERNAME_SIZE, re.MULTILINE)
    text = re.sub(idregex, '', text)
    text = re.sub('<metadata.*?>', '', text)
    text = '\n'.join([i.strip() for i in text.splitlines()])
    return re.sub('\n\s*\n', '\n', text)


def cast(text):
    import json
    try:
        return json.loads(text)
    except:
        return text


def make_csv(raw_lines, fname, meta, subcorpus=None, lt=True):
    """
    Take one CONLL-U file and add all metadata to each row
    Return: str (CSV data) and list of dicts (sent level metadata)
    """
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
        metadata = dict() if not subcorpus else dict(subcorpus=subcorpus)
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
    from .classes import Subcorpus
    with open(corpus.path, 'r') as fo:
        data = fo.read().strip('\n')

    # metadata that applies filewide
    file_meta = dict(f=corpus.name)

    # try to parse years
    subcorpus = corpus.container.name if type(corpus.container) == Subcorpus else None
    file_meta['subcorpus'] = subcorpus

    cname = corpus.path.split('.')[0].split('/', 1)[-1]

    data, metadata = make_csv(data, cname, file_meta, subcorpus=corpus.container.name, lt=load_trees)
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


def saferead(path):
    """
    Read a file with detect encoding

    Returns:
        text and its encoding
    """
    import chardet
    import sys
    if sys.version_info.major == 3:
        enc = 'utf-8'
        try:
            with open(path, 'r', encoding=enc) as fo:
                data = fo.read()
        except:
            with open(path, 'rb') as fo:
                data = fo.read().decode('utf-8', errors='ignore')
        return data, enc
    else:
        with open(path, 'r') as fo:
            data = fo.read()
        try:
            enc = 'utf-8'
            data = data.decode(enc)
        except UnicodeDecodeError:
            enc = chardet.detect(data)['encoding']
            data = data.decode(enc, errors='ignore')
        return data, enc


def partition(lst, n):
    """
    Divide a lst or dataframe into n chunks
    """
    from .classes import Corpus
    if isinstance(lst, pd.DataFrame):
        import numpy as np
        return np.array_split(lst, n)
    if isinstance(lst, Corpus):
        lst = lst.filepaths
    q, r = divmod(len(lst), n)
    indices = [q*i + min(i, r) for i in range(n+1)]
    chunks = [lst[indices[i]:indices[i+1]] for i in range(n)]
    divved = [i for i in chunks if len(i)]
    return divved


def timestring(text):
    """
    Print with time prepended
    """
    from time import localtime, strftime
    thetime = strftime("%H:%M:%S", localtime())
    print('%s: %s' % (thetime, text.lstrip()))
