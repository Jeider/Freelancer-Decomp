"""Compile and run standalone audio checks. Never runs Freelancer or FLServer."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env
sys.path.insert(0, str(ROOT / 'tools/train_courier'))
from check_transfer_docking import block

def main():
    out = ROOT / 'out/audio_timescale/check'
    out.mkdir(parents=True, exist_ok=True)
    compiler, env = compiler_env()
    subprocess.run([str(compiler / 'cl.exe'), '/nologo', '/EHsc', '/std:c++17',
                    '/I' + str(ROOT / 'src/include'),
                    str(ROOT / 'tools/audio_timescale/check.cpp'), '/Fe:check.exe'],
                   cwd=out, env=env, check=True)
    subprocess.run([str(out / 'check.exe')], cwd=out, env=env, check=True)
    manager = (ROOT / 'src/SoundManager/SoundManager.cpp').read_text(encoding='utf-8')
    generated = '''#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>
#include <cmath>
#include "audio/dsound8.h"
#include "audio_timescale.h"
#define Fdump(...) ((void)0)
''' + block(manager, 'int UploadSoundBuffer(') + '\n'
    generated += '#include "' + (ROOT / 'src/SoundManager/audio_timescale.inl').as_posix() + '"\n'
    generated += '#include "' + (ROOT / 'tools/audio_timescale/check_frequency.h').as_posix() + '"\n'
    generated += block(manager, 'double PitchToMultiplier(') + '\n'
    generated += block(manager, 'unsigned long Ftol32(') + '\n'
    mixer = block(manager, 'unsigned char FSoundManager::MixerApplyInstance(')
    start = mixer.index('FSoundArchetype* Archetype = LookupArchetype(PlayKey->GetArchId());')
    end = mixer.index('const float ArchGain', start)
    generated += 'void ApplyFrequency(FFrequencyNode* Node) { auto* PlayKey = Node->PlayKey;\n'
    generated += mixer[start:end] + '}\n'
    generated += '#include "' + (ROOT / 'src/SoundStreamer/audio_timescale.inl').as_posix() + '"\n'
    generated += '#include "' + (ROOT / 'tools/audio_timescale/check_buffer.cpp').as_posix() + '"\n'
    (out / 'buffer.cpp').write_text(generated, encoding='utf-8')
    subprocess.run([str(compiler / 'cl.exe'), '/nologo', '/EHsc', '/std:c++17',
                    '/I' + str(ROOT / 'src/include'), 'buffer.cpp', '/Fe:buffer.exe',
                    '/link', 'dsound.lib', 'user32.lib'], cwd=out, env=env, check=True)
    subprocess.run([str(out / 'buffer.exe')], cwd=out, env=env, check=True)

if __name__ == '__main__':
    main()
