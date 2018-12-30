from __future__ import print_function
from collections import Counter
import pandas as pd
from .views import make_match_col


def log_likelihood_measure(word_in_ref, word_in_target, ref_sum, target_sum):
    """calc log likelihood keyness"""
    import math
    neg = (word_in_target / float(target_sum)) < (word_in_ref / float(ref_sum))

    E1 = float(ref_sum)*((float(word_in_ref)+float(word_in_target)) / \
        (float(ref_sum)+float(target_sum)))
    E2 = float(target_sum)*((float(word_in_ref)+float(word_in_target)) / \
        (float(ref_sum)+float(target_sum)))

    if word_in_ref == 0:
        logaE1 = 0
    else:
        logaE1 = math.log(word_in_ref/E1)
    if word_in_target == 0:
        logaE2 = 0
    else:
        logaE2 = math.log(word_in_target/E2)
    score = float(2* ((word_in_ref*logaE1)+(word_in_target*logaE2)))
    if neg:
        score = -score
    return score


def make_keywords(subcorpus, reference=None, measurer=log_likelihood_measure, selfdrop=True, ref_sum=0, target_sum=0):
    #if selfdrop:
    #    reference = reference - subcorpus
    points = [(reference.get(name, 0), count, ref_sum, target_sum) for name, count in subcorpus.iteritems()]
    return [measurer(*arg) for arg in points]


def perc_diff_measure(word_in_ref, word_in_target, ref_sum, target_sum):
    """calculate using perc diff measure"""

    norm_target = float(word_in_target) / target_sum
    norm_ref = float(word_in_ref) / ref_sum
    # Gabrielatos and Marchi (2012) do it this way!
    if norm_ref == 0:
        norm_ref = 0.00000000000000000000000001
    return ((norm_target - norm_ref) * 100.0) / norm_ref


def _get_reference_corpus(self, reference_corpus):
    if isinstance(self, Results):
        df = self._df()
    else:
        df = self
    if not reference_corpus:
        return df, self.reference
    if reference_corpus == 'bnc':
        if len(show) > 1:
            msg = 'Cannot do multiple show values with BNC reference reference corpus'
            raise NotImplementedError(msg)
        from buzz.dictionaries.bnc import _get_bnc
        return df, _get_bnc()
    if isinstance(reference_corpus, (pd.Series, pd.DataFrame)):
        return df, reference_corpus
    if isinstance(reference_corpus, (Corpus, File)):
        return reference_corpus.load(), reference_corpus.load()


def _keywords(self,
              show=['w'],
              subcorpora='file',
              reference_corpus=None,
              selfdrop=True,
              measure='ll',
              only_open_class=True,
              **kwargs):

    from .classes import Frequencies, Corpus, File, Results
    freq_calculated = type(self) == Frequencies
    df, reference_corpus = _get_reference_corpus(self, reference_corpus)

    measures = dict(ll=log_likelihood_measure, pd=perc_diff_measure)
    measurer = measures.get(measure, log_likelihood_measure)

    if only_open_class:
        df = df[df['p'].str.startswith(('N', 'V', 'J', 'A'))]
    rs, ts = reference.shape[0] if not reference_corpus else reference.sum(), df.shape[0]

    form_match = make_match_col(df, show)

    if not freq_calculated:
        df = df.table(subcorpora=subcorpora,
                      show=show,
                      #preserve_case=False,
                      #count=False,
                      #no_punct=True,
                      #sort=kwargs.get('sort', 'total'),
                      #relative=None,
                      ngram=False,
                      top=-1)

    # make the formatted column
    reference['_match'] = form_match
    # formatted -> count series
    ref_counts = reference['_match'].value_counts()

    kwa = dict(axis=0, reference=ref_counts, selfdrop=selfdrop, measurer=measurer, ref_sum=rs, target_sum=ts)
    applied = df.T.apply(make_keywords, **kwa).T
    order = applied.apply(abs).sum().sort_values(ascending=False)
    return Frequencies(applied, reference=reference)
