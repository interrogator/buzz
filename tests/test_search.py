import unittest

from buzz.corpus import Corpus


class TestSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """ get_some_resource() is slow, to avoid calling it for each test use setUpClass()
            and store the result as class variable
        """
        super().setUpClass()
        cls.parsed = Corpus("tests/testing-parsed")
        cls.loaded = cls.parsed.load()

    def test_non_loaded(self):
        # todo: find out why .equals isn't the same.
        res = self.parsed.depgrep("w/book/ = x/NOUN/")
        lres = self.loaded.depgrep("w/book/ = x/NOUN/")
        self.assertEqual(len(res), 3)
        self.assertTrue(list(res._n) == list(lres._n))
        res = self.parsed.depgrep("l/book/")
        lres = self.loaded.depgrep("l/book/")
        self.assertEqual(len(res), 6)
        self.assertTrue(list(res.index) == list(lres.index))
        self.assertTrue(list(res._n) == list(lres._n))

    def test_bigrams(self):
        j = self.loaded.just.words("(?i)jungle")
        self.assertEqual(len(j), 6)
        big = self.loaded.bigrams.depgrep("l/jungle/", from_reference=True).table(
            show=["x"]
        )
        self.assertTrue("punct" in big.columns)
        self.assertEqual(big.shape[1], 5)
        no_punct = self.loaded.skip.wordclass.PUNCT
        big = no_punct.bigrams.lemma("jungle", from_reference=False).table(show=["x"])
        self.assertFalse("punct" in big.columns)
        self.assertEqual(big.shape[1], 3)

    def test_depgrep(self):
        res = self.loaded.depgrep("L/book/")
        self.assertEqual(len(res), 3)
        res = self.loaded.depgrep('x/^NOUN/ -> l"the"', case_sensitive=False)
        sup = self.loaded.depgrep('p/^N/ -> l"the"', case_sensitive=False)
        # sup is a superset of res
        self.assertTrue(all(i in sup.index for i in res.index))
        self.assertEqual(len(sup), 28)
        self.assertEqual(len(res), 24)
        self.assertTrue((res.x == "NOUN").all())
        # let us check this manually
        # get all rows whose lemma is 'the'
        the = self.loaded[self.loaded["l"] == "the"]
        count = 0
        # iterate over rows, get governor of the, lookup this row.
        # if row is a noun, check that its index is in our results
        for (f, s, _), series in the.T.items():
            gov = series["g"]
            gov = self.loaded.loc[f, s, gov]
            if gov.x == "NOUN":
                self.assertTrue(gov.name in res.index)
                count += 1
        self.assertEqual(count, len(res))
