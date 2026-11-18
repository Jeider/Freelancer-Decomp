"""Check terminal wrist vertices did not grow relative to the native mesh."""
from cuff_ends import *
results=[]
for folder in sorted(OUT.iterdir()):
 if not (folder/'report.json').exists():continue
 r=json.loads((folder/'report.json').read_text())
 if not r.get('cuff_end_revision'):continue
 before=json.loads((folder/'before.json').read_text());after=json.loads((folder/'after.json').read_text());p=np.array(after['points']);pi=np.array(after['point_indices']);bp=np.array(before['points']);bpi=np.array(before['point_indices']);ref=np.zeros_like(p)
 for bg,ag in zip(before['groups'],after['groups']):
  f=np.array(ag['faces']);native=bp[bpi[np.array(bg['faces'])]];positions=np.einsum('sij,tjk->tsik',subdivisions(2),native).reshape(-1,3,3);ref[pi[f].ravel()]=positions.reshape(-1,3)
 maximum=-1.;vertices=0
 for center,axis,u,w,ang,radius,ring in rims(before):
  v=ref-center;t=v@axis;mask=(ref[:,0]*np.sign(center[0])>.20)&(t>-.02)&(t<.025)
  original=v[mask]-np.outer(t[mask],axis);actual=p[mask]-center;actual-=np.outer(actual@axis,axis)
  if not mask.any():continue
  growth=np.linalg.norm(actual,axis=1)-np.linalg.norm(original,axis=1);assert growth.max()<2e-6,(folder.name,growth.max());maximum=max(maximum,float(growth.max()));vertices+=int(mask.sum())
 results.append(dict(name=folder.name,terminal_vertices=vertices,max_radial_growth_m=maximum))
(OUT/'cuff_end_validation.json').write_text(json.dumps(results,indent=2));print('Cuff ends checked:',len(results),'max radial growth:',max(r['max_radial_growth_m'] for r in results))
