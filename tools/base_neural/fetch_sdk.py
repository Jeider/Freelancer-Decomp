"""Fetch pinned NVIDIA NGX SDK build inputs, with Git blob verification."""
from pathlib import Path
import hashlib
import json
import urllib.request
ROOT=Path(__file__).resolve().parents[2]
REV='9981c6350dc58c0ce21f024fd65e31e851c31689'

def main():
    manifest=json.loads(Path(__file__).with_name('ngx_files.json').read_text())
    for name,expected in manifest.items():
        path=ROOT/'out/base_neural/reference/ngx'/name
        path.parent.mkdir(parents=True,exist_ok=True)
        if not path.is_file():
            urllib.request.urlretrieve(f'https://raw.githubusercontent.com/NVIDIA/DLSS/{REV}/{name}',path)
        data=path.read_bytes()
        actual=hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
        if actual!=expected:raise SystemExit(f'Pinned SDK blob mismatch: {name}')
    print('PASS pinned NGX SDK headers/library verified')

if __name__=='__main__':main()
