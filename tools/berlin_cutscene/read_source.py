"""Structural read-only import of literal tables in the Berlin source THN."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
PYTHONLANCER = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
SOURCE = Path('D:/Games/FL_MOD/DATA/SCRIPTS/MOD/m01_berlin_bar.thn')
sys.path.insert(0, str(PYTHONLANCER))
from story.cutscenes.thn_parser import MotionReader


def read():
    text = SOURCE.read_text(encoding='utf-8-sig')
    reader = MotionReader(text)
    tokens = reader.tokens

    def value(a, b):
        if tokens[a].value == '{' and reader.pairs.get(a) == b - 1:
            fields = reader.fields(a)
            named = [tokens[x].kind == 'name' and y - x >= 3 and tokens[x + 1].value == '=' for x, y in fields]
            if any(named):
                assert all(named), (a, b)
                return {tokens[x].value: value(x + 2, y) for x, y in fields}
            return [value(x, y) for x, y in fields]
        if b == a + 1 and tokens[a].kind == 'string':
            return tokens[a].value
        raw = ''.join(t.value for t in tokens[a:b])
        try:
            number = float(raw)
            return int(number) if number.is_integer() else number
        except ValueError:
            return raw

    result = {}
    for i, token in enumerate(tokens[:-2]):
        if token.value in ('entities', 'events') and tokens[i + 1].value == '=' and tokens[i + 2].value == '{':
            result[token.value] = value(i + 2, reader.pairs[i + 2] + 1)
    result['duration'] = float(tokens[2].value)
    return result


if __name__ == '__main__':
    data = read()
    (ROOT / 'source.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
    for entity in data['entities']:
        print('ENTITY', entity['entity_name'], entity['type'], json.dumps({k:v for k,v in entity.items() if k not in ('entity_name','type','spatialprops')}))
    for i, event in enumerate(data['events']):
        print('EVENT', i, json.dumps(event))
    print('DURATION', data['duration'])
