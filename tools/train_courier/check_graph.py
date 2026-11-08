"""Check hop semantics, actual graph paths and station/shipyard depots."""
import json
from pathlib import Path
from types import SimpleNamespace
from trade_graph import paths_from


class Node:
    def __init__(self,name,system):self.name=name;self.system=system;self.connections=[]
    def get_full_alias(self):return self.name


class Gate(Node):
    def get_target_jumpgate(self):
        if not hasattr(self,'target'):raise KeyError(self.name)
        return self.target


class Lane:
    def __init__(self,a,b):self.ends=(a,b);a.connections.append(self);b.connections.append(self)
    def get_destination_objects(self):return self.ends


def main():
    a=SimpleNamespace(NAME='a',SCAN_JUMP=True);b=SimpleNamespace(NAME='b',SCAN_JUMP=True)
    start=Node('start',a);mid=Node('mid',a);g1=Gate('gate',a);g2=Gate('gate',b);end=Node('end',b)
    Lane(start,mid);Lane(mid,g1);g1.target=g2;g2.target=g1;Lane(g2,end)
    excluded=set();paths=paths_from(start,Gate,excluded)
    assert len(paths[mid])==1 and len(paths[g1])==2 and len(paths[end])==4
    assert [s['kind'] for s in paths[end]]==['tradelane','tradelane','jumpgate','tradelane']
    Lane(start,g1);assert len(paths_from(start,Gate,excluded)[end])==3
    # A shorter route through gates must not inflate geographic separation:
    # there is also a longer lane-only path to a destination in this system.
    back=Gate('back',b);home=Gate('home',a);local=Node('local',a)
    Lane(g2,back);back.target=home;home.target=back;Lane(home,local)
    cursor=start
    for i in range(8):
        n=Node('detour'+str(i),a);Lane(cursor,n);cursor=n
    Lane(cursor,local)
    assert sum(s['kind']=='jumpgate' for s in paths_from(start,Gate,excluded)[local])==2
    assert sum(s['kind']=='jumpgate' for s in paths_from(start,Gate,excluded,minimize_jumps=True)[local])==0
    missing=Gate('missing',a);Lane(start,missing);paths_from(start,Gate,excluded);assert excluded
    isolated=Node('isolated',a);assert paths_from(isolated,Gate,set())=={isolated:[]}
    patrol=Node('patrol',a);patrol.connections.append(start.connections[0])
    assert paths_from(patrol,Gate,set())=={patrol:[]} # patrol origin is not a lane endpoint
    root=Path(__file__).resolve().parents[2]
    catalog=json.loads((root/'out/train_courier/catalog.json').read_text(encoding='utf-8'))
    kinds={b['base_type'] for b in catalog['bases'].values()};assert {'Station','Shipyard','Refinery'}<=kinds
    for route in catalog['routes']:
        assert route['distance']==len(route['path'])>0
        assert 0<=route['minimum_jumps']<=route['jumps']
        for step in route['path']:
            same=step['from'].split(':')[0]==step['to'].split(':')[0]
            assert same==(step['kind']=='tradelane')
        assert all(x['to']==y['from'] for x,y in zip(route['path'],route['path'][1:]))
    departures=[r for r in catalog['routes'] if r['source']=='rh_biz_01_base']
    for wagons in (2,3,10,20):assert any(r['distance']>=wagons-1 and r['minimum_jumps']>=wagons//5 for r in departures)
    print(f'PASS: lane=1, jumpgate=1, shortest path, cycles, missing gates, no patrol shortcuts; {len(catalog["routes"])} actual paths; starts 2/3/10/20 have routes')


if __name__=='__main__':main()
