"""Install the reviewed Mesh0 body batch using DataFolder, with full rollback."""
import argparse,hashlib,json,runpy,sys
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/hatcher_hair'))
from build import DataFolder,GAME,read_tree,child,triangles
from policy import load_policy,excluded_name
OUT=ROOT/'out/character_rounding/all_bodies'
sha=lambda data:hashlib.sha256(data).hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
 reports=json.loads((OUT/'inventory.json').read_text());live=DataFolder(root=GAME);stage=DataFolder(root=OUT/'stage');pending=[]
 policy=load_policy();limit=policy['max_mesh0_triangles']
 oversized=[r['name'] for r in reports if not excluded_name(r['name'],policy) and r['triangles_after']>limit]
 if oversized:raise SystemExit('Install blocked by contour plan: '+str(len(oversized))+' bodies exceed '+str(limit)+' Mesh0 triangles. Rebuild local contours first; see tools/character_rounding/PLAN.txt.')
 assert len(reports)==93,'Incomplete reviewed inventory'
 for record in reports:
  name=record['name'];assert Path(name).name==name and '/' not in name and '\\' not in name
  if excluded_name(name,policy):continue
  r=json.loads((OUT/name/'report.json').read_text());assert r==record,'Gallery inventory out of date: '+name
  rel='CHARACTERS/BODIES/'+name+'.dfm';old=live.data_path(rel).read_bytes();desired=stage.data_path(rel).read_bytes()
  assert sha(desired)==r['output_sha256'],'Staged body changed: '+name
  mesh=child(child(read_tree(desired)[1][0],'MultiLevel'),'Mesh0')
  actual=sum(len(triangles(g)) for g in child(mesh,'Face_groups').children if g.children)
  assert actual==r['triangles_after'] and actual<=limit,'Exported triangle budget exceeded: '+name
  assert sha(old) in (r['source_sha256'],r['output_sha256']),'Live body independently modified: '+name
  preview=json.loads((OUT/name/'render_source.json').read_text());assert preview['sha256']==r['output_sha256'],'Preview out of date: '+name
  if old!=desired:
   assert r['changed'] and r['only_mesh0'] and r['other_lods_skeleton_materials_unchanged']
   pending.append((rel,old,desired))
 if not pending:print('All reviewed bodies already installed and hashes verified.');return
 # Full checks run before any game write, also on the dry run.
 runpy.run_path(str(ROOT/'tools/character_rounding/check_all_bodies.py'),run_name='__main__')
 runpy.run_path(str(ROOT/'tools/character_rounding/check_cuff_ends.py'),run_name='__main__')
 print('Validated install:',len(pending),'body DFM files; heads, other LODs, skeletons and materials unchanged.',flush=True)
 if not args.apply:return
 backup=OUT/'backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f');store=DataFolder(root=backup)
 manifest=[]
 for rel,old,desired in pending:
  store.sync_data_file(rel,old);assert store.data_path(rel).read_bytes()==old
  manifest.append(dict(relative_path=rel,before_sha256=sha(old),after_sha256=sha(desired)))
 (backup/'manifest.json').write_text(json.dumps(manifest,indent=2))
 touched=[]
 try:
  for rel,old,desired in pending:
   assert live.data_path(rel).read_bytes()==old,'File changed during preflight: '+rel
   touched.append((rel,old));live.sync_data_file(rel,desired)
   assert live.data_path(rel).read_bytes()==desired,'Write verification failed: '+rel
  for rel,old,desired in pending:assert sha(live.data_path(rel).read_bytes())==sha(desired)
 except BaseException:
  failures=[]
  for rel,old in reversed(touched):
   try:live.sync_data_file(rel,old);assert live.data_path(rel).read_bytes()==old
   except Exception as error:failures.append((rel,repr(error)))
  (backup/'rollback.json').write_text(json.dumps(dict(failures=failures),indent=2))
  if failures:print('Rollback failures:',failures,flush=True)
  raise
 result=dict(installed=len(pending),game=str(GAME),backup=str(backup),manifest=str(backup/'manifest.json'),hashes_verified=True,heads_modified=False,other_lods_modified=False,game_launched=False,files=manifest)
 (OUT/'installed.json').write_text(json.dumps(result,indent=2))
 print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))

if __name__=='__main__':main()
