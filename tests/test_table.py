import unittest

from buzz.corpus import Corpus
from buzz.table import Table


TOTAL_TOKENS = 329

STRUCTURE = dict(first='one',
                 second='second',
                 third='space in name')

BOOK_IX = [('second', 1, 6), ('space in name', 3, 2), ('space in name', 4, 12)]


LOADED = Corpus('tests/testing-parsed').load()


class TestTable(unittest.TestCase):

    def test_loaded_corpus_table(self):
        tab = LOADED.table()
        self.assertIsInstance(tab, Table)
        self.assertEqual(tab.shape, (3, 167))
        self.assertEqual(tab.index.name, 'file')
        self.assertEqual(tab.columns.name, 'w')

    def test_loaded_corpus_relative(self):
        relative = LOADED.table(relative=True)
        absolute = LOADED.table()
        self.assertIsInstance(relative, Table)
        self.assertEqual(relative.shape, absolute.shape)
        self.assertEqual(relative.index.name, absolute.index.name)
        self.assertEqual(relative.columns.name, absolute.columns.name)
