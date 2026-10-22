"""Derive GPU medium-tier checks from the existing full material fixture."""
from pathlib import Path
s=Path('src/obj/surface_gpu_check.cpp').read_text()
s=s.replace('Check(D3DXCompileShaderFromFileA(path,nullptr,nullptr,"PSMain"',
'''D3DXMACRO low[]={{"SURFACE_LOW_DETAIL","1"},{nullptr,nullptr}};
    Check(D3DXCompileShaderFromFileA(path,low,nullptr,"PSMain"''')
s=s.replace('assert(((layered>>16)&255)>((oldLobes>>16)&255)+20);',
            'assert(layered==oldLobes);')
s=s.replace('assert(((offAxisBrushed>>16)&255)>((offAxisPlain>>16)&255)+2);',
            'assert(offAxisBrushed==offAxisPlain);')
s=s.replace('assert(glossy!=rough);',
            'assert(((glossy>>16)&255)>((rough>>16)&255));')
s=s.replace('assert(((reflected>>16)&255)>((emission>>16)&255)+3);',
            'assert(reflected==emission);')
s=s.replace('assert(((facing>>16)&255)>((reflected>>16)&255)+20);',
            'assert(facing==reflected); // no artificial reflection from a zero-energy light')
s=s.replace('PASS: layered frontal glint', 'PASS: low tier excludes layered frontal glint')
s=s.replace('PASS: real D3D9 draw', 'PASS: medium-tier real D3D9 draw')
Path('src/obj/surface_low_check.cpp').write_text(s)
