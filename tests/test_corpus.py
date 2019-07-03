import shutil
import unittest
from collections import OrderedDict
from unittest.mock import patch

from buzz.constants import LONG_NAMES
from buzz.contents import Contents
from buzz.corpus import Corpus
from buzz.dataset import Dataset
from buzz.table import Table
from nltk.tree import ParentedTree
from spacy.tokens.doc import Doc

TOTAL_TOKENS = 329

STRUCTURE = dict(first="one", second="second", third="space in name")

BOOK_IX = [("second", 1, 6), ("space in name", 3, 2), ("space in name", 4, 12)]


class TestCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """ get_some_resource() is slow, to avoid calling it for each test use setUpClass()
            and store the result as class variable
        """
        super().setUpClass()
        cls.unparsed = Corpus("tests/data")
        cls.loaded_plain = cls.unparsed.load()
        cls.parsed = Corpus("tests/testing-parsed")
        cls.loaded = cls.parsed.load(load_trees=True)
        cls.loaded_no_tree = cls.parsed.load(load_trees=False)

    def test_trees(self):
        self.assertIsInstance(self.loaded["parse"].iloc[0], ParentedTree)
        self.assertIsInstance(self.loaded_no_tree["parse"].iloc[0], str)

    def test_load_plain(self):
        self.assertIsInstance(self.loaded_plain, OrderedDict)
        for i, (path, data) in enumerate(self.loaded_plain.items()):
            self.assertEqual(self.unparsed.files[i].path, path)
            self.assertEqual(self.unparsed.files[i].read(), data)

    def test_subcorpora_and_files(self, corpus=None):
        corpus = corpus or self.unparsed
        subcorpora = corpus.subcorpora
        files = corpus.files
        self.assertIsInstance(subcorpora, Contents)
        self.assertEqual(len(subcorpora), 3)
        for i, (k, v) in enumerate(STRUCTURE.items()):
            sub = corpus[i]
            also_sub = subcorpora[i]
            self.assertEqual(sub, also_sub)
            self.assertEqual(sub.name, k)
            f = sub[0]
            also_f = sub.files[0]
            self.assertEqual(f, also_f)
            self.assertEqual(f.name, v)

        for sub in subcorpora:
            self.assertTrue(len(sub))
        self.assertIsInstance(files, Contents)
        self.assertEqual(len(files), 3)

    def test_repr(self):
        start = "<buzz.corpus.Corpus"
        end = "(tests/data, unparsed)>"
        self.assertTrue(str(self.unparsed).startswith(start), str(self.unparsed))
        self.assertTrue(str(self.unparsed).endswith(end), str(self.unparsed))

    # add slow deco
    def test_parse(self):
        parsed_path = "tests/data-parsed"
        try:
            shutil.rmtree(parsed_path)
        except FileNotFoundError:
            pass
        parsed = self.unparsed.parse()
        self.assertEqual(parsed.name, self.unparsed.name + "-parsed")
        self.test_subcorpora_and_files(parsed)
        start = "<buzz.corpus.Corpus"
        end = "(tests/data-parsed, parsed)>"
        self.assertTrue(str(parsed).startswith(start))
        self.assertTrue(str(parsed).endswith(end), str(parsed))

    def test_loaded(self):
        self.assertIsInstance(self.loaded, Dataset)
        self.assertEqual(len(self.loaded), TOTAL_TOKENS)
        expect = [
            "w",
            "l",
            "x",
            "p",
            "g",
            "f",
            "e",
            "annotated",
            "field",
            "parse",
            "sent_id",
            "sent_len",
            "speaker",
            "text",
            "_n",
        ]
        self.assertTrue(all(i in self.loaded.columns for i in expect))

    def test_just_skip(self):
        book = self.loaded.just.lemmata.book
        regex_book = self.loaded.just.lemmata("b..k")
        self.assertTrue(all(book.index == regex_book.index))
        self.assertEqual(len(book), 3)
        indices = list(book.index)
        for fsi in BOOK_IX:
            self.assertTrue(fsi in indices)
        nobook = self.loaded.skip.lemmata.book
        self.assertEqual(len(nobook), TOTAL_TOKENS - len(book))

    def test_all_slice_names(self):
        """
        Test that all slice names work and produce same result as column name
        """
        for col, set_of_names in LONG_NAMES.items():
            if col not in list(self.loaded.columns):
                continue
            every_match = getattr(self.loaded.just, col)(".*")
            self.assertEqual(len(every_match), len(self.loaded))
            for name in set_of_names:
                res = getattr(self.loaded.just, name)(".*")
                self.assertEqual(len(res), len(every_match))

    def test_conc(self):
        book = self.loaded.just.lemmata.book
        conc = book.conc(show=["w", "p"])
        self.assertTrue(all(i in conc.columns for i in ["left", "match", "right"]))
        left, match = "A major theme in the", "book/NN"
        # right = 'is abandonment followed by'
        self.assertTrue(conc.iloc[0, 0].endswith(left))
        self.assertTrue(conc.iloc[0, 1].endswith(match))
        # can we use iloc here reliably? speaker can move to be next to match...
        # self.assertTrue(right in conc['right'][0])

    def test_dot_syntax(self):
        """
        The kind of ridiculous 'see' method

        Tests for the table itself should stay in test_table
        """
        tab = self.loaded.see.pos.by.lemma
        short = self.loaded.see.l()
        self.assertIsInstance(tab, Table)
        self.assertEqual(tab.columns.name, "l")
        self.assertEqual(tab.index.name, "p")
        self.assertEqual(tab.sum()["the"], 30)
        self.assertEqual(short["the"], 30)

    def test_no_path(self):
        with self.assertRaises(FileNotFoundError):
            Corpus("no/exist/dir")

    def test_bad_compare(self):
        with self.assertRaises(TypeError):
            self.unparsed == "a string"

    def test_spacy(self):
        spac = self.unparsed.to_spacy()
        self.assertIsInstance(spac, list)
        self.assertTrue(all(isinstance(i, Doc) for i in spac))

    def test_dataset(self):
        d = Dataset(self.parsed.path, load_trees=True)
        f = Dataset(self.parsed.files[0].path, load_trees=True)
        self.assertTrue(d.equals(self.loaded))
        self.assertTrue(f.equals(self.parsed.files[0].load()))
        with patch("buzz.views.view", side_effect=ValueError("Boom!")):
            with self.assertRaises(ValueError):
                self.loaded.view()

    def test_just_index(self):
        just_two = self.loaded.just.sentences("^2$")
        self.assertTrue((just_two.index.get_level_values("s") == 2).all())


if __name__ == "__main__":
    unittest.main()
