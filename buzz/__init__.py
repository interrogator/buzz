import warnings

warnings.filterwarnings('ignore', message='numpy.dtype size changed')
warnings.filterwarnings('ignore', message='numpy.ufunc size changed')
warnings.filterwarnings('ignore', message='registration of accessor')
warnings.filterwarnings('ignore', message='Attribibute \'is_copy')
warnings.filterwarnings('ignore')

from .corpus import Corpus
from .dataset import Dataset

__version__ = '1.0.5'
