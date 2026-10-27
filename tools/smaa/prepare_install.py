"""Prepare the verified SMAA installer using the existing backup/restore workflow."""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[2]
template = (repo / 'tools/install_jumpgate_visual.py').read_text()
start = template.index('PAYLOAD = ')
end = template.index('\n\n\ndef main()', start)
payload = ('bin/freelancer.exe', 'bin/freelancer.pdb', 'bin/RP9.dll', 'bin/RP9.pdb',
           'DATA_EXTRA/SHADERS/scene_smaa.hlsl', 'DATA_EXTRA/SHADERS/SMAA/SMAA.hlsl',
           'DATA_EXTRA/SHADERS/SMAA/AreaTexDX9.dds', 'DATA_EXTRA/SHADERS/SMAA/SearchTex.dds',
           'DATA_EXTRA/SHADERS/SMAA/LICENSE.txt', 'DATA_EXTRA/SHADERS/SMAA/UPSTREAM.txt')
template = template[:start] + 'PAYLOAD = ' + repr(payload) + template[end:]
template = template.replace('from install_hyperspace_tunnel import',
    "import sys\nsys.path.insert(0, str(Path(__file__).resolve().parents[1]))\nfrom install_hyperspace_tunnel import")
template = template.replace('Path(__file__).resolve().parents[1]\nSTAGE',
                            'Path(__file__).resolve().parents[2]\nSTAGE')
template = template.replace('src/obj/jumpgate_install', 'src/obj/smaa/install')
template = template.replace('codex_jumpgate_', 'codex_smaa_')
scope_start = template.index("scope='jumpgate ")
scope_end = template.index("')", scope_start)
template = template[:scope_start] + "scope='SMAA 1x High before UI in space, cockpit and rooms; FXAA fallback retained; configurations untouched" + template[scope_end:]
template = template.replace('ordinary and alternate jumpgate visuals', 'SMAA 1x High')
template = template.replace('No game INIs, ALE, Common DLL or other gate types are changed.',
                            'Game configurations are unchanged; only client, RP9 and SMAA assets are installed.')
# Check both game executables; a running server may still hold shared libraries.
template = template.replace('    stopped()\n', '''    stopped()
    import subprocess
    processes = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq flserver.exe', '/FO', 'CSV', '/NH'],
                               capture_output=True, check=True)
    if b'flserver.exe' in processes.stdout.lower():
        raise RuntimeError('Close FLServer before installation/restoration.')
''')
installer = Path(__file__).with_name('install.py')
installer.write_text(template)
subprocess.run([sys.executable, str(installer)], check=True)
