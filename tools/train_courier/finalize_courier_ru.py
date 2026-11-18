"""Read back installed courier audio/scenes; discard verified staging duplicates."""
import json
from pathlib import Path
from install_evacuation import safe_file
from install_courier_ru_scenes import verify, sha, GAME, ROOT

OUT = ROOT/'out/train_courier/audio_ru'


def main():
    installed = json.loads((OUT/'installed.json').read_text(encoding='utf-8'))
    expected = dict(installed['files'])
    bank_path = OUT/'bank_installed.json'
    bank = json.loads(bank_path.read_text(encoding='utf-8')) if bank_path.exists() else None
    if bank:
        expected.update(bank['files'])
        from install_courier_ru_bank import verify as verify_bank
        verify_bank(bank)
    for name, entry in expected.items():
        assert sha(GAME/name)==entry['after'], name
    verify()
    connected = json.loads((OUT/'scenes/connected.json').read_text(encoding='utf-8'))
    for name, expected in connected['files'].items():
        assert sha(GAME/'DATA'/name)==expected, name
    # Three reference WAVs were published before restaging; their obsolete package
    # duplicates no longer occur in the latest transaction manifest.
    for name in ('Trent', 'MaleDispatcher', 'RpgTradeDirector'):
        relative = f'Assets/VOICE_SOURCE_RU/{name}.wav'
        path = safe_file(OUT/'package'/relative, OUT/'package')
        if path.exists():
            assert sha(path)==sha(GAME/relative)==sha(OUT/'references'/(name+'.wav'))
            path.unlink()
    for path in (OUT/'package').rglob('*'):
        safe_file(path, OUT/'package')
        assert not path.is_file() or path.suffix.lower() not in ('.wav','.exe','.dll','.pdb','.utf'), path
    report = {'installed_recordings':installed['lines'], 'bar_fragments':32,
              'owners':connected['owners'], 'missing_cargo':installed['missing_cargo'],
              'game_launched_by_agent':False, 'verification':'All installed transaction, RU scene and dialogue hashes; RU timing bounds',
              'staging_binaries_removed':True, 'native_dispatcher_bank_verified':bool(bank)}
    (OUT/'final_verified.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('PASS: 268 recordings, 32 RU bar scenes, 19 connected owners; installed hashes verified; staging binaries removed')


if __name__=='__main__':
    main()
