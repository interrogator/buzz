import re
import unittest

from buzz.contents import Contents
from buzz.corpus import Corpus, Subcorpus
from buzz.file import File


class TestContents(unittest.TestCase):
    def test_contents(self):
        corpus = Corpus("tests/data")
        self.assertNotEqual(len(corpus.subcorpora), len(corpus.files))
        self.assertEqual(len(corpus.subcorpora), len(corpus.files) - 1)
        # there are three subcorpora and 4 files. here is the data that
        # needs to be in the repr of these objects
        points = [
            ("subcorpora", "buzz.corpus.Subcorpus object", Subcorpus, "first", 3),
            ("files", "buzz.file.File object", File, "one", 4),
        ]

        for name, rep, clas, filename, tot in points:
            iterab = getattr(corpus, name)
            # check repr
            self.assertTrue(str(iterab).startswith("["))
            self.assertTrue(str(iterab).endswith("]"))
            self.assertEqual(str(iterab).count(rep), tot, str(iterab))

            # check that getattr and getitem bothx work the same way
            att, item = getattr(iterab, filename), iterab[filename]
            self.assertEqual(att, item)
            self.assertIsInstance(att, clas)
            self.assertIsInstance(item, clas)
            # no such attribute
            with self.assertRaises(AttributeError):
                iterab.does_not_exist
            # no such item
            with self.assertRaises(KeyError):
                iterab["does_not_exist"]
            # check that regex and slice can both work in the same way
            pat = re.compile("^(fir|o)..$")
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
            self.assertEqual(len(iterab), tot - 1)
            # non comparable
            with self.assertRaises(TypeError):
                iterab == corpus
            # insertion
            iterab.insert(0, iterab[-1])
            self.assertEqual(iterab[0], iterab[-1])
            # unequal length should eq to false
            reloaded = getattr(Corpus("tests/data"), name)
            del reloaded[0]
            self.assertFalse(iterab == reloaded)
