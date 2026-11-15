import struct as S
import valensia_mega as m
for rel in ['solar/misc/space_solar_plant.cmp','polygon2.cmp','solar/dockable/lair_door01.cmp']:
    path=m.GAME/'DATA'/rel
    root=m.utf.read_tree(path.read_bytes())[1][0]
    print('\nMODEL',rel)
    comp=m.b.one(root,'Cmpnd')
    for entry in comp.children:
        obj=m.b.one(entry,'Object name');file=m.b.one(entry,'File name')
        if obj:print('PART',m.b.text(obj.blob),m.b.text(file.blob))
    cons=m.b.one(comp,'Cons')
    for kind in cons.children:
        stride={'fix':176,'rev':208,'pris':208}[kind.name.lower()]
        for at in range(0,len(kind.blob),stride):
            rec=kind.blob[at:at+stride]
            print(kind.name,m.b.text(rec[:64]),m.b.text(rec[64:128]),S.unpack('<'+'f'*((len(rec)-128)//4),rec[128:]))
    anim=m.b.one(root,'Animation')
    def dump(n,depth=0):
        print(' '*depth+n.name,repr(n.blob[:200]) if n.blob else '')
        for x in n.children:dump(x,depth+1)
    if anim:dump(anim)
    if path.with_suffix('.sur').exists():
        print('SUR',[(hex(ident),[(label,len(blob),blob.hex() if label==b'!fxd' else '') for label,blob in chunks]) for ident,chunks in m.old.parts(path.with_suffix('.sur').read_bytes())])
