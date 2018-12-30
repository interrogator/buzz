__all__ = ["wordlists", "roles", "bnc", "processes", "verbs",
           "uktous", "tagtoclass", "queries", "mergetags"]

from buzz.dictionaries.bnc import _get_bnc
from buzz.dictionaries.process_types import processes
from buzz.dictionaries.process_types import verbs
from buzz.dictionaries.roles import roles
from buzz.dictionaries.wordlists import wordlists
from buzz.dictionaries.queries import queries
from buzz.dictionaries.word_transforms import taglemma
from buzz.dictionaries.word_transforms import mergetags
from buzz.dictionaries.word_transforms import usa_convert

roles = roles
wordlists = wordlists
processes = processes
bnc = _get_bnc
queries = queries
tagtoclass = taglemma
uktous = usa_convert
mergetags = mergetags
verbs = verbs
