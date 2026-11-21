"""Bounded, read-only PDB-guided sampling. No injection or thread suspension."""
import collections
import json
import struct
import time


def capture(api, modules):
    C, W, d, handle = (api[k] for k in ('C', 'W', 'd', 'handle'))
    Symbol = api['Symbol']
    def load(key):
        address, path = modules[key]
        base = d.SymLoadModuleExW(handle, None, path, None, address, 0, None, 0)
        assert base, key
        api['base'] = base
        return base
    def symbol_buffer():
        raw = C.create_string_buffer(C.sizeof(Symbol)+2048)
        s = C.cast(raw, C.POINTER(Symbol))
        s.contents.SizeOfStruct = C.sizeof(Symbol)
        s.contents.MaxNameLen = 2048
        return raw, s
    load('dalib.dll')
    api['symbols'].clear()
    assert d.SymEnumSymbols(handle, api['base'], b'*Pipeline*', api['visit'], None)
    found = [s for s in api['symbols'] if s['name']=='DALib::Pipeline']
    assert len(found)==1, api['symbols']
    pipeline = api['u32'](found[0]['address'])
    load('rp9.dll')
    d.SymGetTypeFromName.argtypes = [W.HANDLE, C.c_ulonglong, C.c_char_p, C.POINTER(Symbol)]
    raw, sym = symbol_buffer()
    assert d.SymGetTypeFromName(handle, api['base'], b'FDirectX9', sym)
    pf = api['fields'](sym.contents.TypeIndex)
    et = api['info'](pf['Ex_']['type'], 4)
    ex = api['u32'](pipeline + pf['Ex_']['offset'])
    ef = api['fields'](et)
    wanted = ('bInPass','bShadowDrawing','bSurfaceActive','bSurfaceMaterialValid',
              'bSurfaceEnabled','bSurfaceCompileFailed','bSurfaceCubeCompileFailed',
              'bRoomFrame','bNativeNebulaObject','bNebulaFogShape','SurfaceSpawnCoverage',
              'SurfaceShader','RockClass','RockDetail','bRockEnabled','bShipNormalScope',
              'SurfaceDistanceTier','SurfacePsMirror','SurfacePsMirrorValid')
    missing = [k for k in wanted if k not in ef]
    assert not missing, missing
    start = min(ef[k]['offset'] for k in wanted)
    end = max(ef[k]['offset']+ef[k]['size'] for k in wanted)
    assert end-start<65536
    counts = collections.Counter()
    samples = {}
    until = time.monotonic()+8
    while time.monotonic()<until:
        data = api['read'](ex+start, end-start)
        row = {}
        for key in wanted:
            f=ef[key]; offset=f['offset']-start
            b=data[offset:offset+f['size']]
            if key=='SurfacePsMirror':
                values=struct.unpack('<'+'f'*(len(b)//4),b)
                row['fog_c5']=values[20:24]
                row['shape_c107']=values[428:432]
                row['coverage_c109']=values[436:440]
            elif key=='SurfacePsMirrorValid':
                row['constants_valid']=[b[i] for i in (5,107,109)]
            elif key=='SurfaceSpawnCoverage':row[key]=struct.unpack('<f',b)[0]
            else:row[key]=int.from_bytes(b,'little')
        # Focus on asteroid draws. Read-only observations can straddle a draw
        # boundary; treat aggregate states as evidence, not an atomic capture.
        if row['RockClass'] or row['SurfaceShader'] in (8,9):
            key=json.dumps({k:v for k,v in row.items() if k not in ('fog_c5','SurfaceSpawnCoverage')},sort_keys=True)
            counts[key]+=1; samples[key]=row
        time.sleep(.001)
    result={'pid':api['args'].pid,'pipeline':hex(pipeline),'rp9_state':hex(ex),
            'limitations':'Non-atomic read-only samples; no game pause or GPU interception',
            'routes':[dict(samples[k],count=n) for k,n in counts.most_common()]}
    out=api['ROOT']/'out/graphics_settings/nebula_asteroid_mesh/fog_coverage/physical_order/trace/routes.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2))
    print(json.dumps({'samples':sum(counts.values()),'distinct':len(counts),'output':str(out)}))
