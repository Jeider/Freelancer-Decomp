"""Adds the keys the repo's bin/port.ini has and the game's port.ini lacks, with their default
value and comment, at the end of the matching section (a missing section is appended). Existing
keys and values are never touched. usage: port_ini_sync.py <repo port.ini> <game port.ini>
(python -I tools/port_ini_sync.py bin/port.ini D:/games/FL_MOD/bin/port.ini; a backup is written first)"""
import re
import shutil
import sys
import time

repo_path, game_path = sys.argv[1], sys.argv[2]


def parse(lines):
    """[(section, key, line)] in file order, plus each section's last line index."""
    section = None
    entries, last = [], {}
    for i, line in enumerate(lines):
        m = re.match(r'\s*\[(.+?)\]', line)
        if m:
            section = m.group(1)
            last[section] = i
            continue
        if section is not None:
            if line.strip():
                last[section] = i
            m = re.match(r'\s*([A-Za-z0-9_.]+)\s*=', line)
            if m:
                entries.append((section, m.group(1), line.rstrip('\r\n')))
    return entries, last


repo_lines = open(repo_path, encoding='utf-8', errors='replace', newline='').read().splitlines()
raw = open(game_path, encoding='utf-8', errors='replace', newline='').read()
game_lines = raw.splitlines()
repo_entries, _ = parse(repo_lines)
game_entries, game_last = parse(game_lines)
have = {(s, k) for s, k, _ in game_entries}

missing = {}
for section, key, line in repo_entries:
    if (section, key) not in have:
        missing.setdefault(section, []).append(line)
if not missing:
    print('nothing to add')
    sys.exit(0)

backup = game_path + '.before_defaults_' + time.strftime('%Y%m%d_%H%M%S')
shutil.copyfile(game_path, backup)
# Insert from the bottom up so earlier indices stay valid; new sections go at the end.
for section in sorted((s for s in missing if s in game_last), key=lambda s: -game_last[s]):
    at = game_last[section] + 1
    game_lines[at:at] = missing[section]
for section in missing:
    if section not in game_last:
        game_lines += ['', '[' + section + ']'] + missing[section]
open(game_path, 'w', encoding='utf-8', newline='').write('\r\n'.join(game_lines) + '\r\n')
for section, lines in missing.items():
    print('[%s] +%d: %s' % (section, len(lines), ' '.join(re.match(r'\s*([A-Za-z0-9_.]+)', l).group(1) for l in lines)))
print('backup:', backup)
