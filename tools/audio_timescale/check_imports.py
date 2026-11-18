"""Check the built client/extension against the DLLs actually installed in bin/."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / 'out/audio_timescale/build'
GAME = Path('D:/Games/FL_MOD/bin')
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env

def main():
    compiler, env = compiler_env()
    def dump(option, path):
        return subprocess.check_output([str(compiler / 'dumpbin.exe'), option, str(path)], env=env, text=True)
    def exports(path):
        return set(re.findall(r'^\s+\d+\s+[0-9A-F]+\s+(?:[0-9A-F]+\s+)?(\S+)', dump('/exports', path), re.M))
    cache = {}
    checked = 0
    for name in ('freelancer.exe', 'SoundManager.dll', 'SoundStreamer.dll'):
        assert exports(GAME / name) <= exports(BIN / name), 'Installed exports removed: ' + name
        dependency = None
        for line in dump('/imports', BIN / name).splitlines():
            match = re.match(r'^    (\S+\.dll)\s*$', line, re.I)
            if match:
                dependency = match.group(1)
                continue
            symbol = re.match(r'^\s+[0-9A-F]+\s+(\?\S+|[A-Za-z_]\S*)\s*$', line)
            if not symbol or not dependency or not (GAME / dependency).exists():
                continue
            if dependency not in cache:
                cache[dependency] = exports(GAME / dependency)
            assert symbol.group(1) in cache[dependency], (name, dependency, symbol.group(1))
            checked += 1
    assert 'PortInstallAudioTimeScaleV1' in exports(BIN / 'SoundManager.dll')
    assert 'PortSetStreamTimeScaleV1' in exports(BIN / 'SoundStreamer.dll')
    print(f'PASS: {checked} imports resolve against installed DLLs; exports preserved; audio extension exported')

if __name__ == '__main__':
    main()
