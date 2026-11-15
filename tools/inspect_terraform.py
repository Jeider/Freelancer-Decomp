import valensia_mega as m
builder=m.Builder()
print('FX',[x for x in builder.loadouts['terraform_new_root']['equip'] if x.startswith('gf_')])
for rel in ['solar/misc/wire/terraforming.cmp','polygon2.cmp','solar/planets/STATION_CENTER/sw_center_250.sph']:
    root=m.utf.read_tree((m.GAME/'DATA'/rel).read_bytes())[1][0]
    print(rel,[(n.name,len(n.blob or b''),len(n.children)) for n in root.children])
    print('HP',len(m.b.hardpoints(root)),list(m.b.hardpoints(root))[:5])
    cons=m.b.one(root,'Cons')
    print('CONS',[(n.name,len(n.blob or b'')) for n in cons.children] if cons else None)
    anim=m.b.one(root,'Animation')
    print('ANIMATION',[(n.name,len(n.children)) for n in anim.children] if anim else None)
    if cons:
        for n in cons.children:
            stride={'fix':176,'rev':208,'pris':208}.get(n.name.lower(),len(n.blob))
            print(n.name,[(m.b.text(n.blob[i:i+64]),m.b.text(n.blob[i+64:i+128])) for i in range(0,len(n.blob),stride)])
