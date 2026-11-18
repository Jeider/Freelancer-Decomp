"""UV, displacement, repetition and source integrity checks of regional exports."""
import argparse,json
from depot_family_audit import paths,REGIONS
from depot_family_features import MATERIALS
from depot_relief_check import main as check_surface


def check(region):
    out,live,original,_=paths(region)
    surfaces=json.loads((out/'surfaces.json').read_text());door_groups=[]
    for rh_number,center in [('14',5.43),('04',2.57)]:
        number=MATERIALS[region][rh_number]
        groups=[g for g in surfaces['groups'] if g['part']=='room' and
                surfaces['materials'][g['material']]['number']==number]
        assert len(groups)==1,(region,number,groups)
        door_groups.append((groups[0]['key'],center))
    check_surface(out,original,live,door_groups)
    print('REGION_CHECK_PASS',region,flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('regions',nargs='+',choices=list(REGIONS));args=ap.parse_args()
    for region in args.regions:check(region)
