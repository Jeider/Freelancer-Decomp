"""Stage/install authored field distances, ASF mine fog and the Sphere2 exterior volume."""
import argparse
import json
from pathlib import Path
import re

import asf_hq as deployment
from sphere_exterior import edit_section

ROOT, GAME = deployment.ROOT, deployment.GAME
OUT = ROOT/'src/obj/field_fog'
VOLUME = deployment.VOLUME
MINES = ('DATA/SOLAR/ASTEROIDS_MOD/asf_hq/m13_asf_prom_field.ini',
         'DATA/SOLAR/ASTEROIDS_MOD/asf_hq/m8_asf_entry_field.ini')
SYSTEM = 'DATA/UNIVERSE/SPECIAL/SPHERE2/sphere2.ini'
TEMPLATE = 'DATA/UNIVERSE/SPECIAL/SPHERE2/sph2_dev.ini'
NEBULA = 'DATA/SOLAR/NEBULA_MOD/sphere2_nebula.ini'
FIELD = 'DATA/SOLAR/ASTEROIDS_MOD/dyson/sphere2_field.ini'
PAYLOAD = ('bin/freelancer.exe', 'bin/freelancer.pdb', *MINES, SYSTEM, TEMPLATE, NEBULA, FIELD, VOLUME)


def profile(text, name):
    found = [m[0] for m in re.finditer(r'(?ims)^\[NebulaOverride\][^\n]*\n.*?(?=^\[|\Z)', text)
             if re.search(rf'(?im)^file\s*=\s*{re.escape(name)}\s*$', m[0])]
    assert len(found) == 1, name
    return found[0].strip()+'\n'


def prepare():
    build = json.loads((OUT/'build.json').read_text())
    sha = deployment.sha
    assert sha((GAME/'bin/freelancer.exe').read_bytes()) == build['baseline_client']
    assert sha((OUT/'freelancer.exe').read_bytes()) == build['client']
    assert sha((ROOT/'src/freelancer/Client/cli_asteroid.cpp').read_bytes()) == build['source']
    # All three active ASF variants share static field assets with their Pythonlancer templates.
    for folder, system, template, field, nebula in (
        ('ASF_HQ','asf_hq','asf_hq_dev','m13_asf_right_field','m13_asf_hq_nebula'),
        ('ASF_PROMETHEUS','asf_prom','asf_prom_dev','m13_asf_prom_field','m13_asf_prom_nebula'),
        ('MSN8_ASF_HQ','m8_asf_hq','m8_asf_hq_dev','m8_asf_entry_field','m8_asf_hq_nebula')):
        for name in (system, template):
            text = (GAME/f'DATA/UNIVERSE/SPECIAL/{folder}/{name}.ini').read_text(encoding='utf-8-sig')
            assert f'file = solar\\asteroids_mod\\asf_hq\\{field}.ini' in text
            assert f'file = solar\\nebula_mod\\{nebula}.ini' in text
    source_volume = (ROOT/VOLUME).read_text(encoding='utf-8-sig')
    manifest = {}
    for relative in PAYLOAD:
        original = (GAME/relative).read_bytes()
        if relative.startswith('bin/'):
            data = (OUT/Path(relative).name).read_bytes()
        else:
            text = original.decode('utf-8-sig').replace('\r\n', '\n')
            before_fill = re.findall(r'(?im)^fill_dist\s*=.*$', text)
            if relative in MINES:
                text = edit_section(text, 'Field', None, {'contains_fog_zone':'1', 'rock_normals':'false'})
                assert text.count('asteroid = mine_radiate,') == 6
            elif relative == FIELD:
                text = edit_section(text, 'Field', None, {'contains_fog_zone':'1'})
                assert re.search(r'(?im)^fill_dist\s*=\s*15000\s*$', text)
            elif relative in (SYSTEM, TEMPLATE):
                text = edit_section(text, 'Nebula', r'^file\s*=\s*solar\\nebula_mod\\sphere2_nebula.ini\s*$', {'volumetric':'true'})
                zone = re.search(r'(?ims)^\[zone\]\s*\nnickname\s*=\s*Zone_sphere2_main_sphere\s*\n(.*?)(?=^\[|\Z)', text)[1]
                assert re.search(r'(?im)^size\s*=\s*28000\s*$', zone)
                assert re.search(r'(?im)^shape\s*=\s*SPHERE\s*$', zone)
            elif relative == NEBULA:
                text = edit_section(text, 'Fog', None, {'fog_enabled':'1'})
                text = edit_section(text, 'Exclusion Zones', None, {'exclusion':'Zone_sphere2_main_sphere'})
                assert not re.search(r'(?im)^zone_shell\s*=', text)
                assert re.search(r'(?im)^fog_far\s*=\s*10000(?:\.0+)?\s*$', text)
            else:
                # Replace only the legacy reach block and append the three scoped profiles.
                pattern = r'(?ms)^; ---- asteroid fields inside a drawn nebula ----\n.*?(?=^; ---- lightning inside the clouds ----)'
                block = re.search(pattern, source_volume)[0]
                text, count = re.subn(pattern, lambda m:block, text)
                assert count == 1
                for name in ('m13_asf_prom_nebula', 'm8_asf_hq_nebula', 'sphere2_nebula'):
                    assert not re.search(rf'(?im)^file\s*=\s*{name}\s*$', text), name+' already present'
                    text = text.rstrip()+'\n\n'+profile(source_volume, name)
                assert profile(text, 'sphere_nebula') == profile(source_volume, 'sphere_nebula')
                assert profile(text, 'm13_asf_hq_nebula') == profile(source_volume, 'm13_asf_hq_nebula')
            assert re.findall(r'(?im)^fill_dist\s*=.*$', text) == before_fill, relative+' fill_dist changed'
            newline = '\r\n' if b'\r\n' in original else '\n'
            data = text.replace('\n', newline).encode('utf-8')
            if original.startswith(b'\xef\xbb\xbf'):
                data = b'\xef\xbb\xbf'+data
        target = OUT/'staged'/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        manifest[relative] = {'before':sha(original), 'after':sha(data)}
    (OUT/'manifest.json').write_text(json.dumps(manifest, indent=2))
    print('PASS: staged nine files; all fill_dist values preserved, ASF source references verified, meshless Sphere2 exclusion = 28km')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    if parser.parse_args().apply:
        deployment.OUT, deployment.PAYLOAD = OUT, PAYLOAD
        deployment.apply()
    else:
        prepare()
