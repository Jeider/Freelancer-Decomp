"""Regression for real EngBase playback binding with missing ship parts; offline only."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/obj/ship_damage'


def function(source, name):
    # Skip forward declarations; copy the production definition, not a reimplementation.
    pattern = r'^static [^\n]*\b' + name + r'\([^;{]*\)\s*\{'
    match = re.search(pattern, source, re.M)
    if not match:
        raise ValueError(name)
    start = match.start(); end = match.end(); depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end] + '\n'


STUB = r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <map>
#include <set>
#include <vector>
#include <cstddef>
#define DACOM_API
using GENRESULT=long; constexpr GENRESULT GR_OK=0;
constexpr int kFdumpWarning=1; const char* G_FdumpFileAnim="test";
void EngBaseFdump(int,const char*,int,const char*,const char*){}
struct FChannelArchetypeObject {
    int refs=1;float duration=2;
    void AddRef(){++refs;} void Release(){assert(refs>0);--refs;}
    void GetDuration(float* out){*out=duration;} void GetFlags(unsigned long* out){*out=1;}
};
struct FTypedChannel {
    FChannelArchetypeObject* Archetype=nullptr;
    unsigned long PlayState=0, LoopFlags=0;
    float Time=0,Weight=1,Scale=1,Field_0x30=0;
    unsigned long BindMap(unsigned long*,void*){return 1;}
};
FTypedChannel* NewTypedChannelWithArchetype(unsigned long,FChannelArchetypeObject* a){
    auto* t=new FTypedChannel();t->Archetype=a;a->AddRef();return t;
}
struct FAnimTrack {FChannelArchetypeObject* Channel;unsigned long ParentCrc=0,ChildCrc=0;
    const char* ParentName="Root";const char* ChildName="Wing";};
struct FAnimNameEntry {FChannelArchetypeObject* LongestChannel;const char* Name;std::vector<FAnimTrack> Tracks;};
struct FAnimScript {FAnimNameEntry* entry;int refs=1;void AddRef(){++refs;}void Release(){--refs;}};
struct FEngineInstance {unsigned mask;};
struct FAnimBindOut {unsigned long Kind;void* Extra;void* Typed;FEngineInstance* Instance;};
unsigned char BindTrackTarget(FAnimBindOut*,FEngineInstance* root,FAnimTrack* track,void*,void*,unsigned char* already){
    *already=0;return (root->mask&track->ChildCrc)!=0;
}
struct FAnimPlayback {FAnimNameEntry* Name=nullptr;FEngineInstance* Root=nullptr;
    std::vector<FTypedChannel*> Typed;FTypedChannel* LongestTyped=nullptr;FAnimScript* Script=nullptr;};
using FAnimPlaybackMap=std::map<long,FAnimPlayback>;
struct FAnimationObject {FAnimPlaybackMap* Playbacks;std::set<FTypedChannel*>* Channels;unsigned long NextPlaybackId=237;};
bool IsValidAnimScript(FAnimScript* s){return s!=nullptr;}
namespace DACOM_CRC {unsigned long GetCRC32(const char*){return 1;}}
FAnimNameEntry* FindAnimName(FAnimScript* s,unsigned long){return s->entry;}
void MixerUnbindTyped(FAnimationObject*,FTypedChannel*){}
unsigned long PlaybackBindAll(FAnimPlayback* p,float*,unsigned long result){
    for(auto* t:p->Typed)t->PlayState|=1;return result;
}
'''

CHECKS = r'''
int main(){
    FChannelArchetypeObject left,right;
    FAnimNameEntry name{&left,"Sc_launch extend",{{&left,0,1},{&right,0,2}}};
    FAnimScript script{&name}; FAnimPlaybackMap playbacks;std::set<FTypedChannel*> channels;
    FAnimationObject anim{&playbacks,&channels};
    // Both absent: exactly the saved-ship case from the 16:54:48 dump. No phantom handle.
    FEngineInstance gone{0};auto next=anim.NextPlaybackId;
    auto id=AnimationPlayScript(&anim,&script,&gone,name.Name,nullptr,nullptr);
    assert(id==0xffffffffUL&&playbacks.empty()&&channels.empty()&&anim.NextPlaybackId==next);
    assert(script.refs==1&&left.refs==1&&right.refs==1);
    puts("PASS: both wings missing rejects launch without publishing a handle or retaining channels");
    // One lost wing must not disable the surviving wing's animation.
    for(unsigned mask:{1u,2u,3u}){
        FEngineInstance ship{mask};
        id=AnimationPlayScript(&anim,&script,&ship,name.Name,nullptr,nullptr);
        assert(id!=0xffffffffUL);auto& p=playbacks.at(id);
        assert(p.Typed.size()==(mask==3?2:1)&&p.LongestTyped);
        p.LongestTyped->Time=.75f;
        assert(AnimationGetStoredDuration(&anim,id)==.75f);
        assert(PlaybackEvalStoredTyped(&p)==0);
        for(auto* t:p.Typed)assert(t->PlayState&1);
        assert(AnimationDestroyScript(&anim,id)==GR_OK);
        assert(playbacks.empty()&&channels.empty()&&script.refs==1&&left.refs==1&&right.refs==1);
    }
    puts("PASS: either surviving wing and intact pair retain time, resume and balanced ownership");
    // Existing empty records and an unknown id are safe even outside PlayScript's entry point.
    FAnimPlayback empty;playbacks.emplace(900,empty);
    assert(AnimationGetStoredDuration(&anim,900)==-1.f);
    assert(AnimationGetStoredDuration(&anim,901)==-1.f);
    assert(PlaybackEvalStoredTyped(&playbacks.at(900))==0xffffffffUL);
    playbacks.clear();
    FAnimNameEntry noTracks{nullptr,"Empty",{}};FAnimScript emptyScript{&noTracks};
    assert(AnimationPlayScript(&anim,&emptyScript,&gone,noTracks.Name,nullptr,nullptr)==0xffffffffUL);
    assert(emptyScript.refs==1&&playbacks.empty()&&channels.empty());
    puts("PASS: empty record time/resume, unknown handle and trackless script");
}
'''


def main():
    sys.stdout.reconfigure(errors='replace')
    parser=argparse.ArgumentParser();parser.add_argument('--build',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'src/EngBase/EngBase.cpp').read_text()
    names=('FreePlaybackTyped','ClonePlaybackTypedChannels','BindPlaybackTracks','PlaybackStoredDuration',
           'PlaybackEvalStoredTyped','FindPlaybackRecord','AnimationGetStoredDuration','AnimationPlayScript','AnimationDestroyScript')
    (OUT/'check.cpp').write_text(STUB+'\n'.join(function(source,n) for n in names)+CHECKS)
    vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
    sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
    env=dict(os.environ)
    env['INCLUDE']=';'.join(str(p) for p in [vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')])
    env['LIB']=';'.join(str(p) for p in [ROOT/'bin',vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')])
    with (OUT/'check.log').open('wb') as log:
        subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/EHsc','/MT',
                        'check.cpp','/Fecheck.exe'],cwd=OUT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        subprocess.run([str(OUT/'check.exe')],cwd=OUT,stdout=log,stderr=subprocess.STDOUT,check=True)
    print((OUT/'check.log').read_text(errors='replace'))
    if not args.build:return
    binary=OUT/'bin';obj=OUT/'EngBase';binary.mkdir(exist_ok=True);obj.mkdir(exist_ok=True)
    (binary/'dacom.lib').write_bytes((ROOT/'bin/dacom.lib').read_bytes())
    command=['C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe',
        str(ROOT/'src/EngBase/EngBase.vcxproj'),'/t:Build','/p:Configuration=Release','/p:Platform=Win32',
        '/p:PlatformToolset=v145','/p:BuildProjectReferences=false','/p:FreelancerRp9=1',
        '/p:FreelancerRpgWorld=1','/p:Dx8SdkDir=C:/DXSDK','/p:Dx9SdkDir=C:/DXSDK_Jun10',
        '/p:OutDir='+str(binary)+'/', '/p:IntDir='+str(obj)+'/', '/m:2','/nr:false','/v:minimal','/nologo']
    with (OUT/'build.log').open('wb') as log:
        result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
    print((OUT/'build.log').read_text(errors='replace')[-5000:]);result.check_returncode()
    print('BUILD READY',binary/'EngBase.dll')


if __name__=='__main__':main()
