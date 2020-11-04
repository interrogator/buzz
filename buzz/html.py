import re
from collections import OrderedDict
from html.parser import HTMLParser

from buzz.utils import cast

SPEAKER_REGEX = re.compile(r"^([A-Z0-9-_]{1,30}):\s*", re.MULTILINE)


class MetadataStripper(HTMLParser):
    """
    Strip HTML/XML properly
    """

    def __init__(self, speakers=True):
        super().__init__()
        self.text = str()
        self.speakers = speakers

    def handle_data(self, data):
        if not self.getpos()[1] and self.speakers:
            data = re.sub(SPEAKER_REGEX, "", data)
        self.text += data


class InputParser(HTMLParser):
    """
    Get metadata out of a line of text
    """

    def __init__(self, speakers=True):
        super().__init__()
        self.tmp = None
        self.sent_meta = dict()
        self.text = None
        self.num_elements = 0
        self.num_done = 0
        self.speakers = speakers

    def _has_sent_meta(self):
        # todo: fix this to work even with coordinate data
        return False
        n_meta = self.text.count("<meta")
        n_end = self.text.count("</meta")
        return bool(n_meta - n_end)

    def handle_starttag(self, tag, attrs):
        self.tmp = dict()
        if tag in {"metadata", "meta"}:
            for k, v in attrs:
                self.tmp[k.strip().replace("-", "_")] = cast(v)
        is_last = self.num_elements == self.num_done + 1
        if is_last and self._has_sent_meta():
            self.sent_meta = {**self.tmp, **self.sent_meta}
        self.num_done += 1

    def feed(self, text, *args, **kwargs):
        self.text = text
        self.num_elements = text.count("<meta")
        return super().feed(text, *args, **kwargs)

    def handle_data(self, data):
        """
        data is the string of plain text
        """
        offset = self.getpos()[1]
        if not offset and self.speakers:
            found_speaker = re.search(SPEAKER_REGEX, data)
            if found_speaker:
                self.sent_meta["speaker"] = found_speaker.group(1)
