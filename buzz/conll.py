import shlex
import re
from .constants import MAX_SPEAKERNAME_SIZE


def make_meta_dict_from_sent(text):
    from .utils import cast
    metad = dict()
    if '<metadata' in text:
        relevant = text.strip().rstrip('>').rsplit('<metadata ', 1)
        try:
            shxed = shlex.split(relevant[-1])
        except:
            shxed = relevant[-1].split("' ")
        for m in shxed:
            try:
                k, v = m.split('=', 1)
                v = v.replace(u"\u2018", "'").replace(u"\u2019", "'")
                v = v.strip("'").strip('"')
                metad[k] = cast(v)
            except ValueError:
                continue
    # speaker seg part
    regex = r'(^[a-zA-Z0-9-_]{,%d}?):..+' % MAX_SPEAKERNAME_SIZE
    speaker_regex = re.compile(regex)
    match = re.search(speaker_regex, text)
    if not match:
        return metad
    speaker = match.group(1)
    metad['speaker'] = speaker
    return metad


def get_metadata(stripped,
                 plain,
                 sent_offsets,
                 first_line=False,
                 has_fmeta=False):
    """
    Take offsets and get a speaker ID or metadata from them
    """
    if not stripped and not plain:
        return dict()

    # are we getting file or regular metadata?
    if not first_line:
        start, end = sent_offsets
    else:
        start = 0
        # if there's newline, stop there, or else it's just the end of the text
        try:
            end = stripped.index('\n')
        except:
            end = len(stripped) - 1
    # get everything before this text
    cut_old_text = stripped[:start]
    # count which line the sent must be on from the old text
    line_index = cut_old_text.count('\n')
    if has_fmeta and not first_line:
        line_index += 1
    if first_line:
        line_index = 0
    # lookup this text
    text_with_meta = plain.splitlines()[line_index]
    return make_meta_dict_from_sent(text_with_meta)
