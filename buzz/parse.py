import argparse
import os
import re
import shutil

import nltk
from nltk.parse import BllipParser

from .constants import MAX_SPEAKERNAME_SIZE
from .utils import (
    _get_nlp,
    _get_tqdm,
    _make_meta_dict_from_sent,
    _tqdm_close,
    _tqdm_update,
)

tqdm = _get_tqdm()

# this is where we store the bllip parser, which can only be loaded once.
BLLIP = None



def _parse_cmd_line():
    parser = argparse.ArgumentParser(description='Parse a corpus.')

    parser.add_argument(
        '-l',
        '--language',
        nargs='?',
        default='english',
        type=str,
        required=False,
        help='Language of the corpus',
    )

    parser.add_argument(
        '-p',
        '--cons-parser',
        nargs='?',
        default='benepar',
        type=str,
        required=False,
        choices=['bllip', 'benepar'],
        help='Constituency parser to use (bllip/benepar)',
    )

    parser.add_argument('path', help='Directory containing files to parse')
    return vars(parser.parse_args())


class Phony(object):
    """
    shitty object that overrides the str.decode method in bllip, currently broken
    """

    def __init__(self, word):
        self.word = Parser._normalise_word(word)

    def decode(self, *args, **kwargs):
        return self.word

    def __str__(self):
        return str(self.word)

    def __repr__(self):
        return str(self.word)


