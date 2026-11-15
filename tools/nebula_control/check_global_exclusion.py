"""Verify global defaults and Pythonlancer output without touching the live DATA."""
import ast
import json
from pathlib import Path
import re
import sys
import tempfile
import types

from pythonlancer_exclusion import prepare_exclusion_shells

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'out/global_exclusion'
values = {'RenderInExclusion': ('render_in_exclusion', 1),
          'ExclusionMarchDistance': ('exclusion_march_distance', 6000),
          'ExclusionTransitionFraction': ('exclusion_transition_fraction', .2),
          'ExclusionDensityScale': ('exclusion_density_scale', .15),
          'ExclusionCoreHaze': ('exclusion_core_haze', .04)}
source = (ROOT/'src/freelancer/Client/nebula_volume.cpp').read_text(encoding='utf-8-sig')
for path in (ROOT/'DATA_EXTRA/VOLUMETRIC/volumetric.ini', OUT/'staged/DATA_EXTRA/VOLUMETRIC/volumetric.ini'):
    text = path.read_text(encoding='utf-8-sig')
    section = re.search(r'(?ims)^\[Nebula\]\s*\n(.*?)(?=^\[|\Z)', text)[1]
    for member, (key, expected) in values.items():
        assert float(re.search(rf'S\.{member} = ([0-9.]+)f;', source)[1]) == expected
        assert float(re.search(rf'(?m)^{key}\s*=\s*([0-9.]+)', section)[1]) == expected

fixture = '[Exclusion Zones]\nexclusion = test\nzone_shell = shell.3db\nmax_alpha = 1 ; keep comment\nexclusion_tint = 100, 80, 10\n'
result = prepare_exclusion_shells(fixture)
assert result == fixture.replace('1 ; keep', '0.8 ; keep')
assert prepare_exclusion_shells(result) == result
for alpha in ('0', '0.3', '0.5', '0.8'):
    text = fixture.replace('1 ; keep', alpha+' ; keep')
    assert prepare_exclusion_shells(text) == text
meshless = '[Exclusion Zones]\nexclusion = field\nfog_far = 10000\n'
assert prepare_exclusion_shells(meshless) == meshless
assert prepare_exclusion_shells(fixture.replace('[Exclusion Zones]', '[;Exclusion Zones]')) == fixture.replace('[Exclusion Zones]', '[;Exclusion Zones]')
assert 'max_alpha = 0.8' in prepare_exclusion_shells(fixture.replace('max_alpha = 1 ; keep comment\n', ''))
assert prepare_exclusion_shells(fixture.replace('\n', '\r\n')) == result.replace('\n', '\r\n')

# Run the staged production DataFolder entry point, not a test reimplementation.
folder_source = (OUT/'staged/Assets/Pythonlancer/tools/data_folder.py').read_text()
ast.parse(folder_source)
namespace = {}
exec(compile(folder_source, 'staged_data_folder.py', 'exec'), namespace)
policy = types.ModuleType('tools.nebula_exclusion')
policy.prepare_exclusion_shells = prepare_exclusion_shells
sys.modules['tools.nebula_exclusion'] = policy
with tempfile.TemporaryDirectory() as temporary:
    folder = namespace['DataFolder'](root=temporary)
    folder.sync_templated_nebula('probe', 'GENERATED', fixture)
    target = Path(temporary)/'DATA/SOLAR/NEBULA_MOD/GENERATED/probe.ini'
    assert target.read_text() == result
    # Raw sync remains lossless for installation backups and rollback.
    folder.sync_data_file('SOLAR/NEBULA_MOD/GENERATED/probe.ini', fixture.encode())
    assert target.read_bytes() == fixture.encode()
manifest = json.loads((OUT/'manifest.json').read_text())
assert 'DATA/SOLAR/NEBULA_MOD/m11_vienna_nebula.ini' not in manifest
print('PASS global config/native defaults, inherited policy, shell alpha bounds/comments/CRLF, meshless zones, Pythonlancer generation and lossless rollback')
