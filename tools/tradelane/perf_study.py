"""Measure isolated tunnel variants; never install or edit production shaders."""
from pathlib import Path
import hashlib
import json
import os
import re
import statistics
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'out/tunnel_perf'
OUT.mkdir(parents=True, exist_ok=True)
sources = [ROOT/'DATA_EXTRA/SHADERS/tradelane_corridor.hlsl', ROOT/'DATA_EXTRA/SHADERS/jump_cloud.hlsl']
protected = sources + [Path('D:/Games/FL_MOD')/p for p in ('bin/freelancer.exe', 'DATA_EXTRA/SHADERS/tradelane_corridor.hlsl', 'DATA_EXTRA/SHADERS/jump_cloud.hlsl')]
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = {str(p):digest(p) for p in protected}
lane, jump = [p.read_text() for p in sources]

def replace(source, old, new):
    assert old in source, old
    return source.replace(old, new)

def layers(count):
    return replace(lane, 'return ShadeCorridor(In,Pixel,16);', f'return ShadeCorridor(In,Pixel,{count});')

old = (ROOT/'out/tradelane_mix/corridor_before_install.hlsl').read_text()
old = old[:old.index('float4 PSWarp(')]+lane[lane.index('float4 PSWarp('):]
variants = [
    ('lane_current', 'lane', lane, 1920, 1080),
    ('lane_half_resolution', 'lane', lane, 960, 540),
    ('lane_8_layers', 'lane', layers(8), 1920, 1080),
    ('lane_4_layers', 'lane', layers(4), 1920, 1080),
    ('lane_far_3000', 'lane', replace(lane, 'smoothstep(5000.0, 9400.0, abs(P.z))', 'smoothstep(1600.0, 3000.0, abs(P.z))'), 1920, 1080),
    ('lane_no_rings', 'lane', replace(lane, 'Accumulated+=TradeLaneRings(Ray,SceneRay);', '// Rings excluded from this cost probe.'), 1920, 1080),
    ('lane_previous_volume', 'lane', old, 1920, 1080),
    ('jump_current', 'jump', jump, 960, 540),
    ('jump_360p', 'jump', jump, 640, 360),
    ('jump_270p', 'jump', jump, 480, 270),
    ('jump_far_120', 'jump', replace(replace(jump, 'endDistance=240/ray.z', 'endDistance=120/ray.z'), 'smoothstep(80,225,depth)', 'smoothstep(40,112,depth)'), 960, 540),
    ('jump_simple_light', 'jump', replace(jump, 'float towardLight=Field(p+light*.65);', 'float towardLight=gap+.3;'), 960, 540),
]
coarse = replace(jump, 'step<256', 'step<128')
coarse = replace(coarse, 'distance+=clamp((gap-.3)*.26,.06,1.2)*max(1,distance/32);', 'distance+=2*clamp((gap-.3)*.26,.06,1.2)*max(1,distance/32);')
coarse = replace(coarse, 'float opacity=1-exp2(-density*stride);', 'stride*=2;\n        float opacity=1-exp2(-density*stride);')
variants.append(('jump_double_stride', 'jump', coarse, 960, 540))

vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10'); version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(map(str, [vc/'include'] + [sdk/'Include'/version/x for x in ('ucrt','shared','um')] + [Path('C:/DXSDK_Jun10/Include')]))
env['LIB'] = ';'.join(map(str, [vc/'lib/x86'] + [sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')] + [Path('C:/DXSDK_Jun10/Lib/x86')]))
exe = OUT/'perf_study.exe'
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/O2', '/EHsc', '/MT', '/D_CRT_SECURE_NO_WARNINGS', str(ROOT/'tools/tradelane/perf_study.cpp'), '/Fe'+str(exe), '/link', 'd3d9.lib', 'd3dx9.lib', 'user32.lib'], cwd=OUT, env=env, check=True)
results=[]
for name, kind, source, width, height in variants:
    folder=OUT/name;folder.mkdir(exist_ok=True)
    path=folder/'shader.hlsl';path.write_text(source)
    print('Measuring', name, flush=True)
    with (folder/'run.log').open('w') as log:
        subprocess.run([str(exe), kind, str(path), str(width), str(height), str(folder)+os.sep], cwd=ROOT, stdout=log, stderr=log, check=True)
    log=(folder/'run.log').read_text()
    times=[float(x) for x in re.findall(r'RESULT \w+ [\d.]+ \d+x\d+ ([\d.]+) ms', log)]
    assert len(times)==5, log
    row=dict(name=name,kind=kind,resolution=[width,height],gpu=re.search(r'GPU: (.+)',log)[1],times_ms=times,median_ms=statistics.median(times),max_ms=max(times))
    results.append(row)
    (OUT/'results.json').write_text(json.dumps(results, indent=2))
    print(f'{name}: median {row["median_ms"]:.3f} ms, max {row["max_ms"]:.3f} ms', flush=True)
assert before == {str(p):digest(p) for p in protected}, 'Production/game files changed'
(OUT/'manifest.json').write_text(json.dumps(dict(protected_hashes=before,scope='Isolated D3D9 GPU timestamps; five poses. Lane excludes scene-copy/warp. Jump includes native 1080p composite. No world, ship, HUD, game CPU or total FPS. Lane half resolution excludes upsampling and depth reconstruction. Not a GTX1060 measurement.'), indent=2))
print(OUT/'results.json')
