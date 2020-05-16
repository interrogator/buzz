import numpy as np

CONLL_COLUMNS = ["i", "w", "l", "x", "p", "m", "g", "f", "e", "o"]

COLUMN_NAMES = ["file", "s"] + CONLL_COLUMNS

SHORT_TO_LONG_NAME = dict(
    w="Word",
    l="Lemma",  # noqa: E741
    p="Part of speech",
    g="Governor index",
    f="Dependency role",
    x="Wordclass",
    i="Token index",
    e="Extra",
    m="Morphological features",
    gw="Governor word",
    gl="Governor lemma",
    gp="Governor POS",
    gg="Governor gov. index",
    gf="Governor dep. role",
    gx="Governor wordclass",
    gi="Governor token index",
    s="Sentence number",
    file="Filename",
    speaker="Speaker",
    d="Depgrep",
    t="TGrep2",
    describe="Describe entities",
)

_SHORTER = dict(
    s="Sent #", i="Token #", p="POS", g="Gov.", f="Function", x="Class", m="Morph"
)
SHORT_TO_COL_NAME = {**SHORT_TO_LONG_NAME, **_SHORTER}
SHORT_TO_COL_NAME = {
    k: v.replace("Governor", "Gov.") for k, v in SHORT_TO_COL_NAME.items()
}

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
    e=str,
    speaker="category",
    year=np.int64,  # 'datetime64',
    date="category",  # 'datetime64',
    month="category",  # 'datetime64',
    postgroup=np.float64,
    totalposts=np.float64,
    postnum=np.float64,
    _n=np.int64,
    sent_len=np.int64,
    sent_id=np.int64,
    line=np.int64,
    mood="category",
    number="category",
    person=np.int64,
    tense="category",
    verbform="category",
    definite="category",
    gender="category",
    prontype="category",
    adptype="category",
    puncttype="category",
    numtype="category",
    punctside="category",
    part_name=str,
    part_number=np.int64,
    chapter_name=str,
    chapter_number=np.int64,
    emph=bool,
    strong=bool,
    text=str,
    location=str,
    file="category",
    title=str,
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
    text={"text", "texts", "original"},
)

SENT_LEVEL_METADATA = {"sent_len", "text", "parse", "speaker", "year", "date"}

LANGUAGES = {
    "German": "de",
    "Greek": "el",
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "Italian": "it",
    "Dutch": "nl",
    "Portuguese": "pt",
    "Multi-language": "xx",
    "Afrikaans": "af",
    "Arabic": "ar",
    "Basque": "eu",
    "Bulgarian": "bg",
    "Bengali": "bn",
    "Catalan": "ca",
    "Czech": "cs",
    "Danish": "da",
    "Estonian": "et",
    "Persian": "fa",
    "Finnish": "fi",
    "Irish": "ga",
    "Hebrew": "he",
    "Hindi": "hi",
    "Croatian": "hr",
    "Hungarian": "hu",
    "Indonesian": "id",
    "Icelandic": "is",
    "Japanese": "ja",
    "Kannada": "kn",
    "Korean": "ko",
    "Lithuanian": "lt",
    "Latvian": "lv",
    "Marathi": "mr",
    "Norwegian Bokmål": "nb",
    "Polish": "pl",
    "Romanian": "ro",
    "Serbian": "rs",
    "Russian": "ru",
    "Sinhala": "si",
    "Slovak": "sk",
    "Slovenian": "sl",
    "Albanian": "sq",
    "Swedish": "sv",
    "Tamil": "ta",
    "Telugu": "te",
    "Thai": "th",
    "Tagalog": "tl",
    "Turkish": "tr",
    "Tatar": "tt",
    "Ukrainian": "uk",
    "Urdu": "ur",
    "Vietnamese": "vi",
    "Chinese": "zh",
}

AVAILABLE_MODELS = {"en", "de", "it", "nl", "el", "pt", "fr", "es"}

LANGUAGE_TO_MODEL = {v: v for k, v in LANGUAGES.items() if v in AVAILABLE_MODELS}
# need to give the full name for english, due to issue noted here:
# https://github.com/interrogator/buzz/issues/4
LANGUAGE_TO_MODEL["en"] = "en_core_web_sm"

BENEPAR_LANGUAGES = dict(
    en="benepar_en_small",  # en2 will use own POS, we want to share with spacy
    zh="benepar_zh",
    ar="benepar_ar",
    de="benepar_de",
    eu="benepar_eu",
    fr="benepar_fr",
    he="benepar_he",
    hu="benepar_hu",
    ko="benepar_ko",
    pl="benepar_pl",
    sv="benepar_sv",
)

MORPH_FIELDS = {
    "adptype": "adp_type",
    "definite": "definite",
    "gender": "gender",
    "mood": "mood",
    "number": "number",
    "numtype": "num_type",
    "person": "person",
    "prontype": "pron_type",
    "punctside": "punct_side",
    "puncttype": "punct_type",
}


