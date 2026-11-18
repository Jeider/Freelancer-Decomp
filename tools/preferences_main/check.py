"""Verify cached mode probing against the original code without launching the game."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/preferences_main_hitch/check'
sys.path.insert(0, str(ROOT / 'tools/train_courier'))
from check_transfer_docking import block
from build_asf_hq import compiler_env

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    path = 'src/freelancer/Client/nn_preferences.cpp'
    current = (ROOT / path).read_text(encoding='utf-8')
    old = subprocess.check_output(['git', 'show', 'HEAD:' + path], cwd=ROOT).decode('utf-8')
    # Preserve the pre-change functions as a reference even after a later commit.
    reference = ROOT / 'out/preferences_main_hitch/reference_modes.cpp'
    if not reference.exists():
        assert 'ReadDisplayModeSnapshot' not in old
        reference.write_text(block(old, 'bool NnPreferences::FindVideoMode(') + '\n' +
                             block(old, 'void NnPreferences::ProbeModes('), encoding='utf-8')
    old = reference.read_text(encoding='utf-8')
    source = r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>
#ifdef FREELANCER_WIDESCREEN_SUPPORT
constexpr int kPrefVideoModeCount=48;
#else
constexpr int kPrefVideoModeCount=10;
#endif
struct FPipelineDisplayMode {int Index,Width,Height,RefreshRate,Format,Field14;};
struct PF{unsigned Bpp;};
PF const* PixelFormatGetDesc(int f){static PF p16{16},p32{32};return f==2?&p16:&p32;}
int PixelFormatFromD3D(int){return 0;}
struct Pipeline {
 std::vector<FPipelineDisplayMode> Modes;
 int Counts=0,Enums=0; bool Fail=false;
 int GetDisplayModeCount(unsigned* count){++Counts;if(Fail)return -1;*count=unsigned(Modes.size());return 0;}
 int GetDisplayModeEnum(unsigned i,void* out){++Enums;if(Modes.at(i).Format==-1)return -1;*static_cast<FPipelineDisplayMode*>(out)=Modes[i];return 0;}
 void QueryDeviceAbility(int,unsigned long* out){*out=1024u*1024*1024;}
} Device;
namespace DALib{auto* Pipeline=&Device;}
struct FPrefVideoMode{int Width,Height,Bpp;};
struct DisplaySettings{int width,height,pad[2],color_bpp,tail[5];};
DisplaySettings g_display{1920,1080,{0,0},32,{0,0,0,0,0}};
struct LegacyPreferences {
 FPrefVideoMode Modes[kPrefVideoModeCount]{};
 unsigned char bBigVram=0,bModeAvail[kPrefVideoModeCount]{};
 int ModeCount=0,CycleIndex[kPrefVideoModeCount]{};
 bool FindVideoMode(DisplaySettings*,int,int,int)const;
 void ProbeModes(int);
};
struct NnPreferences:LegacyPreferences {
 bool FindVideoMode(DisplaySettings*,int,int,int)const;
 void ProbeModes(int);
};
'''
    source += old.replace('NnPreferences::', 'LegacyPreferences::') + '\n'
    for marker in ('std::vector<FPipelineDisplayMode> ReadDisplayModeSnapshot(',
                   'bool FindVideoModeInSnapshot(', 'bool NnPreferences::FindVideoMode(',
                   'void NnPreferences::ProbeModes('):
        source += block(current, marker) + '\n'
    source += r'''
void CompareProbe(NnPreferences& now,LegacyPreferences& old){
 old.ProbeModes(-1); Device.Counts=Device.Enums=0; now.ProbeModes(-1);
 assert(Device.Counts==1 && Device.Enums==(Device.Fail?0:int(Device.Modes.size())));
 assert(now.ModeCount==old.ModeCount && now.bBigVram==old.bBigVram);
 assert(memcmp(now.bModeAvail,old.bModeAvail,sizeof(now.bModeAvail))==0);
 assert(memcmp(now.CycleIndex,old.CycleIndex,sizeof(now.CycleIndex))==0);
}
int main(){
 NnPreferences now;LegacyPreferences old;
 Device.Modes={{0,800,600,60,2,0},{1,800,600,60,3,0},{2,1920,1080,60,3,0},
   {3,1024,768,60,3,0},{4,1920,1080,144,3,0},{5,1280,1024,60,3,0},
   {6,1280,720,60,1,0},{7,1280,720,60,-1,0}};
 int widths[]={0,-1,800,1024,1280,1920},heights[]={0,-1,600,768,720,1080},bpps[]={-1,0,16,32};
 for(int w:widths)for(int h:heights)for(int b:bpps)for(int inherited:{16,32}){
  DisplaySettings a=g_display,c=g_display;a.color_bpp=c.color_bpp=inherited;
  bool expected=old.FindVideoMode(&a,w,h,b),actual=now.FindVideoMode(&c,w,h,b);
  assert(actual==expected && memcmp(&a,&c,sizeof(a))==0);
 }
 for(int i=0;i<kPrefVideoModeCount;++i){
  FPrefVideoMode m=i<6?FPrefVideoMode{Device.Modes[i].Width,Device.Modes[i].Height,i%2?32:16}:FPrefVideoMode{-1,-1,32};
  old.Modes[i]=now.Modes[i]=m;
 }
 CompareProbe(now,old);
 Device.Modes={{0,1024,768,60,3,0}};CompareProbe(now,old); // fresh snapshot after device changes
 Device.Modes.clear();CompareProbe(now,old);
 Device.Modes={{0,800,600,60,3,0}};Device.Fail=true;CompareProbe(now,old);
 Device.Fail=false;CompareProbe(now,old); // failures are never cached persistently
 puts("PASS: exact mode matching, first match/order, aspect rules, BPP/fallback, failed entries/count, unused slots, refresh after device changes; one enumeration per probe");
}
'''
    (OUT / 'check.cpp').write_text(source, encoding='utf-8')
    compiler, env = compiler_env()
    for wide in (False, True):
        name = 'wide' if wide else 'retail'
        command = [str(compiler / 'cl.exe'), '/nologo', '/EHsc', '/std:c++17']
        if wide:
            command.append('/DFREELANCER_WIDESCREEN_SUPPORT')
        subprocess.run(command + ['check.cpp', '/Fe:' + name + '.exe'], cwd=OUT, env=env, check=True)
        subprocess.run([str(OUT / (name + '.exe'))], cwd=OUT, env=env, check=True)

if __name__ == '__main__':
    main()
