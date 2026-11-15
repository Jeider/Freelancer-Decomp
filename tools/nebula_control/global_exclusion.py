"""Stage/install global exclusion defaults and Pythonlancer shell generation."""
import argparse
import json
from pathlib import Path
import re

import vienna as deployment
from pythonlancer_exclusion import prepare_exclusion_shells
from sphere_exterior import edit_section

ROOT, GAME = deployment.ROOT, deployment.GAME
OUT = ROOT/'out/global_exclusion'
deployment.OUT = OUT
deployment.STAGE = OUT/'staged'
VALUES = {'render_in_exclusion':'1', 'exclusion_march_distance':'6000',
          'exclusion_transition_fraction':'0.2', 'exclusion_density_scale':'0.15',
          'exclusion_core_haze':'0.04'}


def prepare():
    payload = {}
    for name in ('freelancer.exe', 'freelancer.pdb'):
        payload['bin/'+name] = (ROOT/'src/obj/train_courier/rpg1/bin'/name).read_bytes()
    shader = 'DATA_EXTRA/SHADERS/nebula_composite.hlsl'
    payload[shader] = (ROOT/shader).read_bytes()
    relative = deployment.VOLUME
    original = (GAME/relative).read_bytes()
    text = original.decode('utf-8-sig').replace('\r\n', '\n')
    text = edit_section(text, 'Nebula', None, VALUES)
    # The test profile now inherits the global policy, instead of pinning its old values.
    def inherit(match):
        if not re.search(r'(?im)^file\s*=\s*m11_vienna_nebula\s*$', match[0]):
            return match[0]
        result = match[0]
        for key in VALUES:
            result = re.sub(rf'(?im)^{key}\s*=[^\r\n]*\r?\n', '', result)
        return result
    text = re.sub(r'(?ims)^\[NebulaOverride\][^\r\n]*\r?\n.*?(?=^\[|\Z)', inherit, text)
    payload[relative] = text.replace('\n', '\r\n' if b'\r\n' in original else '\n').encode(
        'utf-8-sig' if original.startswith(b'\xef\xbb\xbf') else 'utf-8')
    pythonroot = 'Assets/Pythonlancer/'
    payload[pythonroot+'tools/nebula_exclusion.py'] = Path(__file__).with_name('pythonlancer_exclusion.py').read_bytes()
    relative = pythonroot+'tools/data_folder.py'
    original = (GAME/relative).read_bytes()
    text = original.decode('utf-8').replace('\r\n', '\n')
    old = "        nebula_file = self.get_solar() / 'NEBULA_MOD' / subfolder / f'{nebula_file_name}.ini'\n        nebula_file.write_text(content, encoding='utf-8')"
    new = "        from tools.nebula_exclusion import prepare_exclusion_shells\n        self.sync_data_file(\n            f'SOLAR/NEBULA_MOD/{subfolder}/{nebula_file_name}.ini',\n            prepare_exclusion_shells(content))"
    assert text.count(old) == 1 or new in text
    text = text.replace(old, new)
    payload[relative] = text.replace('\n', '\r\n' if b'\r\n' in original else '\n').encode('utf-8')
    shell_files = 0
    for path in (GAME/'DATA/SOLAR').rglob('*.ini'):
        original = path.read_bytes()
        if b'zone_shell' not in original.lower():
            continue
        encoding = 'utf-8-sig' if original.startswith(b'\xef\xbb\xbf') else 'utf-8'
        try:
            text = original.decode(encoding)
        except UnicodeDecodeError:
            encoding = 'cp1251'
            text = original.decode(encoding)
        data = prepare_exclusion_shells(text).encode(encoding)
        if data != original:
            payload[path.relative_to(GAME).as_posix()] = data
            shell_files += 1
    manifest = {}
    for relative, data in payload.items():
        target = GAME/relative
        original = target.read_bytes() if target.exists() else None
        if data == original:
            continue
        deployment.write(deployment.STAGE, relative, data)
        manifest[relative] = {'before':deployment.sha(original) if original is not None else None,
                              'after':deployment.sha(data)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(f'Staged {len(manifest)} files: global defaults, Pythonlancer policy, {shell_files} shell INIs')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    deployment.apply() if parser.parse_args().apply else prepare()
