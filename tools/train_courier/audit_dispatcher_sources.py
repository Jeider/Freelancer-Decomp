"""Read-only inventory for migrating Russian dispatcher UTFs to loose WAVs."""
import json
from pathlib import Path
from courier_ru_bank import audio_key, entries, GAME, ROOT
from export import sections, one


def main():
    output={}
    for voice, ini in [('dispatcher01','voices_space_male'),('dispatcher02','voices_space_female'),('dispatcher03','voices_space_female')]:
        active='';codes=set()
        for kind,row in sections(GAME/f'DATA/AUDIO/{ini}.ini'):
            if kind=='voice':active=one(row,'nickname')
            elif kind=='sound' and active==voice:codes.add(one(row,'msg'))
        archive=GAME/f'DATA/AUDIO/{voice}.utf'
        bank=entries(archive.read_bytes()) if archive.exists() else {}
        sources={p.stem.lower():str(p) for p in (GAME/'Assets/PILOTS'/voice).rglob('*') if p.suffix.lower() in ('.wav','.mp3')}
        loose={p.stem.lower():str(p) for p in (GAME/'DATA/AUDIO/MOD'/voice).glob('*.wav')}
        missing=[c for c in sorted(codes) if audio_key(c).lower() not in bank and c.lower() not in sources and c.lower() not in loose]
        output[voice]=dict(registered=len(codes),archive=len(bank),sources=len(sources),loose=len(loose),missing=missing)
        print(voice,json.dumps(output[voice],ensure_ascii=False))
    (ROOT/'out/train_courier/audio_ru/dispatcher_sources_audit.json').write_text(json.dumps(output,indent=2),encoding='utf-8')


if __name__=='__main__':main()
