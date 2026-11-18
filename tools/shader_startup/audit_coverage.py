"""Inventory runtime shader requests and compare them with the startup manifest.

Read-only with respect to the game/cache. Generates native preprocessing checks;
does not compile HLSL or launch the game.
"""
import ast
import configparser
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/shader_startup/coverage'
GAME = Path('D:/Games/FL_MOD')
STRING = r'"(?:\\.|[^"\\])*"'
LEX = re.compile(STRING + r"|'(?:\\.|[^'\\])*'|//[^\n]*|/\*[\s\S]*?\*/")


def uncomment(text):
    return LEX.sub(lambda m: re.sub(r'[^\n]', ' ', m[0]) if m[0].startswith(('//', '/*')) else m[0], text)


def calls(text, name):
    pattern = re.compile(r'\b' + name + r'\s*\(')
    for match in pattern.finditer(text):
        if text[max(0, match.start()-2):match.start()] == '::':
            continue
        start, depth, args, cursor = match.end(), 1, [], match.end()
        while depth:
            if text[cursor] in ('"', "'"):
                quoted = LEX.match(text, cursor)
                cursor = quoted.end()
                continue
            char = text[cursor]
            if char in '([{': depth += 1
            if char in ')]}': depth -= 1
            if char == ',' and depth == 1 or not depth:
                args.append(text[start:cursor].strip())
                start = cursor + 1
            cursor += 1
        yield match.start(), args


def strings(expression):
    return [ast.literal_eval(x) for x in re.findall(STRING, expression)]


