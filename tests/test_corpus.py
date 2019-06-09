import os
import shutil
import unittest

from unittest.mock import ANY, Mock, mock_open, patch
from buzz.corpus import Corpus
from buzz.contents import Contents


STRUCTURE = dict(first='one',
                 second='second',
                 third='space in name')


class TestCorpus(unittest.TestCase):

    def setUp(self):
        self.unparsed = Corpus('tests/data')
        # super().__init__()

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
        start = '<buzz.corpus.Corpus'
        end = '(tests/data, unparsed)>'
        self.assertTrue(str(self.unparsed).startswith(start), str(self.unparsed))
        self.assertTrue(str(self.unparsed).endswith(end), str(self.unparsed))

    # add slow deco
    def test_parse(self):
        parsed_path = 'tests/data-parsed'
        # shutil.rmtree(parsed_path) ?
        if not os.path.isdir(parsed_path):
            parsed = self.unparsed.parse()
        else:
            parsed = Corpus(parsed_path)
        self.assertEqual(parsed.name, self.unparsed.name + '-parsed')
        self.test_subcorpora_and_files(parsed)
        start = '<buzz.corpus.Corpus'
        end = '(tests/data-parsed, parsed)>'
        self.assertTrue(str(parsed).startswith(start))
        self.assertTrue(str(parsed).endswith(end), str(parsed))


if __name__ == '__main__':
    unittest.main()
