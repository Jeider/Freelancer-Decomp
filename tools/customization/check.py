"""Exercise built Common and the actual Server costume serialization against live catalogues, read-only."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env

SOURCES=[ROOT/p for p in (
    'src/include/player_customization.h','src/Common/graphics_settings.cpp',
    'src/Server/server_pub.cpp','src/Server/server_savegame.cpp',
    'src/freelancer/Client/nn_ship_park.cpp','src/freelancer/Client/nn_inventory.cpp',
    'src/freelancer/Client/nn_inventory.h','src/freelancer/Client/native_subtitles.cpp','src/freelancer/Client/native_subtitles.h',
    'src/freelancer/Client/page_customization.cpp','src/freelancer/Client/page_customization.h',
    'src/freelancer/Client/nn_preferences.cpp','src/freelancer/Client/nn_preferences_misc.cpp',
    'src/freelancer/Client/preferences_customization.cpp','src/freelancer/Client/nn_preferences_graphics.cpp',
    'src/freelancer/Client/nn_preferences.h','src/freelancer/Client/ui_win_deform.cpp',
    'src/freelancer/Client/ui_win_deform.h','src/freelancer/Client/engine_character.cpp',
    'src/freelancer/Client/gf_character_object.cpp','src/freelancer/Client/gf_script_spawn.cpp',
    'src/freelancer/Client/base_walk.cpp','src/freelancer/Client/perf_options.cpp',
    'src/freelancer/freelancer.vcxproj')]
BUILD=ROOT/'src/obj/train_courier/rpg1/bin'
NAMES=('Common.dll','Common.pdb','Server.dll','Server.pdb','freelancer.exe','freelancer.pdb')

def function(source,signature):
    start=source.index(signature); begin=source.index('{',start); depth=1; end=begin+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}'); end+=1
    return source[start:end]+'\n'

def main():
    output=ROOT/'src/obj/customization/bin'; output.mkdir(parents=True,exist_ok=True)
    for name in ('Common.dll','Common.lib'): shutil.copy2(BUILD/name,output/name)
    (output/'flplusplus.ini').write_text('[flplusplus]\nsave_in_directory = true\n')
    save=(ROOT/'src/Server/server_savegame.cpp').read_text()
    code='struct FCostumeTarget { Costume* Target; CostumeDescriptions const* Descriptions; };\n'
    for sig in ('unsigned int CostumeTarget_FindPartId(', 'unsigned int CostumeTarget_FindAccessoryId(',
                'void Costume_AddAccessory(', 'bool LoadCostumeKey('): code+=function(save,sig)
    code+=function((ROOT/'src/Server/server_pub.cpp').read_text(),'static void Server_WriteCostume(')
    code+=function((ROOT/'src/freelancer/Client/perf_options.cpp').read_text(),'void SavePerfOptions(')
    (output/'save_functions.inc').write_text(code)
    compiler,env=compiler_env(); env['PATH']=str(ROOT/'bin')+';'+env['PATH']
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/MD','/D_ITERATOR_DEBUG_LEVEL=1',
                    '/I'+str(ROOT/'src/include'),'/I'+str(output),str(ROOT/'tools/customization/check.cpp'),
                    '/Fe:customization_check.exe','/Fo:customization_check.obj','/link',
                    '/LIBPATH:'+str(output),'/LIBPATH:'+str(ROOT/'bin'),'Common.lib','dacom.lib'],cwd=output,env=env,check=True)
    subprocess.run([str(output/'customization_check.exe')],cwd=output,env=env,check=True,timeout=60)
    checks=SOURCES+[BUILD/n for n in NAMES]
    assert (BUILD/'freelancer.exe').stat().st_mtime >= max(p.stat().st_mtime for p in SOURCES if '/Client/' in p.as_posix())
    report=ROOT/'out/customization/check'; report.mkdir(parents=True,exist_ok=True)
    (report/'verified.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in checks},indent=2))

if __name__=='__main__': main()
