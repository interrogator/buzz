import warnings
warnings.filterwarnings('ignore', message='numpy.dtype size changed')
warnings.filterwarnings('ignore', message='numpy.ufunc size changed')
warnings.filterwarnings('ignore', message='registration of accessor')
warnings.filterwarnings('ignore', message='Attribibute \'is_copy')
warnings.filterwarnings('ignore')

from .classes import Corpus, LoadedCorpus, Results

__version__ = '1.0.3'
