import re
import unittest

from buzz.corpus import Corpus, Subcorpus
from buzz.file import File
from buzz.contents import Contents


class TestContents(unittest.TestCase):
    def test_contents(self):
        corpus = Corpus('tests/data')
        self.assertEqual(len(corpus.subcorpora), len(corpus.files))

        for name in ['subcorpora', 'files']:
            iterab = getattr(corpus, name)
            self.assertTrue(str(iterab).startswith('['))
            self.assertTrue(str(iterab).endswith(']'))
            if name == 'subcorpora':
                rep, clas, name = 'buzz.corpus.Subcorpus object', Subcorpus, 'first'
            else:
                rep, clas, name = 'buzz.file.File object', File, 'one'
            self.assertEqual(str(iterab).count(rep), 3, str(iterab))
            att, item = getattr(iterab, name), iterab[name]
            self.assertEqual(att, item)
            self.assertIsInstance(att, clas)
            with self.assertRaises(AttributeError):
                iterab.does_not_exist
            self.assertIsInstance(item, clas)
            with self.assertRaises(KeyError):
                iterab['does_not_exist']
            # two ways to get same thing, regex and slice
            pat = re.compile('^(fir|o)..$')
            reg_match = iterab[pat]
            slice_match = iterab[:1]
            # check totally equal, then just check one to make sure both are correct
            self.assertEqual(reg_match, slice_match)
            self.assertIsInstance(reg_match, Contents)
            self.assertEqual(len(reg_match), 1)
            self.assertEqual(reg_match[0].name, name)
            self.assertEqual(iterab[pat][0], iterab[0])
