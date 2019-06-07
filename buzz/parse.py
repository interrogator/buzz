import os
import shutil
import fnmatch

from .utils import _strip_metadata, _get_tqdm, _tqdm_close, _tqdm_update, _get_metadata, _get_nlp

import nltk
import spacy

tqdm = _get_tqdm()


class Phony(object):
    """
    shitty object that overrides the str.decode method in bllip, currently broken
    """
    def __init__(self, word):
        self.word = Parser.normalise_word(word)

    def decode(self, *args, **kwargs):
        return self.word

    def __str__(self):
        return str(self.word)

    def __repr__(self):
        return str(self.word)


class Parser(object):
    """
    Create an object that can parse a Corpus.
    """
    def __init__(self, corpus, parser='spacy', cons_parser='benepar', language='english'):
        self.corpus = corpus
        self.parser = parser
        self.cons_parser = cons_parser
        self.language = language
        self.ntokens = -1
        self.nsents = -1
        super(Parser, self).__init__()

    def unimplemented(self):
        """
        For things not yet done
        """
        raise NotImplementedError

    def spacy_prepare(self):
        self.nlp = _get_nlp()
        if not self.trees:
            return
        if self.cons_parser == 'bllip':
            self.prepare_bllip()
        elif self.cons_parser == 'benepar':
            self.prepare_benepar()
        return True

    def prepare_bllip(self):
        print('Loading constituency parser...')
        from nltk.parse import BllipParser
        try:
            model_dir = nltk.data.find('models/bllip_wsj_no_aux').path
        except LookupError:
            print('Downloading constituency data...')
            nltk.download('bllip_wsj_no_aux')
            model_dir = nltk.data.find('models/bllip_wsj_no_aux').path
        self.tree_parser = BllipParser.from_unified_model_dir(model_dir)
        return True

    def prepare_benepar(self):
        from benepar.spacy_plugin import BeneparComponent
        langs = dict(english='en', german='de')
        lang = langs.get(self.language)
        ben_file = 'benepar_{}'.format(lang)
        try:
            nltk.data.find(ben_file).path
        except LookupError:
            import benepar
            benepar.download(ben_file)
        self.nlp.add_pipe(BeneparComponent(ben_file))
        return True

    def prepare_parser(self):
        """
        Calls the correct preparation method
        """
        prepares = dict(spacy=self.spacy_prepare)
        return prepares.get(self.parser, self.spacy_prepare)()

    @staticmethod
    def normalise_word(word, wrap=False):
        norm = str(word).strip().replace('\t', '').replace('\n', '')
        return Phony(norm) if wrap else norm

    @staticmethod
    def _make_misc_field(word):
        if not word.ent_type_ and not word.sentiment:
            return '_'
        formatters = dict(typ=word.ent_type_,
                          num=word.ent_type,
                          iob=word.ent_iob_)
        ent = 'ent_type={typ}|ent_id={num}|ent_iob={iob}'.format(**formatters)
        if not word.sentiment:
            return ent
        return ent + '|sentiment={}'.format(word.sentiment)

    @staticmethod
    def _get_governor_id(word):
        if word.i == word.head.i:
            return '0'
        return str(word.head.i - word.sent[0].i + 1)

    def spacy_parse(self):
        abspath = os.path.abspath(os.getcwd())
        fs = [os.path.join(abspath, f.path) for f in self.plain_corpus.files]
        kwa = dict(ncols=120, unit='file', desc='Parsing', total=len(fs))
        t = None
        ntokens = 0
        nsents = 0
        t = tqdm(**kwa) if len(fs) > 1 else None
        for file_num, path in enumerate(fs, start=1):

            with open(path, 'r') as fo:
                plain = fo.read().strip()
            
            stripped_data = _strip_metadata(plain)
            doc = self.nlp(stripped_data)
            file_meta = _get_metadata(stripped_data, plain, False, first_line=True)
            has_file_meta = plain.splitlines()[0].strip().startswith('<metadata')

            output = list()
            nsents += len(list(doc.sents))
            for sent_index, sent in enumerate(doc.sents, start=1):
                word_index = 1
                sent_parts = list()
                text = sent.text.strip().replace('\n', ' ')
                sent_meta = dict(sent_id=str(sent_index),
                                 text=text,
                                 sent_len=len(sent))
                if self.trees and self.language.startswith('en'):
                    parse = [self.normalise_word(str(i), wrap=True) for i in sent if not i.is_space]
                    if self.cons_parser == 'bllip':
                        parse = self.tree_parser.parse_one(parse)
                        parse = parse[0]._pformat_flat('', ('(', ')'), "").replace('\n', '').strip()
                    else:
                        parse = sent._.parse_string.strip('')
                    parse = parse.replace('\n', ' ')
                    sent_meta['parse'] = parse

                extra_meta = _get_metadata(stripped_data,
                                          plain,
                                          (sent.start_char, sent.end_char),
                                          first_line=False,
                                          has_fmeta=has_file_meta)

                all_meta = {**file_meta, **sent_meta, **extra_meta}

                for field, value in sorted(all_meta.items()):
                    sent_parts.append('# {} = {}'.format(field, value))

                for word in sent:

                    ntokens += 1
                    if word.is_space:
                        continue
                    
                    governor = self._get_governor_id(word)
                    word_text = self.normalise_word(str(word))
                    named_ent = self._make_misc_field(word)
                    
                    parts = [str(word_index),
                             word_text,
                             word.lemma_,
                             word.pos_,
                             word.tag_,
                             '_',
                             governor,
                             word.dep_,
                             '_',
                             named_ent]

                    line = '\t'.join(parts)
                    sent_parts.append(line)
                    word_index += 1

                output.append('\n'.join(sent_parts))

            output = '\n\n'.join(output).strip() + '\n'
            outpath = path.replace(self.corpus_name, self.corpus_name + '-parsed')
            outpath = outpath.rstrip('.') + '.conllu'

            with open(outpath, 'w') as fo:
                fo.write(output)

            _tqdm_update(t)
        _tqdm_close(t)

        self.ntokens = ntokens
        self.nsents = nsents

    def _make_metadata(self, description):
        return dict(language=self.language,
                    parser=self.parser,
                    cons_parser=self.cons_parser,
                    copula_head=self.copula_head,
                    path=self.parsed_path,
                    name=self.corpus_name,
                    parsed=True,
                    nsents=self.nsents,
                    ntokens=self.ntokens,
                    nfiles=len(self.plain_corpus.files),
                    desc=description)

    def run(self, corpus, out_dir: str = '.'):
        """
        Run the parsing pipeline

        Args:
           corpus (Corpus): plain data to process

        Return:
            Corpus: parsed corpus
        """
        from .corpus import Corpus
        self.plain_corpus = corpus
        self.trees = bool(self.cons_parser)
        self.corpus_name = corpus.name

        # name for final corpus folder
        self.parsed_name = corpus.name + '-parsed'
        # dir to put parsed corpus in
        self.out_dir = out_dir
        # full path to final parsed corpus
        self.parsed_path = os.path.join(self.out_dir, self.parsed_name)

        if os.path.isdir(self.parsed_path):
            raise OSError(f'Path already exists: {self.parsed_path}')

        os.makedirs(self.out_dir, exist_ok=True)
        shutil.copytree(self.plain_corpus.path, self.parsed_path,
                        ignore=shutil.ignore_patterns('*.*'))
        self.made_new_dir = True

        try:
            prepared = self.prepare_parser()
            if not prepared:
                raise ValueError('Error in preparation...')
            self.spacy_parse()
        except:
            if self.made_new_dir:
                shutil.rmtree(self.parsed_path)
            raise

        parsed = Corpus(self.parsed_path)
        metadata = self._make_metadata(None)
        parsed.add_metadata(metadata)
        return parsed
