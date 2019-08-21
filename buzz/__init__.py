import warnings

from .corpus import Corpus  # noqa: F401, E402

# we may not have buzz[word] installed, so this can fail
try:
    from .dashview import DashSite  # noqa: F401, E402
except ImportError:
    pass
from .dataset import Dataset  # noqa: F401, E402
from .file import File  # noqa: F401, E402
from .parse import Parser  # noqa: F401, E402

warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")
warnings.filterwarnings("ignore", message="registration of accessor")
warnings.filterwarnings("ignore", message="Attribibute 'is_copy")
warnings.filterwarnings("ignore")


__version__ = "3.0.6"
