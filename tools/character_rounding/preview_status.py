"""Inspect completed previews, including legacy renderer completion metadata."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]/'out/character_rounding/all_bodies'
reports=front=back=0
for p in ROOT.iterdir():
 if not (p/'report.json').exists():continue
 reports+=1
 front+=(p/'front.png').exists();back+=(p/'back.png').exists()
 # The first renderer predates the hash sidecar. Only tag finished pairs
 # rendered after the final report, while the staged output was immutable.
 if not (p/'render_source.json').exists() and all((p/f).exists() and (p/f).stat().st_mtime>=(p/'report.json').stat().st_mtime for f in ('front.png','back.png')):
  r=json.loads((p/'report.json').read_text())
  (p/'render_source.json').write_text(json.dumps(dict(sha256=r['output_sha256'],front='front.png',back='back.png')))
print(dict(reports=reports,front=front,back=back))
