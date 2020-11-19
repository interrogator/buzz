import argparse
import os
import re
import shutil

import numpy as np
from joblib import Parallel


from . import multi
from .html import MetadataStripper
from .utils import _get_nlp, _get_tqdm, _make_meta_dict_from_sent, cast

tqdm = _get_tqdm()


def _strip_metadata(plain, speakers):
    # todo: do this without splitting
    out = []
    for line in plain.splitlines():
        parser = MetadataStripper(speakers)
        parser.feed(line)
        out.append(parser.text)
    return "\n".join(out)


def to_stripped(text, hocr=False):
    """
    Replace all XML with spaces:

    "<meta>hello</meta>" -> "      hello       "

    We do this so that we can find the original XML after parsing.
    """
    if hocr:
        xmltag = "(.*?)((?:<span.*?ocrx_word|<em).*?>)(.*?)((?:</span>|</em>)\s*)"
        out = ""
        text = text.strip()
        for line in text.splitlines():
            match = re.search(xmltag, line)
            if not match:
                out += " " * len(line) + "\n"
                continue
            first, start, content, end = match.group(1), match.group(2), match.group(3), match.group(4)
            piece = first + (" " * len(start)) + content + (" " * len(end)) + "\n"
            if len(piece) - 1 != len(match.group(0)):
                raise ValueError(len(piece), len(match.group(0)), piece + "///" + match.group(0))
            out += piece
        text += "\n"
        assert len(out) == len(text), f"{len(out)} vs {len(text)}"
        return out
    
    xmltag = "(.*?)(<meta.*?>)(.*?)(</meta>\s*)"
    out = ""
    text = text.strip()
    for match in re.finditer(xmltag, text):
        first, start, content, end = match.group(1), match.group(2), match.group(3), match.group(4)
        piece = first + (" " * len(start)) + content + (" " * len(end))
        if len(piece) != len(match.group(0)):
            raise ValueError(piece + "///" + match.group(0))
        out += piece

    assert len(out) == len(text), f"{len(out)} vs {len(text)}"
    return out


def _normalise_word(word, wrap=False):
    return str(word).strip().replace("\t", "").replace("\n", "")


def _get_line_with_meta(start, plain, stripped):
    all_before = stripped[:start]
    line_index = all_before.count("\n")
    plain = plain.splitlines()
    return plain[line_index]


def _get_governor_id(word):
    if word.i == word.head.i:
        return "0"
    return str(word.head.i - word.sent[0].i + 1)


def _strip_punct(span):
    """
    Fallback only --- last ditch effort to match token in span
    """
    return "".join(i for i in span if i.isalnum() or i in {"-"})


def _make_misc_field(word, token_meta, all_meta):
    """
    Build the misc cell for this word. It has NER, sentiment AND user-added
    """
    if not word.ent_iob and not word.sentiment and not token_meta:
        return "_"
    ent = word.ent_type_ or "_"
    formatters = dict(typ=ent, num=word.ent_iob, iob=word.ent_iob_)
    misc = "ent_type={typ}|ent_id={num}|ent_iob={iob}".format(**formatters)
    if word.sentiment:
        misc += "|sentiment={}".format(word.sentiment)
    for key, val in token_meta.items():
        if key not in all_meta:
            misc += "|{}={}".format(key, val)
    return misc


