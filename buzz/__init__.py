import warnings


warnings.filterwarnings('ignore', message='numpy.dtype size changed')
warnings.filterwarnings('ignore', message='numpy.ufunc size changed')
warnings.filterwarnings('ignore', message='registration of accessor')
warnings.filterwarnings('ignore', message='Attribibute \'is_copy')
warnings.filterwarnings('ignore')

from .corpus import Corpus  # noqa: F401
from .dataset import Dataset  # noqa: F401

__version__ = '1.0.5'
