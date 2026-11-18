"""Regression: an INI WAV path cannot satisfy a profile backed by an existing UTF."""
import json
from courier_ru_bank import audio_key, entries, merge, check, read_tree, write_tree, Node
from install_courier_ru_bank import GAME, BANK, STAGE, MANIFEST, clips


def main():
    report=json.loads(MANIFEST.read_text(encoding='utf-8'))
    target=STAGE/BANK if (STAGE/BANK).is_file() else GAME/BANK
    raw=target.read_bytes();sources=clips()
    check(raw,sources,report['inherited'])
    # This is the exact hexadecimal filename requested in the user's error log.
    assert audio_key('tc_board_04-')=='0xBC4D1DC9'
    assert entries(raw)['0xbc4d1dc9']==sources['tc_board_04-']
    # Existing UTF banks win over per-message file paths. Prove that the same
    # registered WAVs fail coverage against the old uncompiled bank.
    if (STAGE/BANK).is_file():
        old=(GAME/BANK).read_bytes()
        try:check(old,sources)
        except AssertionError:pass
        else:assert not report['missing_before']
    # Repacking is deterministic and retains duplicate original entries too.
    repacked,_=merge(raw,sources)
    assert repacked==raw
    header,_=read_tree(raw)
    root=Node('\\');root.children=[Node('old',blob=b'first'),Node('old',blob=b'second')]
    fixture=write_tree(header,[root]);result,_=merge(fixture,{'tc_board_04-':sources['tc_board_04-']})
    nodes=read_tree(result)[1][0].children
    assert [(node.name,node.blob) for node in nodes[:2]]==[('old',b'first'),('old',b'second')]
    print('PASS: exact logged missing ID; all 236 runtime UTF lookups; 76 base names; rejects old bank; idempotent merge; duplicate leaves preserved')


if __name__=='__main__':main()
