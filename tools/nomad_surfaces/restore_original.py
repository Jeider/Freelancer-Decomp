"""Restore only the saved pre-simplification Nomad shader, retaining other materials."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
shader = ROOT / 'DATA_EXTRA/SHADERS/surface_material.hlsl'
baseline = ROOT / 'src/obj/nomad_lair_revision/baseline/surface_material.hlsl'
current, original = shader.read_bytes(), baseline.read_bytes()
newline = b'\r\n' if b'\r\n' in current else b'\n'
original = original.replace(b'\r\n', b'\n').replace(b'\n', newline)
start = b'#ifdef SURFACE_NOMAD' + newline + b'sampler2D NomadDetail'
end = b'#ifdef SURFACE_SHIP_NORMALS' + newline + b'sampler2D ShipNormalMap'
assert current.count(start) == original.count(start) == 1
assert current.count(end) == original.count(end) == 1
snapshot = ROOT / 'src/obj/nomad_original_restore/before.hlsl'
snapshot.parent.mkdir(parents=True, exist_ok=True)
if not snapshot.exists():
    snapshot.write_bytes(current)
replacement = original[original.index(start):original.index(end)]
assert b'k<12' in replacement
shader.write_bytes(current[:current.index(start)] + replacement + current[current.index(end):])
print('Restored original Nomad block; other shader blocks retained byte for byte.')