def _process_string(
    plain, path, save_as, corpus_name, language, constituencies, speakers, corpus_path, hocr
):
    """
    spacy: process a string of text
    """
    # break into lines, removing empty
    plain = [i.strip(" ") for i in plain.splitlines() if i.strip(" ")]
    file_meta = _make_meta_dict_from_sent(plain[0], first=True, speakers=speakers)
    if file_meta:
        plain = plain[1:]
    plain = "\n".join(plain)
    # stripped_data = _strip_metadata(plain, speakers)
    stripped_data = to_stripped(plain, hocr=hocr)
    nlp = _get_nlp(language=language, constituencies=constituencies)
    sentencizer = nlp.create_pipe("sentencizer")
    nlp.add_pipe(sentencizer, before='parser')
    doc = nlp(stripped_data)
    output = list()
    sent_index = 1
    for sent in doc.sents:

        if all(i.is_space for i in sent):
            continue

        sent_index += 1

        sstr = _process_sent(
            sent_index,
            sent,
            file_meta,
            plain,
            stripped_data,
            language,
            constituencies,
            speakers,
        )
        output.append(sstr)
    output = "\n\n".join(output).strip() + "\n"

    # path is the original filepath, corpus_path is the base
    make_in = os.path.dirname(corpus_path)
    outdir = os.path.join(make_in, "conllu")
    os.makedirs(outdir, exist_ok=True)
    outpath = path.replace(corpus_path, outdir)
    outpath = os.path.splitext(outpath)[0] + ".conllu"
    with open(outpath, "w") as fo:
        fo.write(output)


def _get_token_meta(plain, word):
    # this block gets the token metadata. it's evil.
    before_this_token = plain[:word.idx+len(word)]
    this_line = before_this_token.rstrip("\n").rsplit("\n", 1)[-1]
    token_meta = dict()
    if "<meta" not in this_line:
        return token_meta
    this_token_tag = this_line.rsplit("<meta", 1)[-1]
    this_token_tag = this_token_tag[:-len(word)].rsplit(">", 1)[0]
    for piece in this_token_tag.strip().split(" "):
        k, v = piece.split("=", 1)
        token_meta[k] = cast(v)
    return token_meta


def _get_tag_morph(word):
    if "__" in word.tag_ and len(word.tag_) > 2:
        return word.tag_.split("__", 1)
    return word.tag_, "_"


def _process_sent(
    sent_index,
    sent,
    file_meta,
    plain,
    stripped_data,
    language,
    constituencies,
    speakers,
):
    word_index = 1
    sent_parts = list()
    text = sent.text.strip(" ").replace("\n", " ")
    text = " ".join(text.strip().split())
    toks = [i for i in sent if not i.is_space]
    sent_meta = dict(sent_id=str(sent_index), text=text, sent_len=len(toks))

    if constituencies:
        sent_meta["parse"] = str(sent._.parse_string).replace("\n", " ")

    metaline = plain[sent.start_char:sent.end_char]
    inner_sent_meta = _make_meta_dict_from_sent(metaline, speakers=speakers)
    all_meta = {**file_meta, **sent_meta, **inner_sent_meta}

    for field, value in sorted(all_meta.items()):
        sent_parts.append("# {} = {}".format(field, value))

    sent = [w for w in sent if not w.is_space]

    for word in sent:

        governor = _get_governor_id(word)
        word_text = _normalise_word(str(word))
        token_meta = _get_token_meta(plain, word)
        named_ent = _make_misc_field(word, token_meta, all_meta)
        tag, morph = _get_tag_morph(word)

        parts = [
            str(word_index), word_text, word.lemma_, word.pos_,
            tag, morph, governor, word.dep_, "_", named_ent,
        ]

        sent_parts.append("\t".join(parts))
        word_index += 1

    return "\n".join(sent_parts)


def _parse_cmd_line():
    parser = argparse.ArgumentParser(description="Parse a corpus.")

    parser.add_argument(
        "-l",
        "--language",
        nargs="?",
        default="en",
        type=str,
        required=False,
        help="Language of the corpus",
    )

    parser.add_argument(
        "-c",
        "--constituencies",
        default=True,
        action="store_true",
        required=False,
        help="Attempt constituency parsing as well as dependency parsing",
    )

    parser.add_argument("path", help="Directory containing files to parse")
    return vars(parser.parse_args())


