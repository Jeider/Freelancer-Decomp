"""Pinned user-supplied RenoDX runtime; NVIDIA libraries remain separately pinned."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[2]
VERSION = '10.8.0'
SHA256 = '79871879324053d49931a9f8c1865fcb83e8146df4a56b146d7a8a14cc7e70fe'
CACHED = ROOT / 'out/base_neural/reference/renodx-10.8.0/renodx-dlss5.addon64'

def verify(path):
    if hashlib.sha256(path.read_bytes()).hexdigest() != SHA256:
        raise RuntimeError('Expected the verified RenoDX v10.8.0 binary: ' + str(path))
    return path
