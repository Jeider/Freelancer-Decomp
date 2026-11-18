"""Render the unmodified LI pirate elite as a neutral shape reference."""
import numpy as np
from li_elite_concept_audit import a, active_ships, read_ship
from bw_family_audit import frame, sheet, write_json
from rh_redesign_paths import TOPIC


def main():
    values=active_ships()['li_elite_pir']
    source,path,rest,mats,stats,record,names,flight=read_ship('li_elite_pir',values)
    neutral={k:dict(v,image=None,colour=np.array([.18,.30,.38]) if 'glass' in v['name'].lower()
                   else np.array([.62,.65,.67])) for k,v in mats.items()}
    center,radius=frame(flight)
    cameras=[((-1,.42,-.32),'SIDE THREE-QUARTER / ORTHOGRAPHIC'),
             ((-1,0,0),'SIDE / ORTHOGRAPHIC'),((0,1,.000001),'TOP / ORTHOGRAPHIC'),
             ((0,0,-1),'FRONT / ORTHOGRAPHIC')]
    panels=[(label,a.source.render(flight,neutral,center,radius,cam,650,'texture'))
            for cam,label in cameras]
    output=TOPIC/'li_elite/references/native_neutral_shape.jpg'
    sheet(output,[panels[:2],panels[2:]],2,'LI PIR ELITE / ORIGINAL SHAPE / DEPLOYED',
          'Same unmodified source geometry. Neutral presentation only; opaque blue glazing. Same scale.',size=650)
    assert a.sha(path)==stats['sha256']
    write_json(output.with_suffix('.json'),dict(source_model=path.as_posix(),source_sha256=stats['sha256'],
        output=output.as_posix(),sha256=a.sha(output),pose='sc_extend wing t=0',
        cameras=cameras,geometry_unchanged=True,materials='Neutral display overrides only; no MAT writes.'))
    print(output)


if __name__=='__main__':
    main()
