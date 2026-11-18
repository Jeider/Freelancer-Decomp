"""Read current catalog and author the missing RU cargo vocabulary; no DATA writes."""
import contextlib
import json
import os
from pathlib import Path
import sys
from export import sections, one

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/train_courier/audio_ru'
GAME = Path('D:/Games/FL_MOD')
PROJECT = GAME / 'Assets/Pythonlancer'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(PROJECT))
    OUT.mkdir(parents=True, exist_ok=True)
    os.chdir(PROJECT)
    with (OUT / 'vocabulary_core.log').open('w', encoding='utf-8') as log, contextlib.redirect_stdout(log):
        from core import get_core
        core = get_core()
    goods = {good.get_msg_id_prefix(): good for good in core.store.get_commodities()}
    bases = {base.get_base_msg_relative(): base for base in core.universe.get_bases()}
    needed = {one(values, 'voice_name') for kind, values in sections(GAME / 'DATA/MISSIONS/TrainCourier/catalog.ini')
              if kind in ('courierpoint', 'courierparking', 'couriercommodity')}
    active = ''
    present = set()
    for kind, values in sections(GAME / 'DATA/AUDIO/voices_space_male.ini'):
        if kind == 'voice':
            active = one(values, 'nickname')
        elif kind == 'sound' and active == 'dispatcher01':
            present.add(one(values, 'msg'))
    result = []
    for code in sorted(needed - present):
        source = goods.get(code) or bases.get(code)
        assert source is not None, code
        text = source.get_ru_name().get_ru().replace('+', '')
        # Expand UI abbreviations for speech without changing item names.
        text = text.replace('солн. генератора', 'солнечного генератора')
        if code == 'gcs_gen_commodity_comm_roid_berilium':
            text = 'Бериллий'
        result.append(dict(id=code, text=text, actor='MaleDispatcher', bank='vocabulary'))
    (OUT / 'vocabulary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'vocabulary_audit.json').write_text(json.dumps(dict(required=sorted(needed),
        inherited=sorted(needed & present), new=sorted(needed - present)), indent=2), encoding='utf-8')
    print('Required:', len(needed), 'inherited:', len(needed & present), 'new:', len(result))
    for row in result:
        print(row['id'], row['text'])


if __name__ == '__main__':
    main()
