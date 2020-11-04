"""
Do OCR from PDF files, saving as text corpus, possibly with coordinates
"""

import os
import re
from .utils import _get_ocr_engine


def _pdf_to_tif(collection):
    from pdf2image import convert_from_path
    from buzz import Corpus

    os.makedirs(collection.path.rstrip("/") + "/tiff", exist_ok=True)

    for pdf in collection.pdf.files:
        pdf_path = pdf.path
        images = convert_from_path(pdf_path)
        if len(images) == 1:
            images[0].save(pdf_path.replace("pdf", "tiff"))
        else:
            for i, img in enumerate(images):
                replace = f"-page-{str(i+1).zfill(3)}.tiff"
                out_path = pdf_path.replace("/pdf/", "/tiff/").replace(".pdf", replace)
                print(f"Saving {out_path}...")
                img.save(out_path)

    collection.tiff = Corpus(collection.pdf.path.replace("pdf", "tiff"))
    return collection


def _extract(collection,
             language="en",
             multiprocess=False,
             coordinates=True,
             page_numbers=False):

    import pyocr
    import pytesseract
    from pytesseract import Output
    from PIL import Image
    from .corpus import Corpus

    lang_chosen = {"en": "eng", "de": "deu"}

    if not collection.tiff and collection.pdf:
        collection = _pdf_to_tif(collection)

    os.makedirs(collection.path.rstrip("/") + "/txt", exist_ok=True)

    for tif in collection.tiff.files:
        tif_path = tif.path

        pdf_path = (
            tif_path.replace("/tiff/", "/pdf/")
            .replace("/tif/", "/pdf/")
            .replace(".tiff", ".pdf")
            .replace(".tif", ".pdf")
        )

        # make pdf if need be
        if not os.path.isfile(pdf_path):
            image = Image.open(tif_path)
            print(f"Saving {pdf_path}...")
            image.save(pdf_path)

        ocr_engine, lang_chosen = _get_ocr_engine(language)

        # there is no OCRUpdate for this data; therefore we do OCR and save it
        plaintext = ocr_engine.image_to_string(
            Image.open(tif_path), lang=lang_chosen, builder=pyocr.builders.TextBuilder(),
        )

        if coordinates:
            try:
                d = pytesseract.image_to_data(
                    Image.open(tif_path),
                    output_type=Output.DICT,
                    lang=lang_chosen,
                )
            except:  # no text at all
                d = {}

            n_boxes = len(d.get("level", []))

            text_out = ""
            prev_height = None
            # do not seek to optimise me; much trial and error was used to
            # correctly handle newlines, spaces, and that sort of thing.
            # refactor should preserve all functionality as is
            for i in range(n_boxes):
                text = d["text"][i]
                # if line ending, but not sentence ending
                if not len(text) and prev_height != d["height"][i]:
                    text_out += "\n"  # or just continue?
                    continue
                x, y, w, h = (d[loc][i] for loc in ["left", "top", "width", "height"])
                prev_height = h
                text = f'<meta box_x={x} box_y={y} box_w={w} box_h={h}>{text}</meta> '
                # d['conf'][i] == certainty
                text_out += text
            plaintext = text_out.strip()
            plaintext = plaintext.replace("</meta> \n<meta", "</meta> <meta")
            plaintext = re.sub("\n{2,}", "\n", plaintext)

        if page_numbers:
            pass

        # todo: postprocessing here

        txt_path = (
            tif_path.replace("/tiff/", "/txt/")
            .replace("/tif/", "/txt/")
            .replace(".tiff", ".txt")
            .replace(".tif", ".txt")
        )

        if os.path.isfile(txt_path):
            raise ValueError(f"Already exists: {txt_path}")
        with open(txt_path, "w") as fo:
            fo.write(plaintext)

    collection.txt = Corpus(collection.path.rstrip("/") + "/txt")
    return collection
