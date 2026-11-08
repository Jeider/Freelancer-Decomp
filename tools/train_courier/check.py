"""Verify courier rules and the actual IVP coupling implementation."""
from pathlib import Path
import argparse
import os
import subprocess
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--boarding-only',action='store_true')
    parser.add_argument('--rules-only',action='store_true')
    parser.add_argument('--sizes-only',action='store_true')
    options=parser.parse_args()
    compiler,env=compiler_env()
    out=ROOT/'src/obj/train_courier/rpg1/bin'
    shutil.copy2(ROOT/'src/obj/train_consist/check_dacom.ini',out/'check_dacom.ini')
    fixtures=ROOT/'out/train_courier/physics'
    fixtures.mkdir(parents=True,exist_ok=True)
    for path in (ROOT/'out/train_courier/payload/DATA/SHIPS/UTILITY/FREIGHT_TRAIN').glob('train_wagons_*.*'):
        shutil.copy2(path,fixtures/path.name)
    for ext in ['cmp','sur']:shutil.copy2(ROOT/'out/train_yard'/('train_locomotive.'+ext),fixtures/('train_locomotive.'+ext))
    for ext in ['cmp','sur']:shutil.copy2(ROOT/'out/train_courier/payload/DATA/SHIPS/UTILITY/FREIGHT_TRAIN'/('train_boarding.'+ext),fixtures/('train_boarding.'+ext))
    env['PATH']=str(ROOT/'bin')+';'+env['PATH']
    tests=[('rules',Path(__file__).with_name('check.cpp'),[],[]),
           ('physics',ROOT/'tools/train_consist/yard_check.cpp',
            ['Common.lib','DALib.lib','dacom.lib'],[str(ROOT/'out/train_yard')]),
           ('sizes',Path(__file__).with_name('sizes_check.cpp'),
            ['Common.lib','DALib.lib','dacom.lib'],[str(fixtures)]),
           ('boarding',Path(__file__).with_name('boarding_check.cpp'),
            ['Common.lib','DALib.lib','dacom.lib'],[str(fixtures)])]
    if options.boarding_only:tests=[test for test in tests if test[0]=='boarding']
    if options.rules_only:tests=[test for test in tests if test[0]=='rules']
    if options.sizes_only:tests=[test for test in tests if test[0]=='sizes']
    for name,source,libs,args in tests:
        command=[str(compiler/'cl.exe'),'/nologo','/std:c++17','/W4','/EHsc','/O2','/MD',
                 '/D_ITERATOR_DEBUG_LEVEL=1','/D_CRT_SECURE_NO_WARNINGS',
                 '/I'+str(ROOT/'src/include'),str(source),'/Fe'+name+'.exe',
                 '/Fo'+name+'.obj','/link','/LIBPATH:'+str(out),'/LIBPATH:'+str(ROOT/'bin')]+libs
        with (out/(name+'_compile.log')).open('wb') as log:
            result=subprocess.run(command,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:print((out/(name+'_compile.log')).read_text(errors='replace'))
        result.check_returncode()
        with (out/(name+'.log')).open('wb') as log:
            result=subprocess.run([str(out/(name+'.exe'))]+args,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
        print((out/(name+'.log')).read_text(errors='replace'))
        result.check_returncode()

if __name__=='__main__':main()
