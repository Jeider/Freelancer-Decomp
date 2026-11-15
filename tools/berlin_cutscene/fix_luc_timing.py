"""Remove only the premature transition to Luc in the installed scene."""
from pathlib import Path
import sys

target = Path('D:/Games/FL_MOD/Assets/Pythonlancer/story/cutscenes/story_scenes/m01_berlin.py')
raw = target.read_bytes()
newline = b'\r\n' if b'\r\n' in raw else b'\n'
old = newline.join([
    b'        # Source facial window: 6s; following pause/overlap: -2s.',
    b'        main_group.append_time(-2)',
])
new = newline.join([
    b'        # Source facial window: 6s; following pause/overlap: 0s.',
    b'        # Luc waits for Trent; do not restore the old two-second overlap.',
])
assert raw.count(old) == 1, 'Expected transition not found; source needs review'
updated = raw.replace(old, new, 1)
compile(updated, str(target), 'exec')
if '--apply' in sys.argv:
    assert target.read_bytes() == raw, 'Source changed during preparation'
    target.write_bytes(updated)
    assert target.read_bytes() == updated
    print('Applied: Luc now starts after Trent finishes speaking.')
else:
    print('Validated: removes only the two-second rewind after Trent line 30.')
