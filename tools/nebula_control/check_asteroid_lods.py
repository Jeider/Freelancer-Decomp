"""Test embedded native-UV LODs and the minimal shader on a standalone D3D9 device."""
import json,re,struct,subprocess
from pathlib import Path
import check_asteroid_mesh as mesh
ROOT=mesh.ROOT;OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/lod';PROBE=OUT/'probe'
SOURCES=['src/freelancer/Client/far_rocks.cpp','src/freelancer/Client/asteroid_lod_data.h',
 'src/freelancer/Client/asteroid_lod_policy.h','src/freelancer/Client/asteroid_lod_batches.inl',
 'src/freelancer/Client/procedural_asteroid_mesh.inl','src/RP9/RP9ShaderManifest.h','src/RP9/RP9MeshInstances.h',
 'DATA_EXTRA/SHADERS/asteroid_simple.hlsl','DATA_EXTRA/SHADERS/far_rocks.hlsl',
 'tools/nebula_control/build_asteroid_lods.py','tools/nebula_control/check_asteroid_lods.cpp',
 'tools/nebula_control/check_asteroid_lods.py']
def main():
 PROBE.mkdir(parents=True,exist_ok=True);compiler,env=mesh.compiler_env()
 env['INCLUDE']=';'.join(p for p in env['INCLUDE'].split(';') if 'DXSDK' not in p.upper())+';C:/DXSDK_Jun10/Include'
 env['PATH']=str(ROOT/'bin')+';D:/Games/FL_MOD/bin;'+env['PATH'];env['TEMP']=env['TMP']=str(PROBE)
 sources={p:mesh.digest(ROOT/p) for p in SOURCES};assets={};arguments=[]
 mat=mesh.DATA/'SOLAR/ASTEROIDS_MOD/om15/ast_om15.mat';assets[str(mat)]=mesh.digest(mat);library=mesh.leaves(mat.read_bytes())[1]
 texture_names={mesh.crc(n.split('/')[-2]):b.rstrip(b'\0').decode('ascii') for n,_,b in library if n.lower().endswith('/dt_name')}
 for letter in 'abc':
  path=mesh.DATA/f'SOLAR/ASTEROIDS_MOD/om15/ast_o15_nrml_{letter}.3db';assets[str(path)]=mesh.digest(path)
  nodes=mesh.leaves(path.read_bytes())[1];blob=next(b for n,_,b in nodes if n.lower().endswith('/vmeshdata'))
  _,descriptors,groups=mesh.triangles(blob);assert len(groups)==1;texture_name=texture_names[descriptors[0][0]]
  texture=next(b for n,_,b in library+nodes if n.lower().endswith('/'+texture_name.lower()+'/mips') or n.lower().endswith('/'+texture_name.lower()+'/mip0'))
  binary=PROBE/(letter+'.bin');binary.write_bytes(struct.pack('<I',len(groups[0]))+b''.join(groups[0]));tex=PROBE/(letter+'.texture');tex.write_bytes(texture)
  arguments += [str(binary),str(tex),'0']
 exe=PROBE/'check.exe'
 cmd=[str(compiler/'cl.exe'),'/nologo','/EHsc','/MD','/O2','/std:c++17','/utf-8','/DNOMINMAX','/D_CRT_SECURE_NO_WARNINGS',
  '/Isrc/RP9','tools/nebula_control/check_asteroid_lods.cpp','/Fo'+str(PROBE/'check.obj'),'/Fe'+str(exe),
  '/link','d3d9.lib','user32.lib','C:/DXSDK_Jun10/Lib/x86/d3dx9.lib']
 for name,args in [('build_probe',cmd),('result',[str(exe),str(ROOT/'DATA_EXTRA/SHADERS')+'/',str(PROBE/'cache'),*arguments,str(OUT/'preview.png')])]:
  with (OUT/(name+'.log')).open('wb') as stream:r=subprocess.run(args,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
  print((OUT/(name+'.log')).read_text(errors='replace')[-5000:]);r.check_returncode()
 assert sources=={p:mesh.digest(ROOT/p) for p in SOURCES}
 (OUT/'checks.json').write_text(json.dumps({'passed':True,'game_launched':False,'sources':sources,'assets':assets,
  'binaries':{name:mesh.digest(OUT/'build/bin'/name) for name in ('RP9.dll','RP9.pdb','freelancer.exe','freelancer.pdb')},
  'geometry':json.loads((OUT/'geometry.json').read_text()),
  'cache_files':{p.name:mesh.digest(p) for p in (PROBE/'cache').iterdir() if re.fullmatch(r'[a-f0-9]{64}\.bin',p.name)}},indent=2))
if __name__=='__main__':main()