def inventory():
    records = []
    files = sorted((ROOT/'src/freelancer/Client').glob('*')) + sorted((ROOT/'src/RP9').glob('*'))
    for path in files:
        if path.suffix not in ('.cpp', '.inl'):
            continue
        text = uncomment(path.read_text(encoding='utf-8-sig'))
        constants = {m[1]: ast.literal_eval(m[2]) for m in re.finditer(
            r'\b(\w+)\s*\[\s*\]\s*=\s*(' + STRING + r')', text)}
        for method in ('CreateExProgram', 'ExCompileShaderPair'):
            for pos, args in calls(text, method):
                file_arg = args[1] if method == 'CreateExProgram' else args[0]
                names = strings(file_arg) or [constants.get(file_arg)]
                assert len(names) == 1 and names[0], (path, method, file_arg)
                name = names[0].replace('\\', '/').removeprefix('SHADERS/')
                vs = args[2] if method == 'CreateExProgram' else args[3] if len(args)>3 else '"VSMain"'
                ps = args[3] if method == 'CreateExProgram' else args[4] if len(args)>4 else '"PSMain"'
                for expr, profile in ((vs, 'vs_3_0'), (ps, 'ps_3_0')):
                    entries = strings(expr)
                    if expr.startswith('TravelQuality::TradeLaneEntry('):
                        quality = (ROOT/'src/include/travel_quality.h').read_text()
                        entries = strings(re.search(r'entries\[\]\s*=\s*\{([^}]+)\}', quality)[1])
                    assert entries, (path, expr)
                    for entry in entries:
                        records.append({'file': name, 'entry': entry, 'profile': profile,
                                        'include': method == 'CreateExProgram',
                                        'source': path.relative_to(ROOT).as_posix(), 'line': text.count('\n',0,pos)+1})
    # Direct CompileStage paths manually checked in RP9Ex/RoomMaterials; not calls
    # to either file-pair wrapper. Embedded/SMAA/surface variants are checked by C++.
    for name, entries, source, line in (
        ('local_shadow.hlsl', [('VSMain','vs_3_0'),('PSMain','ps_3_0')], 'src/RP9/RP9Ex.cpp',4204),
        ('scene_fxaa.hlsl', [('PSMain','ps_3_0')], 'src/RP9/RP9Ex.cpp',4559),
        ('room_contact.hlsl', [('PSMain','ps_3_0')], 'src/RP9/RP9RoomMaterials.inl',799)):
        for entry, profile in entries:
            records.append(dict(file=name,entry=entry,profile=profile,include=False,source=source,line=line))
    return records


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = inventory()
    unique = sorted({(r['file'],r['entry'],r['profile'],r['include']) for r in records})
    manifest = (ROOT/'src/RP9/RP9ShaderManifest.h').read_text()
    listed = set()
    for match in re.finditer(r'\{\s*"([^"\n]+\.hlsl)"\s*,\s*(null|nullptr|"\w+")\s*,\s*"(\w+)"\s*\}', manifest):
        name, vs, ps = match.groups()
        if vs.startswith('"'): listed.add((name,ast.literal_eval(vs),'vs_3_0'))
        listed.add((name,ps,'ps_3_0'))
    missing = [dict(file=f,entry=e,profile=p,installed=(GAME/'DATA_EXTRA/SHADERS'/f).exists())
               for f,e,p,_ in unique if (f,e,p) not in listed]
    prefs=configparser.RawConfigParser(strict=False)
    prefs.read(GAME/'SAVE/PerfOptions.ini',encoding='utf-8-sig')
    port=configparser.RawConfigParser(strict=False,inline_comment_prefixes=(';',))
    port.read(GAME/'bin/port.ini',encoding='utf-8-sig')
    report = {'runtime_file_stages':len(unique),'sites':records,'missing_file_stages':missing,
              'manifest_sha256':hashlib.sha256(manifest.encode()).hexdigest(),
              'current_preferences':{k:prefs.getint('Graphics',k,fallback=3) for k in
                                     ('relief_quality','highlight_quality','interiors','tradelane_quality')},
              'jump_prototype_enabled':port.getint('Render','jump_travel_prototype',fallback=0)!=0,
              'outside_rp9':{'source':'src/BaseNeuralBridge/bridge.cpp','stages':[
                  ['CopyGuides','cs_5_0'],['Flow','cs_5_0'],['Fullscreen','vs_5_0'],['Composite','ps_5_0']],
                  'enabled_in_installed_preferences':prefs.getint('BaseNeural','enabled',fallback=0)!=0},
              'notes':['Call inventory resolves literals, file-local constants and both arms of entry-point ternaries.',
                       'Direct CompileStage paths, embedded shaders, SMAA and surface predicates are reviewed separately.',
                       'Shader-object creation and all possible driver pipeline states are not equivalent to source compilation.']}
    (OUT/'runtime_stages.tsv').write_text(''.join(f'{f}\t{e}\t{p}\t{int(inc)}\n' for f,e,p,inc in unique),encoding='utf-8')
    (OUT/'inventory.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Runtime file stages:',len(unique),'missing:',json.dumps(missing))
    sys.path.insert(0,str(ROOT/'tools/nebula_control'))
    from build_asf_hq import compiler_env
    compiler,env=compiler_env()
    env['INCLUDE'] += ';C:/DXSDK_Jun10/Include'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/EHsc','/std:c++17','/utf-8','/W4','/O2',
                    '/D_CRT_SECURE_NO_WARNINGS','/Isrc/RP9','tools/shader_startup/audit_coverage.cpp',
                    '/Fo'+str(OUT/'audit.obj'),'/Fe'+str(OUT/'audit.exe'),'/link',
                    'C:/DXSDK_Jun10/Lib/x86/d3dx9.lib'],cwd=ROOT,env=env,check=True)
    env['PATH']=str(GAME/'bin')+';'+env['PATH']
    with (OUT/'keys.tsv').open('wb') as stream:
        subprocess.run([str(OUT/'audit.exe'),str(GAME/'DATA_EXTRA/SHADERS')+'/',str(OUT/'runtime_stages.tsv')],
                       cwd=ROOT,env=env,stdout=stream,check=True)
    rows=[line.split('\t') for line in (OUT/'keys.tsv').read_text().splitlines()]
    report['quality_profiles_checked']=64
    report['preprocessed_unique_requests']=int(next(r[1] for r in rows if r[0]=='preprocessed_unique'))
    report['potential_missing_surface_variants']=sorted({r[4].split(',room=')[0] for r in rows if r[0]=='missing_variant'})
    report['surface_variant_limit']='Runtime predicates and exact preprocessed keys checked; no assertion that current model assets use every cubemap route.'
    (OUT/'inventory.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Key comparison:', OUT/'keys.tsv')


if __name__ == '__main__':
    main()
