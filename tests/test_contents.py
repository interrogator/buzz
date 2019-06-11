import re
import unittest

from buzz.corpus import Corpus, Subcorpus
from buzz.file import File
from buzz.contents import Contents


class TestContents(unittest.TestCase):
    def test_contents(self):
        corpus = Corpus('tests/data')
        self.assertEqual(len(corpus.subcorpora), len(corpus.files))

        points = [('subcorpora', 'buzz.corpus.Subcorpus object', Subcorpus, 'first'),
                  ('files', 'buzz.file.File object', File, 'one')]

        for name, rep, clas, filename in points:

            iterab = getattr(corpus, name)
            # check repr
            self.assertTrue(str(iterab).startswith('['))
            self.assertTrue(str(iterab).endswith(']'))
            self.assertEqual(str(iterab).count(rep), 3, str(iterab))

            # check that getattr and getitem both work the same way
            att, item = getattr(iterab, filename), iterab[filename]
            self.assertEqual(att, item)
            self.assertIsInstance(att, clas)
            self.assertIsInstance(item, clas)
            # no such attribute
            with self.assertRaises(AttributeError):
                iterab.does_not_exist
            # no such item
            with self.assertRaises(KeyError):
                iterab['does_not_exist']
            # check that regex and slice can both work in the same way
            pat = re.compile('^(fir|o)..$')
            reg_match = iterab[pat]
            slice_match = iterab[:1]
            # check totally equal, then just check one to make sure both are correct
            self.assertEqual(reg_match, slice_match)
            self.assertIsInstance(reg_match, Contents)
            self.assertEqual(len(reg_match), 1)
            self.assertEqual(reg_match[0].name, filename)
            self.assertEqual(iterab[pat][0], iterab[0])
            # deletion
            del iterab[0]
            self.assertEqual(len(iterab), 2)
            # non comparable
            with self.assertRaises(TypeError):
                iterab == corpus
            # insertion
            iterab.insert(0, iterab[-1])
            self.assertEqual(iterab[0], iterab[-1])
            # unequal length should eq to false
            reloaded = getattr(Corpus('tests/data'), name)
            del reloaded[0]
            self.assertFalse(iterab == reloaded)
