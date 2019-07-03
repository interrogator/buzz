import os
import re
import shutil

import nltk

from .constants import MAX_SPEAKERNAME_SIZE
from .utils import (
    _get_nlp,
    _get_tqdm,
    _make_meta_dict_from_sent,
    _tqdm_close,
    _tqdm_update,
)

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


class Parser:
    """
    Create an object that can parse a Corpus.
    """

    def __init__(self, corpus, parser="spacy", cons_parser="bllip", language="english"):
        self.corpus = corpus
        self.parser = parser
        self.cons_parser = cons_parser
        self.language = language
        self.ntokens = -1
        self.nsents = -1
        self._made_new_dir = False

    def spacy_prepare(self):
        self.nlp = _get_nlp()
        if not self.trees:
            return
        if self.cons_parser == "bllip":
            self.prepare_bllip()
        elif self.cons_parser == "benepar":
            self.prepare_benepar()
        return True

    def prepare_bllip(self):
        print("Loading constituency parser...")
        from nltk.parse import BllipParser

        try:
            model_dir = nltk.data.find("models/bllip_wsj_no_aux").path
        except LookupError:
            print("Downloading constituency data...")
            nltk.download("bllip_wsj_no_aux")
            model_dir = nltk.data.find("models/bllip_wsj_no_aux").path
        self.tree_parser = BllipParser.from_unified_model_dir(model_dir)
        return True

    def prepare_benepar(self):
        from benepar.spacy_plugin import BeneparComponent

        langs = dict(english="en", german="de")
        lang = langs.get(self.language)
        ben_file = "benepar_{}".format(lang)
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
        length = len([i for i in sent if not i.is_space])
        self.ntokens += length
        sent_meta = dict(sent_id=str(sent_index), text=text.strip(), sent_len=length)

        if self.trees and self.language.startswith("en"):
            parse = [
                self.normalise_word(str(i), wrap=True) for i in sent if not i.is_space
            ]
            if self.cons_parser == "bllip":
                parse = self.tree_parser.parse_one(parse)
                parse = (
                    parse[0]._pformat_flat("", ("(", ")"), "").replace("\n", "").strip()
                )
            else:
                parse = sent._.parse_string.strip(" ")
            parse = parse.replace("\n", " ")
            sent_meta["parse"] = parse

        metaline = self._get_line_with_meta(sent.start_char, plain, stripped_data)

        extra_meta = _make_meta_dict_from_sent(metaline)

        all_meta = {**file_meta, **sent_meta, **extra_meta}

        for field, value in sorted(all_meta.items()):
            sent_parts.append("# {} = {}".format(field, value))

        for word in sent:

            if word.is_space:
                continue

            governor = self._get_governor_id(word)
            word_text = self.normalise_word(str(word))
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

    def _process_file(self, path):
        """
        spacy: process one file
        """

        with open(path, "r") as fo:
            plain = fo.read().strip()

        # break into lines, removing empty
        plain = [i.strip(" ") for i in plain.splitlines() if i.strip(" ")]

        if plain[0].startswith("<metadata"):
            file_meta = _make_meta_dict_from_sent(plain[0])
            # remove the metadata line
            plain = plain[1:]
        else:
            file_meta = dict()

        plain = "\n".join(plain)
        stripped_data = self._strip_metadata(plain)
        doc = self.nlp(stripped_data)
        output = list()
        self.nsents += len(list(doc.sents))

        for sent_index, sent in enumerate(doc.sents, start=1):
            sent_string = self._process_sent(
                sent_index, sent, file_meta, plain, stripped_data
            )
            output.append(sent_string)
        output = "\n\n".join(output).strip() + "\n"

        outpath = path.replace(self.corpus_name, self.corpus_name + "-parsed")
        outpath = outpath.rstrip(".") + ".conllu"
        os.makedirs(os.path.split(outpath)[0], exist_ok=True)
        self._made_new_dir = True

        with open(outpath, "w") as fo:
            fo.write(output)

    def spacy_parse(self):
        abspath = os.path.abspath(os.getcwd())
        fs = [os.path.join(abspath, f.path) for f in self.plain_corpus.files]
        kwa = dict(ncols=120, unit="file", desc="Parsing", total=len(fs))
        t = None
        self.ntokens = 0
        self.nsents = 0
        t = tqdm(**kwa) if len(fs) > 1 else None

        for path in sorted(fs):
            self._process_file(path)
            _tqdm_update(t)
        _tqdm_close(t)
        print("Done!")

    def _make_metadata(self, description):
        return dict(
            language=self.language,
            parser=self.parser,
            cons_parser=self.cons_parser,
            path=os.path.abspath(self.parsed_path),
            name=self.corpus_name,
            parsed=True,
            nsents=self.nsents,
            ntokens=self.ntokens,
            nfiles=len(self.plain_corpus.files),
            desc=description,
        )

    def run(self, corpus):
        """
        Run the parsing pipeline

        Args:
           corpus (Corpus): plain data to process

        Return:
            Corpus: parsed corpus
        """
        from .corpus import Corpus

        self.plain_corpus = corpus
        assert not corpus.is_parsed
        self.trees = bool(self.cons_parser)
        self.corpus_name = corpus.name

        # name for final corpus folder
        self.parsed_name = corpus.name + "-parsed"
        self.parsed_path = corpus.path + "-parsed"

        if os.path.isdir(self.parsed_path):
            raise OSError(f"Path already exists: {self.parsed_path}")

        try:
            prepared = self.prepare_parser()
            if not prepared:
                raise ValueError("Error in preparation...")
            self.spacy_parse()
        except Exception:
            if self._made_new_dir:
                shutil.rmtree(self.parsed_path)
            raise

        parsed = Corpus(self.parsed_path)
        metadata = self._make_metadata(None)
        parsed.add_metadata(**metadata)
        return parsed
