"""Run the production panel flush with deferred-font routing instrumentation."""
import os
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[2]
out = root / 'src/obj/hud_tilt_checks'
out.mkdir(parents=True, exist_ok=True)
source = (root/'src/freelancer/Client/hud_tilt.cpp').read_text()
flush = re.search(r'    void Flush\(\)\n    \{.*?\n    \}', source, re.S)
assert flush, 'Production flush not found'
fixture = r'''
#include <cstdio>
#include <cstdlib>
#include <string>
#include <utility>
#include <vector>
static int target=0;
static std::vector<std::string> pending;
static std::vector<std::pair<int,std::string>> painted;
void Win3DImmedBatchFlushAll() {}
void Win3DImmedBatchReset() {}
void ButtonMontageFlushBatch() {}
void ButtonMontageEnsure() {}
// FontStringDrawChildren/number glyphs queue this separate material list; the
// real UiOverlayPrepPipeline drains it through ScreenQuadFlush(FontAtlasMaterialKey()).
void UiOverlayPrepPipeline() {
    for (auto const& text:pending) painted.emplace_back(target,text);
    pending.clear();
}
struct Batcher { void FlushAll(int) {} } batcher;
namespace DALib { Batcher* MaterialBatcher=&batcher; }
PRODUCTION_FLUSH
int main() {
    pending.emplace_back("flat-before"); Flush();
    target=1; pending.emplace_back("weapon-name"); pending.emplace_back("ammo-number"); Flush();
    target=0; pending.emplace_back("centred-child"); Flush();
    target=1; pending.emplace_back("panel-after-child"); Flush();
    target=0; Flush(); // final Win3DDrawAll must not paint the panel's glyphs again
    target=2; pending.emplace_back("target-name"); Flush();
    target=0; Flush();
    std::vector<std::pair<int,std::string>> expected={{0,"flat-before"},{1,"weapon-name"},
        {1,"ammo-number"},{0,"centred-child"},{1,"panel-after-child"},{2,"target-name"}};
    if (painted!=expected || !pending.empty()) {
        std::fprintf(stderr,"FAIL: deferred fonts escaped their HUD surface (%zu/6 painted)\n",painted.size());
        return 1;
    }
    puts("PASS: production flush routes text/numbers to their own panel, centred children stay flat, no late duplicate glyphs");
}
'''.replace('PRODUCTION_FLUSH', flush.group(0))
cpp = out/'font_routing.cpp'
cpp.write_text(fixture)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = os.environ.copy()
env['INCLUDE'] = ';'.join(map(str,[vc/'include',sdk/f'Include/{version}/ucrt',sdk/f'Include/{version}/shared',sdk/f'Include/{version}/um']))
env['LIB'] = ';'.join(map(str,[vc/'lib/x86',sdk/f'Lib/{version}/ucrt/x86',sdk/f'Lib/{version}/um/x86']))
exe = out/'font_routing.exe'
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc','/MT',str(cpp),f'/Fe{exe}'],cwd=out,env=env,check=True)
subprocess.run([str(exe)],cwd=out,check=True)
# Demonstrate that the original missing flush is actually detected by this fixture.
cpp.write_text(fixture.replace('        UiOverlayPrepPipeline();','        /* previous missing font flush */'))
old_exe = out/'font_routing_old.exe'
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc','/MT',str(cpp),f'/Fe{old_exe}'],cwd=out,env=env,check=True)
negative = subprocess.run([str(old_exe)],cwd=out,capture_output=True,text=True)
assert negative.returncode==1, 'Regression fixture did not detect the old bug'
cpp.write_text(fixture)
print('PASS: regression fixture rejects the original implementation')
