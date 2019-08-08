import warnings

from .corpus import Corpus  # noqa: F401, E402
from .dashview import DashSite  # noqa: F401, E402
from .dataset import Dataset  # noqa: F401, E402
from .file import File  # noqa: F401, E402
from .parse import Parser  # noqa: F401, E402
from .tools import cmd
from .tools import strings
from .tools import tabs
from .tools import utils

warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")
warnings.filterwarnings("ignore", message="registration of accessor")
warnings.filterwarnings("ignore", message="Attribibute 'is_copy")
warnings.filterwarnings("ignore")


__version__ = "2.0.5"
