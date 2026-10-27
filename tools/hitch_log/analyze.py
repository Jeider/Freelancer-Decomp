"""Show long frames and overlapping work from the newest automatic hitch log."""
import argparse
import csv
import heapq
import os
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('file',nargs='?',type=Path)
 args=p.parse_args()
 latest=args.file or max((Path(os.environ['LOCALAPPDATA'])/'Freelancer-Decomp/Diagnostics').glob('hitches_*.csv'),key=lambda p:p.stat().st_mtime_ns)
 files=sorted(latest.parent.glob(latest.stem.rsplit('_',1)[0]+'_*.csv'))
 def rows():
  for file in files:
   with file.open(newline='',encoding='utf8',errors='replace') as f:
    for row in csv.DictReader(f):
     try:
      for key in ('start_ms','end_ms','duration_ms'):row[key]=float(row[key])
      yield row
     except (ValueError,TypeError,KeyError):continue # possible incomplete last row during play
 frames=heapq.nlargest(20,(r for r in rows() if r['category']=='frame'),key=lambda r:r['duration_ms'])
 gaps=heapq.nlargest(5,(r for r in rows() if r['category']=='frame_interval'),key=lambda r:r['duration_ms'])
 overlaps=[[] for _ in frames]
 for r in rows():
  if r['category'] in ('frame','frame_interval','diagnostic'):continue
  if r['duration_ms']<2 and r['category']=='render':continue
  for i,frame in enumerate(frames):
   if r['end_ms']>frame['start_ms'] and r['start_ms']<frame['end_ms']:
    overlaps[i].append(r)
 print('Session:',latest.stem.rsplit('_',1)[0])
 print('Times are inclusive; overlapping scopes must not be added together. Worker overlap is not proof of a main-thread stall.')
 for frame,events in zip(frames,overlaps):
  print(f"\nFrame {frame['frame']} at {frame['start_ms']/1000:.2f}s: {frame['duration_ms']:.2f} ms")
  for r in sorted(events,key=lambda r:r['duration_ms'],reverse=True)[:8]:
   thread='main' if r['thread']==frame['thread'] else 'worker'
   print(f"  {r['duration_ms']:8.2f} ms {thread:6} {r['category']}: {r['resource']}")
  if not events:print('  No measured load/phase overlap; inspect render/driver/present or scheduling.')
 print('\nLargest frame intervals (also include limiter/message pump):')
 for r in gaps:print(f"  {r['start_ms']/1000:.2f}s: {r['duration_ms']:.2f} ms")

if __name__=='__main__':main()
