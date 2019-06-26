#!/usr/bin/env python

# flake8: noqa

import re
from collections import defaultdict

CAMERA_ANGLE = '^([A-Z -\']+).*$'

SPEAKER = '                    (.*)'

STAGE_DIR = '^(\s.*)\n\n'

CAMERA_TECH = {'ZOOM', 'PAN', 'FADE IN', 'CAMERA', 'DOLLY', 'HIGH ANGLE', 'LOW ANGLE', 'CLOSE_UP'}

START_OF_DIRECTION = '^[a-zA-Z0-9"\'].*[a-z]'


def dict_to_meta(d):
    out = '<metadata '
    for k, v in d.items():
        if v is True or v is False:
            v = str(v).lower()
        if v is None:
            v = 'null'
        piece = '{}="{}" '.format(str(k).strip(), str(v).replace('"', "'").strip())
        out += piece
    return out.strip() + '>'


def parse_loc(text, scene_number):
    loc, setting = text.split(': ', 1)
    setting, time = setting.rsplit('--', 1)
    return dict(time=time.strip(), loc=loc, setting=setting.strip(), scene=scene_number)


def get_dialogue(dialogue, meta):
    """
    Return dialogue as string plus xml metadata
    """
    meta = meta.copy()
    text_lines = list()
    text_space = '          '
    direct = '                ('
    directions = dict()
    text = [i for i in dialogue.splitlines() if i.startswith(text_space)]
    if not text:
        return

    # get all text lines out, and stage directions into a dict
    for i, line in enumerate(text):
        if not line.startswith(direct):
            text_lines.append((i, line.strip()))
        else:
            directions[i] = line.strip('() ')

    # add stage directions to the right place
    re_ordered = []
    strung = str()
    for i, line in text_lines:
        strung += line.strip() + ' '
        direction = directions.get(i + 1)
        if direction:
            meta['direction'] = direction
            metas = dict_to_meta(meta)
            form_line = '{}. {}'.format(strung.strip(), metas)
        else:
            form_line = line.strip()
        re_ordered.append(form_line)

    strung = ' '.join(re_ordered).strip()
    if strung.strip()[-1] != '>' and '<metadata' not in strung:
        meta.pop('direction', None)
        metas = dict_to_meta(meta)
    else:
        metas = ''
    strung = strung.replace('  ', ' ')
    return strung.strip()
    return '{} {}'.format(strung, metas).strip()


def parse_section(shot, meta, line_number):
    meta = meta.copy()
    before_dialogue = shot.split('                    ', 1)[0]
    camera_angle = re.search(CAMERA_ANGLE, before_dialogue, re.MULTILINE)
    angle = camera_angle.group(1) if camera_angle else None
    if angle and any(i in angle for i in CAMERA_TECH):
        if len(angle) == 25:
            angle += '...'
        meta['camera_angle'] = angle
        before_dialogue = re.sub(camera_angle.group(0), '', before_dialogue)
    meta['speaker'] = 'stage_direction'
    line_meta = dict_to_meta(meta)
    direction = [i for i in before_dialogue.splitlines() if i and re.search(START_OF_DIRECTION, i)]
    direction = ' '.join(direction).replace('  ', ' ').strip()
    if direction:
        direction = '{} {}'.format(direction, line_meta)
    speaker = re.search(SPEAKER, shot, re.MULTILINE)
    if not speaker:
        return direction, None, None
    speaker = speaker.group(1)
    speak_info = re.search(' \((.*?)\)', speaker)
    speak_info = speak_info.group(1) if speak_info else None
    while speak_info:
        if speak_info in {'CONT\'D)', 'MORE'}:
            speak_info = None
        meta['voice_over'] = True
        meta['off_screen'] = True
        speech_type = dict(vo='voice-over', os='off-screen')
        speak_info = speech_type.get(speak_info.lower(), speak_info.lower())
        break
    try:
        dialogue, leftover = shot.split(speaker, 1)[-1].split('\n\n', 1)
    except ValueError:
        dialogue = shot.split(speaker, 1)[-1].rstrip('\n\n')
        leftover = ''

    meta['speaker'] = speaker.split(' (')[0]
    meta['line'] = line_number
    text = get_dialogue(dialogue, meta)
    meta.pop('direction', None)
    text_meta = dict_to_meta(meta)
    if text:
        text = '{} {}'.format(text, text_meta)

    return direction, text, leftover


def parse_scene(text, number, line_number):
    """
    Give back all text correctly formatted, and the line
    we are up to for the next scene
    """
    out_text = list()
    split_text = text.splitlines()
    location = parse_loc(split_text[0], number)
    shot = '\n'.join(split_text[2:])
    while shot:
        direction, text, shot = parse_section(shot, location, line_number)
        if direction:
            out_text.append(direction)
        if text:
            out_text.append(text)
            line_number += 1
    return '\n'.join(out_text), line_number


def normalise_data(text):
    text = re.sub('\n\n+', '\n\n', text)
    text = text.splitlines()
    page_num = '                                                '
    text = [i for i in text if not i.startswith(page_num)]
    text = '\n'.join(text)
    return text.split('CUT TO:', 3)[-1].lstrip('\n')


def make_filename(line, num):
    num = str(num).zfill(2)
    name = line.lower().replace(' ', '-')
    filename = '{}-{}.txt'.format(num, name)
    return filename


def get_scenes(text):
    """
    so unproud of this
    """
    count = 1
    scenes = defaultdict(str)
    for line in text.splitlines():
        match = re.search('^(INT|EXT): (.*?)--', line)
        if match:
            title = make_filename(match.group(2), count)
            count += 1
        scenes[title] += line + '\n'
    return scenes


def main():
    line_number = 1
    output = list()
    with open('do-the-right-thing.txt', 'r') as fo:
        data = fo.read()
    data = normalise_data(data)
    with open('do-the-right-thing-norm.txt', 'w') as fo:
        data = fo.write(data)
    with open('do-the-right-thing-norm.txt', 'r') as fo:
        data = fo.read()
    scenes = get_scenes(data)
    each_scene = enumerate(sorted(scenes.items()), start=1)
    for scene_num, (scene_name, scene) in each_scene:
        print('Doing scene {}: {}'.format(scene_num, scene_name))
        text, line_number = parse_scene(scene, scene_num, line_number)
        fpath = 'do-the-right-thing/{}'.format(scene_name.lower())
        with open(fpath, 'w') as fo:
            fo.write(text.strip() + '\n')


main()
