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

    def test_constructor(self):
        tab = LOADED.table()
        self.assertIsInstance(tab.iloc[0:5, 0:5], Table)

    def test_loaded_corpus_relative(self):
        relative = LOADED.table(relative=True)
        absolute = LOADED.table()
        self.assertIsInstance(relative, Table)
        self.assertEqual(relative.shape, absolute.shape)
        self.assertEqual(relative.index.name, absolute.index.name)
        self.assertEqual(relative.columns.name, absolute.columns.name)

    def test_show(self):
        word_pos = LOADED.table(show=['w', 'p'])
        self.assertTrue(all('/' in i for i in word_pos.columns))
        self.assertEqual(word_pos.columns[0], 'the/dt')
        self.assertEqual(word_pos.columns.name, 'w/p')
        word_pos = LOADED.table(show=['p', 'w'])
        self.assertTrue(all('/' in i for i in word_pos.columns))
        self.assertEqual(word_pos.columns[0], 'dt/the')
        self.assertEqual(word_pos.columns.name, 'p/w')
        word_pos = LOADED.table(show=['w', '+1w'])
        self.assertTrue(all('/' in i for i in word_pos.columns))
        self.assertEqual(list(word_pos.columns[:3]), ['in/the', 'the/jungle', 'the/stories'])

    def test_sort(self):
        tab = LOADED.table()
        self.assertEqual(tab.columns[0], 'the')
        inc = tab.sort('increase')
        dec = tab.sort('decrease')
        nam = tab.sort('name')
        rev = tab.sort('reverse')
        sta = tab.sort('static')
        tur = tab.sort('turbulent')
        sig = tab.sort('increase', remove_above_p=0.05, keep_stats=True)
        # these two entries have same slope...
        book_his = list(inc.columns)[:2]
        self.assertTrue('book' in book_his)
        self.assertTrue('his' in book_his)
        self.assertEqual(list(inc), list(reversed(list(dec))))
        # check that columns are actually alphametical. nice idiom
        self.assertTrue(all(x <= y for x, y in zip(list(nam), list(nam)[1:])))
        # check that sort by reverse is the opposite of default
        self.assertEqual(list(reversed(list(rev))), list(tab))
        # static is opposite of turbulent
        self.assertEqual(list(reversed(list(sta))), list(tur))
        sig_ix = ['one', 'second', 'space in name', 'slope', 'intercept', 'r', 'p', 'stderr']
        self.assertEqual(list(sig.index), sig_ix)
        # check that all values are below the p threshold
        self.assertTrue((sig.loc['p'] <= 0.05).all(), sig.loc['p'])
