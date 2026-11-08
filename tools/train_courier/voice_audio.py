"""Validate installed English clips and measure RIFF durations without conversion."""
from pathlib import Path
import re
import struct

from dispatcher_en import VOICE, clips, REPOSITION_FAMILIES
from export import sections, one


def wav_duration(path):
    raw=path.read_bytes()
    assert raw[:4]==b'RIFF' and raw[8:12]==b'WAVE', f'Not a RIFF WAVE: {path}'
    assert struct.unpack_from('<I',raw,4)[0]+8==len(raw), f'Truncated RIFF: {path}'
    chunks={};offset=12
    while offset+8<=len(raw):
        name,size=struct.unpack_from('<4sI',raw,offset)
        assert offset+8+size<=len(raw), f'Truncated WAVE chunk: {path}'
        chunks[name]=raw[offset+8:offset+8+size];offset+=8+size+(size&1)
    fmt=chunks[b'fmt '];kind,channels,rate,byte_rate,align,bits=struct.unpack_from('<HHIIHH',fmt)
    assert channels and rate and chunks.get(b'data'), f'Empty audio: {path}'
    if kind==1:
        assert align and len(chunks[b'data'])%align==0
        samples=len(chunks[b'data'])//align
    else:
        # Pythonlancer emits MP3-in-WAV (format 0x55). fact stores the decoded
        # sample count; Python's wave module only accepts uncompressed PCM.
        assert kind==0x55 and len(chunks.get(b'fact',b''))>=4, f'Unsupported WAVE: {path}'
        samples=struct.unpack_from('<I',chunks[b'fact'])[0]
    assert samples>0, f'Empty audio: {path}'
    return samples/rate


def english_sounds(game,path=None):
    path=path or game/'DATA/AUDIO/voices_space_male.ini'
    active='';sounds={}
    for kind,values in sections(path):
        if kind=='voice': active=one(values,'nickname')
        elif kind=='sound' and active==VOICE:
            name=one(values,'msg')
            if name in sounds:
                assert one(sounds[name],'file')==one(values,'file'), f'Ambiguous English clip: {name}'
            sounds[name]=values
    return sounds


def reposition_ready(game):
    sounds=english_sounds(game)
    required={name for name,_ in clips(REPOSITION_FAMILIES)}
    missing=[]
    for name in sorted(required):
        relative=one(sounds.get(name,{}),'file')
        path=game/'DATA'/relative.replace('\\','/') if relative else None
        if path is None or not path.is_file():missing.append(name)
        else:wav_duration(path)
    if missing:print(f'Reposition audio pending: {len(missing)} of 20 registered clips missing; existing order audio remains enabled')
    return not missing


def prepare_english(game,catalog,path=None,reposition=False):
    path=path or game/'DATA/AUDIO/voices_space_male.ini'
    sounds=english_sounds(game,path)
    courier={name for name,_ in clips()}
    if reposition:courier.update(name for name,_ in clips(REPOSITION_FAMILIES))
    required=courier|{b['voice_name'] for b in catalog['bases'].values()}|{
        c['voice_name'] for c in catalog['commodities'].values()}
    assert required<=sounds.keys(), 'Missing English voice entries: '+', '.join(sorted(required-sounds.keys()))
    durations={}
    for name in required:
        relative=one(sounds[name],'file')
        assert relative, f'Expected existing file-backed English clip: {name}'
        durations[name]=wav_duration(game/'DATA'/relative.replace('\\','/'))
    text=path.read_text(encoding='utf-8-sig')
    blocks=re.split(r'(?m)(?=^\[)',text);active='';changed=0
    for index,block in enumerate(blocks):
        if block.lower().startswith('[voice]'):
            active=re.search(r'(?mi)^nickname\s*=\s*([^\r\n]+)',block).group(1).strip()
        elif active==VOICE and block.lower().startswith('[sound]'):
            match=re.search(r'(?mi)^msg\s*=\s*([^\r\n]+)',block)
            if match and match.group(1).strip() in courier:
                name=match.group(1).strip()
                line=f'duration = {durations[name]:.6f}'
                blocks[index]=re.sub(r'(?mi)^duration\s*=[^\r\n]*',lambda _:line,block)
                assert line in blocks[index], f'Missing duration field: {name}'
                changed+=1
    assert changed>=len(courier)
    print(f'PASS: {len(courier)} English courier clips + {len(required)-len(courier)} base/commodity names; RIFF audio valid; measured durations')
    return ''.join(blocks).encode('utf-8')
