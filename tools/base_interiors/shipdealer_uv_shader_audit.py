"""Compile installed vertex shader and inspect a UV-selection candidate offline."""
import ctypes as c
import json
from pathlib import Path
import numpy as np
from native_common import GAME,sha,read_tree,get_parts,dump
from shipdealer_uv_audit import OUT,LIVE,ORIGINAL


def buffer_call(obj,index,restype):
    addr=c.cast(obj,c.POINTER(c.POINTER(c.c_void_p))).contents[index]
    return c.WINFUNCTYPE(restype,c.c_void_p)(addr)(obj)


def buffer_data(obj):
    return c.string_at(buffer_call(obj,3,c.c_void_p),buffer_call(obj,4,c.c_uint))


def compile_assembly(source):
    dll=c.WinDLL('d3dx9_43.dll')
    compile=dll.D3DXCompileShader
    compile.argtypes=[c.c_char_p,c.c_uint,c.c_void_p,c.c_void_p,c.c_char_p,c.c_char_p,c.c_uint,c.POINTER(c.c_void_p),c.POINTER(c.c_void_p),c.c_void_p]
    compile.restype=c.c_long
    shader=c.c_void_p();errors=c.c_void_p();assembly=c.c_void_p()
    try:
        result=compile(source,len(source),None,None,b'VSMain',b'vs_3_0',0,c.byref(shader),c.byref(errors),None)
        assert result>=0,buffer_data(errors).decode(errors='replace') if errors else hex(result&0xffffffff)
        disassemble=dll.D3DXDisassembleShader
        disassemble.argtypes=[c.c_void_p,c.c_int,c.c_char_p,c.POINTER(c.c_void_p)];disassemble.restype=c.c_long
        assert disassemble(buffer_call(shader,3,c.c_void_p),0,None,c.byref(assembly))>=0
        return buffer_data(assembly).decode().rstrip('\0')
    finally:
        for obj in (assembly,errors,shader):
            if obj:buffer_call(obj,2,c.c_uint)


def main():
    path=GAME/'DATA_EXTRA/SHADERS/room_material.hlsl';source=path.read_bytes()
    live_asm=compile_assembly(source)
    candidate=source
    for name,axis in [('U0','x'),('U1','y')]:
        old=f'float2 {name}=VertexMode.{axis}>1.5 ? I.U2 : VertexMode.{axis}>.5 ? I.U1 : I.U0;'.encode()
        new=f'float2 {name}=I.U0; [branch] if(VertexMode.{axis}>1.5){{{name}=I.U2;}}else [branch] if(VertexMode.{axis}>.5){{{name}=I.U1;}}'.encode()
        assert old in candidate
        candidate=candidate.replace(old,new)
    proposed_asm=compile_assembly(candidate)
    (OUT/'installed_vertex_shader.asm').write_text(live_asm,encoding='utf8')
    (OUT/'uv_branch_candidate.asm').write_text(proposed_asm,encoding='utf8')
    assert 'mad r0, r2.yyww, r0, v4.xyxy' in live_asm
    assert proposed_asm.count('if_lt')==4
    raw=LIVE.read_bytes();original=ORIGINAL.read_bytes()
    group=get_parts(read_tree(raw)[1][0])[0]['groups'][18]['corners']
    baseline=get_parts(read_tree(original)[1][0])[0]['groups'][18]['corners']
    bad=~np.isfinite(group).all(axis=(1,2));triangles=np.where(bad)[0].tolist()
    assert np.array_equal(group,baseline,equal_nan=True)
    uv0=group[8,2,6:8];uv1=group[8,2,8:10]
    selected=uv0+np.float32(0)*(uv1-uv0)
    assert np.isfinite(uv0).all() and not np.isfinite(selected).all()
    dump(OUT/'shader_diagnosis.json',dict(model_sha256=sha(raw),shader_path=str(path),shader_sha256=sha(source),
        material='rb_floor-root-3.tga021120175041',root_material_group=18,affected_triangles=triangles,
        primary_uv_valid=True,secondary_uv_has_nan=True,same_invalid_value_in_fl_nd=True,
        compiler='D3DX9 43, VSMain vs_3_0, flags 0 (runtime compile policy)',
        diagnosis='Compiled arithmetic UV selection evaluates UV0 + 0 * (UV1 - UV0) even when UV0 is selected. An unused NaN in UV1 contaminates the selected UV0.',
        candidate='Explicit branch selects only the requested UV channel. Candidate compiled to if_lt instructions; not installed.',
        validation_scope='Native asset comparison, real shader compilation/disassembly and IEEE arithmetic reproduction. No game launch or runtime GPU capture.',
        game_files_changed=False))
    assert path.read_bytes()==source and LIVE.read_bytes()==raw
    print('CONFIRMED: original unused UV1 NaN reaches selected UV0 in installed vertex bytecode; affected native triangles',triangles)
    print('Offline branch candidate compiles; game files unchanged.')


if __name__=='__main__':main()