class Parser:
    """
    Create an object that can parse a Corpus.
    """

    def __init__(
        self, language="en", multiprocess=False, constituencies=False, speakers=True, just_missing=False
    ):
        self.multiprocess = multiprocess
        self.language = language
        self.constituencies = constituencies
        self.speakers = speakers
        self.just_missing = just_missing

    def _spacy_parse(self):
        if self.from_str:
            # todo: what is the dot, path, gonna be for? need tests for from string
            args = (
                self.plain_corpus,
                ".",
                self.save_as,
                self.corpus_name,
                self.language,
                self.constituencies,
                self.speakers,
                ".",
                self.hocr
            )
            return self._process_string(*args)
        else:
            abspath = os.path.abspath(os.getcwd())
            fs = [os.path.join(abspath, f.path) for f in self.plain_corpus.files]
            # if just_missing mode is on (used in buzzword, we skip files that exist)
            input_format = "hocr" if self.plain_corpus.path.rstrip("/").endswith("hocr") else "txt"
            if self.just_missing:
                todo = []
                for f in fs:
                    parsed_path = f.replace(f".{input_format}", ".conllu").replace(f"/{input_format}/", "/conllu/")
                    if not os.path.isfile(parsed_path):
                        todo.append(f)
                fs = todo
            if self.files:
                paths = [os.path.abspath(p.path) for p in self.files]
                fs = [f for f in fs if f in paths]
            multiprocess = multi.how_many(self.multiprocess)
            chunks = np.array_split(fs, multiprocess)
            delay = (
                multi.parse(
                    x,
                    i,
                    self.save_as,
                    self.corpus_name,
                    self.language,
                    self.constituencies,
                    self.speakers,
                    self.plain_corpus.path
                )
                for i, x in enumerate(chunks)
            )
            Parallel(n_jobs=multiprocess)(delay)


    def _best_corpus_to_parse(self, collection):
        if getattr(collection, "hocr", None):
            return collection.hocr, True
        return collection.txt, False

    def run(self, corpus, save_as=None, files=[]):
        """
        Run the parsing pipeline

        Args:
           corpus (Corpus): plain data to process
           save_as (str): custom save path
           speakers (bool): look for speakers at start of line

        Return:
            Corpus: parsed corpus
        """
        from .corpus import Corpus, Collection
        from .file import File

        self.plain_corpus = corpus
        self.save_as = save_as
        self.ntokens = 0
        self.nsents = 0
        self.made_new_dir = False
        self.from_str = True
        self.files = files

        # get the corpus name and parsed name/path depending on obj type
        # it's a corpus, everything is easy
        # todo: cleanup when always using collection
        if isinstance(corpus, Collection):
            if not self.just_missing:
                assert not corpus.conllu, "Corpus is already parsed"
            self.plain_corpus, self.hocr = self._best_corpus_to_parse(corpus)
            self.corpus_name = corpus.name
            self.parsed_name = "conllu"
            self.parsed_path = os.path.join(corpus.path, "conllu")
            self.from_str = False
        elif isinstance(corpus, File):
            corpus = Collection(corpus.path.split("/txt/", 1)[0])
            self.plain_corpus, self.hocr = self._best_corpus_to_parse(corpus)
            self.corpus_name = corpus.name
            self.parsed_name = "conllu"
            self.parsed_path = os.path.join(corpus.path, "conllu")
            self.from_str = False
        elif isinstance(corpus, Corpus):
            if not self.just_missing:
                assert not corpus.is_parsed, "Corpus is already parsed"
            self.hocr = self.path.rstrip("/").endswith("/hocr")
            self.corpus_name = corpus.name
            self.parsed_name = "conllu"
            self.parsed_path = os.path.join(os.path.dirname(corpus.path), self.parsed_name)
            self.from_str = False
        # it's a string, and the savename was provided
        elif isinstance(self.save_as, str):
            # todo, self.hocr etc
            self.corpus_name = self.save_as
            self.parsed_name = "conllu"
            self.parsed_path = os.path.join(os.path.dirname(corpus.path), self.parsed_name)
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
        return parsed


if __name__ == "__main__":
    from buzz.corpus import Corpus

    kwargs = _parse_cmd_line()
    corpus = Corpus(kwargs.pop("path"))
    corpus.parse(**kwargs)
