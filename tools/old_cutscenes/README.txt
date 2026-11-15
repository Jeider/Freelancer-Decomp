Pythonlancer old THN motion parsing

The staged sources replace the regex extractor in story/cutscenes/old_format.py
and add story/cutscenes/thn_parser.py. Existing delay, animation, props and facial
keys remain. Added targets contains all target names; parameters maps property
names to raw Lua values (last textual occurrence for repeated keys). props now
preserves the entire source table, including comments, escapes and whitespace.

The reader handles literal motion tables, nested properties, single/double/long
strings, line/long comments, signed decimal/exponent delays and trailing table
separators. It never executes Lua. Malformed or unsupported motion syntax raises
ThnParseError with line/column instead of quietly losing an event.

This is not a full Lua interpreter or a complete scene converter. Dynamic delay,
target and animation expressions are rejected. Other event types are not
converted by this motion-only API. Binary THN requires separate decompilation.

Check staged sources: python -B tools/old_cutscenes/check.py
Install: python -B tools/old_cutscenes/install.py
Check installed sources: python -B tools/old_cutscenes/check.py --installed

The check runs regression cases and all MOD THN files, comparing extracted
motions to active START_MOTION tokens. Two verified malformed existing sources
are pinned by SHA256 and exact error; unexpected failures still fail the check.
m05_equip_start.thn has an extra opening brace in a path event.
m05_equip_support.thn has a motion without targets at line 1371.
Neither source is modified. No final THN generation or DATA writes occur.
