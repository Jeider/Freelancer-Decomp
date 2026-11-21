"""Temporarily enable the existing bounded rock-route log; never launch the game."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/graphics_settings/nebula_asteroid_mesh/fog_coverage/physical_order/trace'
CONFIG = Path('D:/Games/FL_MOD/bin/port.ini')
LOG = Path.home() / 'AppData/Local/Freelancer-Decomp/Diagnostics/rock_debug.txt'
PLAN = OUT / 'trace.json'
PATTERN = rb'(?m)^(rock_debug[ \t]*=[ \t]*)([01])(?=[ \t;\r\n])'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = CONFIG.read_bytes()
    matches = list(re.finditer(PATTERN, data))
    assert len(matches) == 1, 'Expected one rock_debug setting'
    match = matches[0]
    if '--prepare' in sys.argv:
        assert not PLAN.exists(), 'Keep the pending capture state'
        plan = {'before': digest(data), 'original': match[2].decode(),
                'log_offset': LOG.stat().st_size if LOG.exists() else 0,
                'enabled': False, 'restored': False}
        PLAN.write_text(json.dumps(plan, indent=2))
        print('Prepared rock_debug=1; no rendering setting changes')
        return
    plan = json.loads(PLAN.read_text())
    if '--enable' in sys.argv:
        assert digest(data) == plan['before'], 'Configuration changed since preparation'
        replacement = b'1'
    elif '--restore' in sys.argv:
        assert plan['enabled'] and not plan['restored']
        replacement = plan['original'].encode()
        if LOG.exists():
            content = LOG.read_bytes()
            assert len(content) >= plan['log_offset'], 'Diagnostic log was replaced'
            (OUT / 'rock_debug.txt').write_bytes(content[plan['log_offset']:])
    else:
        raise SystemExit('Use --prepare, --enable or --restore')
    updated = data[:match.start(2)] + replacement + data[match.end(2):]
    assert CONFIG.read_bytes() == data
    try:
        CONFIG.write_bytes(updated)
        assert CONFIG.read_bytes() == updated
    except BaseException:
        CONFIG.write_bytes(data)
        raise
    plan['enabled' if '--enable' in sys.argv else 'restored'] = True
    PLAN.write_text(json.dumps(plan, indent=2))
    print('Enabled existing rock route log' if '--enable' in sys.argv else 'Captured log and restored rock_debug')

if __name__ == '__main__':
    main()