QUERYSETS = dict(
    NOUN={
        # women are STUPID
        'f"acomp" <- (X"VERB" -> ({query} = F/nsubj/))',
        # STUPID women
        'f"amod" <- {query}',
        # STUPIDITY of women, women of STUPIDITY
        'P"NN" -> (F"prep" = w/of/ -> ({query} = F/pobj|nsubj/))',
        # women and STUPIDITY
        'X"NOUN" -> F/cc/ -> ({query} = F"conj")',
        # Women's STUPID attitudes (note, women's stupid husbands...)
        'F"amod" <- (X"NOUN" -> ({query} = F"poss"))',
        # women's STUPIDITY
        'X"NOUN" -> ({query} = F"poss")',
        # women who are STUPID
        'F"acomp" <- (F"relcl" <- {query})',
        # women STUPIDLY want ...
        'F"advmod" <- (X"VERB" -> ({query} = F"nsubj"))',
    },
    VERB={
        # I STUPIDLY risked it
        'F"advmod" <- (X"VERB" = {query})'
    },
    # risking it was STUPID...
)

# for the topology queries, it's possible to customise what token attributes
# should be counted for a given feature. this is the default, note no word/lemma
_wanted_features = {"p", "x", "f"}

TOPOLOGY_QUERIES = dict(
    GENERAL=dict(
        is_first_word=(lambda x: x.name[2] == 1, False, None),
        is_last_word=(lambda x: x.name[2] == x.sent_len, False, None),
        is_root=(lambda x: x.f.lower() == "root", False, None),
        root_is=("f/root/ ->> {query}", True, _wanted_features),
        # what shoud9999999999999
        this_token=(lambda x: x, True, _wanted_features | {"w", "l"},),
        word_three_before=("w/.*/ -3 {query}", True, _wanted_features),
        word_two_before=("w/.*/ -2 {query}", True, _wanted_features),
        word_before=("w/.*/ - {query}", True, _wanted_features),
        word_after=("w/.*/ + {query}", True, _wanted_features),
        word_two_after=("w/.*/ +2 {query}", True, _wanted_features),
        word_three_after=("w/.*/ +3 {query}", True, _wanted_features),
        governor=("w/.*/ -> {query}", True, _wanted_features),
    ),
    NOUN=dict(
        is_subject=(lambda x: x.f in {"nsubj"}, False, None),
        is_object=(lambda x: x.f in {"ccomp"}, False, None),
        is_copula=("F/cop/ <- {query}", False, None),
        # is_group_head=(lambda x: x., False, None),
        # group_head=("{query}", True, _wanted_features),
        subject_of=("X/VERB/ -> {query}", True, _wanted_features),
        object_of=("X/VERB/ <- {query}", True, _wanted_features),
        determined_by=("F/det/ <- {query}", True, _wanted_features),
        has_prep_immediately_after=("X/PREP/ + {query}", False, None),
        prep_immediately_after=("X/PREP/ + {query}", True, _wanted_features),
        has_prep_dependent=("X/PREP/ <- {query}", False, None),
        prep_dependent=("X/PREP/ <- {query}", True, _wanted_features),
        modified_by=("F/amod/ <- {query}", True, _wanted_features),
        classified_by=("F/nummod/ <- {query}", True, _wanted_features),
        conjoined_with=("F/conj/ ( <- {query} | -> {query})", True, _wanted_features,),
        subordinated=(lambda x: x.f == "acl", False, None),
        appositional=("F/appos/ [ <- {query} | -> {query} ]", True, _wanted_features,),
        compound=("F/compound$/ [ <- {query} | -> {query} ]", True, _wanted_features,),
    ),
    VERB=dict(
        subject_is=("F/nsubj/ <- {query}", True, _wanted_features),
        object_is=("F/obj/ <- {query}", True, _wanted_features),
        indirect_object_is=("F/iobj/ <- {query}", True, _wanted_features),
        # has_subject=(lambda x: x., False, None),
        # has_object=(lambda x: x., False, None),
        # has_indirect_object=(lambda x: x., False, None),
        modified_by=("F/advmod/ <- {query}", True, _wanted_features),
        modalised_by=("F/aux/ <- {query}", True, _wanted_features),
        phrasal_verb_prep=("f/compound:prt/ <- {query}", True, _wanted_features),
        # aspect=("{query}", True, _wanted_features),
        # progressive=("{query}", True, _wanted_features),
        # tense=(lambda x: x., False, None),
        # aspect=(lambda x: x., False, None),
        # progressive=(lambda x: x., False, None),
        conjoined_with=("F/conj/ [ <- {query} | -> {query} ]", True, _wanted_features,),
        verbal_xcomp=("X/VERB/ = F/xcomp/ <- {query}", True, _wanted_features),
        subordinated=(lambda x: x.f == "mark", False, None),
    ),
)
