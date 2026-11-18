"""Render finished body batches while the two independent builders progress."""
import subprocess,time,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'out/character_rounding/all_bodies'
def needed(p):
 if not (p/'report.json').exists():return False
 if not all((p/f).exists() for f in ('front.png','back.png','render_source.json')):return True
 return json.loads((p/'render_source.json').read_text())['sha256']!=json.loads((p/'report.json').read_text())['output_sha256']
while True:
 ready=[p for p in OUT.iterdir() if needed(p)]
 if ready:
  with (OUT/'render_all.log').open('ab') as log:
   subprocess.run(['C:/Program Files/Blender Foundation/Blender 5.2/blender.exe','--background','--python','tools/character_rounding/render_all_bodies.py'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
  # Blender can return 1 during shutdown after successful renders. Files are
  # validated independently; retry only missing outputs, never launch the game.
  pending=[p for p in ready if not ((p/'front.png').exists() and (p/'back.png').exists())]
  if pending:raise RuntimeError('Missing renders: '+','.join(p.name for p in pending))
 if (OUT/'inventory_0.json').exists() and (OUT/'inventory_1.json').exists():
  pending=[p for p in OUT.iterdir() if needed(p)]
  if not pending:break
 time.sleep(2)
print('All completed DFM bodies rendered front/back',flush=True)
