import unittest

from buzz.dataset import Dataset
from buzz.file import File
from spacy.tokens.doc import Doc


class TestFile(unittest.TestCase):
    def test_load_unequal(self):
        unparsed = File("tests/data/first/one.txt")
        parsed = File("tests/testing-parsed/first/one.txt.conllu")
        self.assertNotEqual(unparsed, parsed)

    def test_spacy_same(self):
        unparsed = File("tests/data/first/one.txt").to_spacy()
        parsed = File("tests/testing-parsed/first/one.txt.conllu").to_spacy()
        # the spacy docs should be very similar for unparsed and parsed version
        # ... though not identical, unfortunately.
        self.assertEqual(len(unparsed), len(parsed))
        for first, second in zip(unparsed, parsed):
            self.assertEqual(str(first), str(second))

    def test_unparsed(self):
        unparsed = File("tests/data/first/one.txt")
        with self.assertRaises(NotImplementedError):
            unparsed.load()
        for from_iter, from_load in zip(unparsed, unparsed.read()):
            self.assertEqual(from_iter, from_load)
        doc = unparsed.to_spacy()
        self.assertIsInstance(doc, Doc)

    def test_parsed(self):
        parsed = File("tests/data-parsed/first/one.txt.conllu")
        loaded = parsed.load()
        self.assertIsInstance(loaded, Dataset, type(loaded))
        self.assertEqual(loaded.shape, (89, 12))
        for from_iter, from_load in zip(parsed, parsed.load()):
            self.assertEqual(from_iter, from_load)
        doc = parsed.to_spacy()
        self.assertIsInstance(doc, Doc)
