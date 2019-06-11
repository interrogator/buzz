import unittest

from buzz.corpus import Corpus


class TestSearch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """ get_some_resource() is slow, to avoid calling it for each test use setUpClass()
            and store the result as class variable
        """
        super().setUpClass()
        cls.parsed = Corpus('tests/testing-parsed')
        cls.loaded = cls.parsed.load()

    def test_tgrep(self):
        res = self.loaded.tgrep('NN < /book/')
        self.assertEqual(len(res), 3)

    def test_depgrep(self):
        res = self.loaded.depgrep('l/book/')
        self.assertEqual(len(res), 3)
