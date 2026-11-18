"""Inventory current Bismarck bar assets without writing to the game."""
import sys,json,struct,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
import generate_station_lods as utf
OUT=ROOT/'out/base_interiors/rh_biz_01_base/bar/prototype_v1';OUT.mkdir(parents=True,exist_ok=True)
GAME=Path('D:/Games/FL_MOD');SOURCE=GAME/'DATA/BASES/RHEINLAND/rh_bizmark_bar.cmp'
root=utf.read_tree(SOURCE.read_bytes())[1][0]
def walk(n,path=''):
 path+='/'+n.name
 if n.children:
  for c in n.children:yield from walk(c,path)
 else:yield path,len(n.blob)
rows=list(walk(root));(OUT/'tree.json').write_text(json.dumps(rows,indent=2))
print('\n'.join(str(x) for x in rows if any(t in x[0] for t in ('VMeshData','VMeshRef','Cons/','Material library'))))
(OUT/'source.json').write_text(json.dumps(dict(source=str(SOURCE),sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest()),indent=2))
