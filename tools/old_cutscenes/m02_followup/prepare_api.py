"""Stage the explicit native API for a standalone cutscene character."""
import ast
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PL = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
OUT = REPO / 'out/story_cutscenes/m02_followup'
EDITS = {
    'story/cutscenes/content.py': [
        ('facial_indexes=1, *args, **kwargs):', 'facial_indexes=1, bind_actor=True, *args, **kwargs):'),
        ("        self.actor = actor\n        name = f'Char_{self.actor.NAME}'",
         "        self.actor = actor\n        self.bind_actor = bind_actor\n        name = f'Char_{self.actor.NAME}'"),
        ("        params['actor'] = self.actor.get_game_actor()",
         "        params['actor'] = self.actor.get_game_actor() if self.bind_actor else None"),
    ],
    'templates/cutscenes/entity/character.lua': [
        ('        Actor="{{ actor }}",', '        {% if actor %}Actor="{{ actor }}",{% endif %}'),
    ],
}
manifest = []
for relative, replacements in EDITS.items():
    target = PL / relative
    original = target.read_bytes()
    newline = b'\r\n' if b'\r\n' in original else b'\n'
    result = original
    for old, new in replacements:
        old, new = (s.encode().replace(b'\n', newline) for s in (old, new))
        assert result.count(old) == 1, (relative, old)
        result = result.replace(old, new)
    if relative.endswith('.py'):
        ast.parse(result.decode('utf-8-sig'))
    stage = OUT / 'api' / relative
    stage.parent.mkdir(parents=True, exist_ok=True)
    stage.write_bytes(result)
    manifest.append({'stage': str(stage), 'target': str(target),
                     'before': hashlib.sha256(original).hexdigest(),
                     'after': hashlib.sha256(result).hexdigest()})
(OUT / 'api_plan.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('Staged Character(bind_actor=False) and its native template; defaults unchanged.')
