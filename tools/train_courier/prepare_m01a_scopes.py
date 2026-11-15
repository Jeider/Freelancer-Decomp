"""Prepare an audited m01a-only scope proposal, never write live templates or DATA."""
from pathlib import Path
import difflib
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = Path('D:/Games/FL_MOD/Assets/Pythonlancer/templates')
OUT = ROOT/'out/m01a_scopes'
LOCAL = {
    'missions/m01/m01a.ini': {
        'real_mission_init', 'init_bar', 'START_vendor_do_accept',
        'return_to_deck', 'Player_on_berlin_planet',
    },
    'missions/m01/_intro.ini': {'BARMAN_init', 'INTRO_CITYSCAPE'},
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    patch = []
    report = {'status': 'PROPOSAL_NOT_RUNTIME_READY', 'sources': {}, 'local': LOCAL.copy()}
    report['local'] = {p: sorted(v) for p, v in LOCAL.items()}
    for relative, names in LOCAL.items():
        path = TEMPLATES/relative
        raw = path.read_bytes()
        text = raw.decode('utf-8')
        found = set()
        def annotate(match):
            name = match.group(2).strip()
            if name not in names:
                return match.group(0)
            assert name not in found, 'Duplicate trigger: '+name
            found.add(name)
            newline = '\r\n' if '\r\n' in text else '\n'
            return match.group(0)+newline+'execution_scope = local'
        proposed = re.sub(r'(^nickname[ \t]*=[ \t]*([^\r\n]+))', annotate, text, flags=re.M)
        assert found == names, (relative, names-found)
        destination = OUT/'proposal'/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(proposed.encode('utf-8'))
        patch += difflib.unified_diff(text.splitlines(True), proposed.splitlines(True),
                                     fromfile='a/templates/'+relative, tofile='b/templates/'+relative)
        report['sources'][str(path)] = hashlib.sha256(raw).hexdigest()
    (OUT/'m01a.patch').write_bytes(''.join(patch).replace('\r\n', '\n').encode('utf-8'))
    (OUT/'manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('Prepared 7 local trigger annotations in m01a and its exclusive intro include.')
    print('NOT APPLIED: runtime lacks cross-scope routing and personal mission acceptance/objectives.')


if __name__ == '__main__':
    main()
