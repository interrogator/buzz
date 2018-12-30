import numpy as np

CONLL_COLUMNS = ['i', 'w', 'l', 'x', 'p', 'm', 'g', 'f', 'e', 'o']

_langs = ['english', 'german', 'chinese', 'arabic', 'spanish', 'french', 'english-kpb']

# it can be very slow to load a bunch of unused metadata categories
MAX_METADATA_FIELDS = 99
MAX_METADATA_VALUES = 99
MAX_SPEAKERNAME_SIZE = 40

STATS_FIELDS = ['Characters',
                'Clauses',
                'Closed class',
                'Interrogative',
                'Modalised declarative',
                'Open class',
                'Open interrogative',
                'Passives',
                'Punctuation',
                'Tokens',
                'Unmodalised declarative',
                'Words']

DTYPES = dict(i=np.int32,
              s=np.int64,
              w='category',
              l='category',
              p='category',
              x='category',
              g=np.int64,
              parse=object,
              f='category',
              m=str,
              o=str,
              n='category',
              gender='category',
              speaker='category',
              year=np.int64, # 'datetime64',
              date='category', # 'datetime64',
              month='category', # 'datetime64',
              postgroup=np.float64,
              totalposts=np.float64,
              postnum=np.float64,
              _n=np.int64,
              sent_len=np.int64,
              line=np.int64)

CONC_CONTEXT = 20

LONG_NAMES = dict(file={'corpus'},
                  s={'sentence'},
                  i={'index'},
                  w={'word', 'words'},
                  l={'lemma', 'lemmas', 'lemmata'},
                  x={'language_specific', 'localpos'},
                  p={'pos', 'wordclass', 'wordclasses'},
                  m={'morph', 'morphology'},
                  g={'governor', 'governors'},
                  f={'function', 'funct', 'functions', 'role', 'roles', 'link'},
                  e={'extra'},
                  o={'other'},
                  speaker={'speaker', 'speakers'})