class Parser:
    """
    Create an object that can parse a Corpus.
    """

    def __init__(self, cons_parser="bllip", language="english"):
        self.cons_parser = cons_parser
        self.language = language
        self.nlp = _get_nlp()
        if self.cons_parser == "bllip":
            self._prepare_bllip()
        elif self.cons_parser == "benepar":
            self._prepare_benepar()

    def _prepare_bllip(self):
        print("Loading constituency parser...")
        try:
            model_dir = nltk.data.find("models/bllip_wsj_no_aux").path
        except LookupError:
            print("Downloading constituency data...")
            nltk.download("bllip_wsj_no_aux")
            model_dir = nltk.data.find("models/bllip_wsj_no_aux").path
        try:
            # need to use global here because you cannot load this model twice...
            global BLLIP
            BLLIP = BllipParser.from_unified_model_dir(model_dir)
        except RuntimeError:
            pass

    def _prepare_benepar(self):
        from benepar.spacy_plugin import BeneparComponent

        langs = dict(english="en", german="de")
        lang = langs.get(self.language)
        ben_file = f"benepar_{lang}"
        try:
            nltk.data.find(ben_file).path
        except LookupError:
            import benepar

            benepar.download(ben_file)
        self.nlp.add_pipe(BeneparComponent(ben_file))

    @staticmethod
    def _normalise_word(word, wrap=False):
        norm = str(word).strip().replace("\t", "").replace("\n", "")
        return Phony(norm) if wrap else norm

    @staticmethod
    def _make_misc_field(word):
        if not word.ent_type_ and not word.sentiment:
            return "_"
        formatters = dict(typ=word.ent_type_, num=word.ent_type, iob=word.ent_iob_)
        ent = "ent_type={typ}|ent_id={num}|ent_iob={iob}".format(**formatters)
        if not word.sentiment:
            return ent
        return ent + "|sentiment={}".format(word.sentiment)

    @staticmethod
    def _get_governor_id(word):
        if word.i == word.head.i:
            return "0"
        return str(word.head.i - word.sent[0].i + 1)

    @staticmethod
    def _strip_metadata(plain):
        idregex = re.compile(r"^[A-Za-z0-9-_]{1,%d}: " % MAX_SPEAKERNAME_SIZE)
        metregex = re.compile("<metadata .*>")
        plain = plain.splitlines()
        plain = [re.sub(metregex, "", re.sub(idregex, "", i)) for i in plain]
        return "\n".join(plain)

    @staticmethod
    def _get_line_with_meta(start, plain, stripped):
        all_before = stripped[:start]
        newlines_before = all_before.count("\n")
        plain = plain.splitlines()
        return plain[newlines_before]

    def _process_sent(self, sent_index, sent, file_meta, plain, stripped_data):
        word_index = 1
        sent_parts = list()
        text = sent.text.strip(" ").replace("\n", " ")
        toks = [i for i in sent if not i.is_space]
        self.ntokens += len(toks)
        sent_meta = dict(sent_id=str(sent_index), text=text.strip(), sent_len=len(toks))

        if self.trees and self.language.startswith("en"):
            parse = [self._normalise_word(str(i), wrap=True) for i in toks]
            if self.cons_parser == "bllip":
                parse = BLLIP.parse_one(parse)
                if parse:
                    parse = parse[0]._pformat_flat("", ("(", ")"), "")
                else:
                    parse = "(. .)"
            else:
                parse = sent._.parse_string
            sent_meta["parse"] = parse.replace("\n", " ").strip()

        metaline = self._get_line_with_meta(sent.start_char, plain, stripped_data)
        extra_meta = _make_meta_dict_from_sent(metaline)
        all_meta = {**file_meta, **sent_meta, **extra_meta}

        for field, value in sorted(all_meta.items()):
            sent_parts.append("# {} = {}".format(field, value))

        for word in sent:

            if word.is_space:
                continue

            governor = self._get_governor_id(word)
            word_text = self._normalise_word(str(word))
            named_ent = self._make_misc_field(word)

            parts = [
                str(word_index),
                word_text,
                word.lemma_,
                word.pos_,
                word.tag_,
                "_",
                governor,
                word.dep_,
                "_",
                named_ent,
            ]

            line = "\t".join(parts)
            sent_parts.append(line)
            word_index += 1

        return "\n".join(sent_parts)

    def _process_string(self, plain, path=None):
        """
        spacy: process a string of text
        """
        # break into lines, removing empty
        plain = [i.strip(" ") for i in plain.splitlines() if i.strip(" ")]
        file_meta = _make_meta_dict_from_sent(plain[0], first=True)
        if file_meta:
            plain = plain[1:]
        plain = "\n".join(plain)
        stripped_data = self._strip_metadata(plain)

        doc = self.nlp(stripped_data)
        output = list()
        self.nsents += len(list(doc.sents))

        for sent_index, sent in enumerate(doc.sents, start=1):
            sstr = self._process_sent(sent_index, sent, file_meta, plain, stripped_data)
            output.append(sstr)
        output = "\n\n".join(output).strip() + "\n"

        if not self.save_as and isinstance(self.plain_corpus, str):
            return output

        outpath = path.replace(self.corpus_name, self.corpus_name + "-parsed")
        outpath = outpath.rstrip(".") + ".conllu"
        os.makedirs(os.path.split(outpath)[0], exist_ok=True)
        self.made_new_dir = True

        with open(outpath, "w") as fo:
            fo.write(output)

    def _spacy_parse(self):
        if self.from_str:
            return self._process_string(self.plain_corpus)
        else:
            abspath = os.path.abspath(os.getcwd())
            fs = [os.path.join(abspath, f.path) for f in self.plain_corpus.files]
            kwa = dict(ncols=120, unit="file", desc="Parsing", total=len(fs))
            t = None
            t = tqdm(**kwa) if len(fs) > 1 else None
            for path in sorted(fs):
                with open(path, "r") as fo:
                    plain = fo.read().strip()
                self._process_string(plain, path=path)
                _tqdm_update(t)
            _tqdm_close(t)
            print("Done!")

    def _make_metadata(self, description):
        return dict(
            language=self.language,
            parser="spacy",
            cons_parser=self.cons_parser,
            path=os.path.abspath(self.parsed_path),
            name=self.corpus_name,
            parsed=True,
            nsents=self.nsents,
            ntokens=self.ntokens,
            nfiles=len(self.plain_corpus.files),
            desc=description,
        )

    def run(self, corpus, save_as=None):
        """
        Run the parsing pipeline

        Args:
           corpus (Corpus): plain data to process

        Return:
            Corpus: parsed corpus
        """
        from .corpus import Corpus

        self.plain_corpus = corpus
        self.save_as = save_as
        self.trees = bool(self.cons_parser)
        self.ntokens = 0
        self.nsents = 0
        self.made_new_dir = False
        self.from_str = True

        # get the corpus name and parsed name/path depending on obj type
        # it's a corpus, everything is easy
        if isinstance(corpus, Corpus):
            assert not corpus.is_parsed, "Corpus is already parsed"
            self.corpus_name = corpus.name
            self.parsed_name = corpus.name + "-parsed"
            self.parsed_path = corpus.path + "-parsed"
            self.from_str = False
        # it's a string, and the savename was provided
        elif isinstance(self.save_as, str):
            self.corpus_name = self.save_as
            self.parsed_name = self.corpus_name + "-parsed"
            self.parsed_path = self.parsed_name
        # save is simply true. needs a name.
        elif self.save_as:
            msg = "Please specify a savename with the `save` argument, or do save_as=False"
            raise ValueError(msg)

        if self.save_as and os.path.isdir(self.parsed_path):
            raise OSError(f"Path already exists: {self.parsed_path}")

        try:
            as_string = self._spacy_parse()
        except Exception:
            if self.made_new_dir:
                shutil.rmtree(self.parsed_path)
            raise

        if as_string is not None:
            parsed = Corpus.from_string(as_string, save_as=False)
        else:
            parsed = Corpus(self.parsed_path)
            metadata = self._make_metadata(None)
            parsed.add_metadata(**metadata)
        return parsed

if __name__ == '__main__':
    kwargs = _parse_cmd_line()
    corpus = Corpus(kwargs.pop('path'))
    corpus.parse(**kwargs)

