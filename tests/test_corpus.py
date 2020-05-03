import shutil
import unittest
from unittest.mock import patch

from spacy.tokens.doc import Doc

from buzz.constants import LONG_NAMES
from buzz.contents import Contents
from buzz.corpus import Corpus
from buzz.dataset import Dataset
from buzz.exceptions import NoReferenceCorpus, DataTypeError
from buzz.table import Table

TOTAL_TOKENS = 342

STRUCTURE = dict(first=["one"], second=["mult", "second"], third=["space in name"])

BOOK_IX = [("second", 1, 6), ("space in name", 3, 2), ("space in name", 4, 12)]


class TestCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.unparsed = Corpus("tests/data")
        cls.loaded_plain = cls.unparsed.load()
        cls.parsed = Corpus("tests/testing-parsed")
        cls.loaded = cls.parsed.load()
        cls.loaded_subcorpora_in_col = cls.parsed.load(folders="column")
        cls.loaded_dropsub = cls.parsed.load(folders=None)

    def test_load_plain(self):
        self.assertIsInstance(self.loaded_plain, dict)
        # iterate over the four files
        for i, (path, data) in enumerate(self.loaded_plain.items()):
            self.assertEqual(self.unparsed.files[i].path, path)
            # tests/data/first/one.txt' != 'tests/data/first'
            self.assertEqual(self.unparsed.files[i].read(), data)

    def test_add_governor(self):
        loaded = self.parsed.load(add_governor=True)
        self.assertTrue(all(i in loaded.columns for i in ["gw", "gl", "gf", "gg"]))

    def test_load_usecols(self):
        load = ["w", "l"]
        loaded = self.parsed.load(usecols=load, folders="column")
        extra = ["subcorpus", "_n"]
        self.assertEqual(list(loaded.columns), load + extra)
        load = ["l", "speaker"]
        loaded = self.parsed.load(usecols=load)
        self.assertEqual(list(loaded.columns), load + ["_n"])

    def test_folder_options(self):
        """
        User can choose how they handle the fact that their project
        has folders. by default it goes into the index, but it can
        also go into a column, or be ignored. check that these values work
        """
        drop = self.loaded_dropsub
        col = self.loaded_subcorpora_in_col
        index = self.parsed.load()  # same as folders="index"
        self.assertTrue("subcorpus" not in drop)
        self.assertTrue("subcorpus" not in index)
        self.assertEqual(drop.index[0][0], "one")
        self.assertEqual(col.index[0][0], "one")
        self.assertEqual(index.index[0][0], "first/one")
        self.assertEqual(col.subcorpus[0], "first")

    def test_subcorpora_and_files(self, corpus=None):
        corpus = corpus or self.unparsed
        subcorpora = corpus.subcorpora
        files = corpus.files
        self.assertIsInstance(subcorpora, Contents)
        self.assertEqual(len(subcorpora), 3)
        for i, (k, filenames) in enumerate(STRUCTURE.items()):
            sub = corpus[i]
            also_sub = subcorpora[i]
            self.assertEqual(sub, also_sub)
            self.assertEqual(sub.name, k)
            file_in_sub = sub[0]
            also_file_in_sub = sub.files[0]
            self.assertEqual(file_in_sub, also_file_in_sub)
            for i, fname in enumerate(filenames):
                self.assertEqual(sub[i].name, fname)

        for sub in subcorpora:
            self.assertTrue(len(sub))
        self.assertIsInstance(files, Contents)
        self.assertEqual(len(files), 4)

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
        self.assertEqual(parsed.name, self.unparsed.name)
        self.test_subcorpora_and_files(parsed)
        start = "<buzz.corpus.Corpus"
        end = "(tests/data-parsed, parsed)>"
        self.assertTrue(str(parsed).startswith(start))
        self.assertTrue(str(parsed).endswith(end), str(parsed))

    def test_loaded_unloaded(self):
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
            "ent_id",
            "ent_iob",
            "ent_type",
            "sent_id",
            "sent_len",
            "speaker",
            "text",
            "token_annotation",
            "_n",
        ]
        self.assertTrue(all(i in self.loaded.columns for i in expect))

    def test_just_skip(self):
        book = self.loaded_dropsub.just.lemmata.book
        regex_book = self.loaded_dropsub.just.lemmata("b..k")
        self.assertTrue(all(book.index == regex_book.index))
        self.assertEqual(len(book), 3)
        indices = list(book.index)
        for fsi in BOOK_IX:
            self.assertTrue(fsi in indices)
        nobook = self.loaded_dropsub.skip.lemmata.book
        self.assertEqual(len(nobook), TOTAL_TOKENS - len(book))

    def test_unloaded_loaded_same(self):
        """
        Test just/load methods on Corpus objects, and that
        they give us the same as on loaded corpora
        """
        book_l = self.loaded.just.lemmata.book
        book_u = self.parsed.just.lemmata.book
        self.assertEqual(len(book_l), len(book_u))
        nobook_l = self.loaded.skip.lemmata.book
        nobook_u = self.parsed.skip.lemmata.book
        self.assertEqual(len(nobook_l), len(nobook_u))
        self.assertEqual(len(nobook_u), TOTAL_TOKENS - len(book_u))
        self.assertEqual(len(nobook_l), TOTAL_TOKENS - len(book_l))

    def test_all_slice_names(self):
        """
        Test that all slice names work and produce same result as column name
        """
        cols = self.loaded.columns
        for corp in [self.loaded, self.parsed]:
            for col, set_of_names in LONG_NAMES.items():
                if col not in cols:
                    continue
                every_match = getattr(corp.just, col)(".*")
                self.assertEqual(len(every_match), len(self.loaded))
                for name in set_of_names:
                    res = getattr(corp.just, name)(".*")
                    self.assertEqual(len(res), len(every_match))

    def test_conc(self):
        """
        Test concordance on loaded data
        """
        book = self.loaded.just.lemmata.book
        conc = book.conc(show=["w", "p"])
        self.assertTrue(all(i in conc.columns for i in ["left", "match", "right"]))
        left, match = "A major theme in the", "book/NN"
        # right = 'is abandonment followed by'
        self.assertTrue(conc.iloc[0, 0].endswith(left))
        self.assertTrue(conc.iloc[0, 1].endswith(match))
        # can we use iloc here reliably? speaker can move to be next to match...
        # self.assertTrue(right in conc['right'][0])

    def test_unloaded_conc_error(self):
        book = self.parsed.just.lemmata.book
        with self.assertRaises(NoReferenceCorpus):
            book.conc(show=["w", "p"])

    def test_dot_syntax(self):
        """
        The kind of ridiculous 'see' method

        Tests for the table itself should stay in test_table
        """
        for corp in [self.parsed.load(multiprocess=False)]:  # self.loaded
            tab = corp.see.pos.by.lemma
            self.assertIsInstance(tab, Table)
            self.assertEqual(tab.columns.name, "l")
            self.assertEqual(tab.index.name, "p")
            self.assertEqual(tab.sum()["the"], 30)
        short = self.loaded.see.l()
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
        d = Dataset(self.parsed.path)
        f = Dataset(self.parsed.files[0].path)
        self.assertTrue(d.equals(self.loaded))
        self.assertTrue(f.equals(self.parsed.files[0].load()))
        with patch("buzz.tabview.view", side_effect=ValueError("Boom!")):
            with self.assertRaises(ValueError):
                self.loaded.view()

    def test_just_index_and_int_match(self):
        for corp in [self.loaded, self.parsed]:
            just_two = corp.just.sentences(2)
            self.assertTrue((just_two.index.get_level_values("s") == 2).all())
            with self.assertRaises(DataTypeError):
                corp.just.words(1)

    def test_token_annotation(self):
        tokens = self.loaded[self.loaded["token_annotation"] == "level"]
        self.assertEqual(len(tokens), 2)
        self.assertEqual(list(tokens["w"]), ["important", "theme"])


if __name__ == "__main__":
    unittest.main()
