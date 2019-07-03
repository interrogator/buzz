import numpy as np

CONLL_COLUMNS = ["i", "w", "l", "x", "p", "m", "g", "f", "e", "o"]

COLUMN_NAMES = ["file", "s"] + CONLL_COLUMNS

MAX_SPEAKERNAME_SIZE = 40

DTYPES = dict(
    i=np.int32,
    s=np.int64,
    w="category",
    l="category",  # noqa: E741
    p="category",
    x="category",
    g=np.int64,
    parse=object,
    f="category",
    m=str,
    o=str,
    n="category",
    gender="category",
    speaker="category",
    year=np.int64,  # 'datetime64',
    date="category",  # 'datetime64',
    month="category",  # 'datetime64',
    postgroup=np.float64,
    totalposts=np.float64,
    postnum=np.float64,
    _n=np.int64,
    sent_len=np.int64,
    line=np.int64,
)

LONG_NAMES = dict(
    file={"files"},
    s={"sentence", "sentences"},
    i={"index", "indices"},
    w={"word", "words", "token", "tokens"},
    l={"lemma", "lemmas", "lemmata"},  # noqa: E741
    x={"language_specific", "localpos", "class", "xpos", "wordclass", "wordclasses"},
    p={"pos", "partofspeech", "tag", "tags"},
    m={"morph", "morphology"},
    g={"governor", "governors", "gov", "govs"},
    f={"function", "funct", "functions", "role", "roles", "link", "links"},
    e={"extra"},
    o={"other"},
    speaker={"speaker", "speakers"},
    text={"text", "texts", "sentence", "sentences"},
)
