"""Exercise the production input/overlay and native sequence skip loop with engine stubs."""
import os
from pathlib import Path
import subprocess

repo = Path(__file__).resolve().parents[2]
client = repo / 'src/freelancer/Client'
out = repo / 'src/obj/cutscene_skip/check'
out.mkdir(parents=True, exist_ok=True)


def function(signature):
    source = (client / 'gf_script_object.cpp').read_text()
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


stub = r'''
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <vector>
#include <windows.h>
#include "cutscene_skip.h"
struct Script {
    int paused=0, fast=0, torn=0;
    void Pause(){++paused;}
    bool Update(int){if(paused){--paused;++fast;return true;}return false;}
    void Teardown(){++torn;}
};
struct Entry {int Kind=0;Script* Script=nullptr;};
struct FGfScriptSequence {
    int bLoop=0,bLetterbox=1,bPlaying=1,bActive=1,bStopped=0,bSkip=0,Field_0x15=0;
    Entry* Entries=nullptr;int Current=0,Count=0,Priority=0,stops=0,starts=0;
    int bOfferAnswered=0,bOfferAccepted=0,OfferType=0,bInfoClosed=0;
    int NextEntryIndex() const;
    int FindNextOfKinds(int const* kinds,int count) const {
        for(int i=Current+1;i<Count;++i)
            for(int k=0;k<count;++k)if(Entries[i].Kind==kinds[k])return i-Current;
        return Count-Current;
    }
    void StartEntry(int){CutsceneSkipInvalidate(this);++starts;}
    void StopPlayback(int){CutsceneSkipInvalidate(this);++stops;bStopped=1;bPlaying=0;}
    bool Update(int);
};
struct {std::vector<FGfScriptSequence*> Sequences;} G_GfScriptManager;
bool single=true,paused=false,G_bNnScreenUp=false;
bool SinglePlayer(){return single;}
bool IsClientServerTickPaused(){return paused;}
int GetMissionOfferAnsweredRetail(){return 0;}
int GetMissionOfferAcceptorIdRetail(){return 0;}
int GetPlayerConnectionId(){return 0;}
int hurried=0;
void NnArrivalTextHurry(){++hurried;}
namespace HudIds {constexpr unsigned CutsceneSkipPrompt=238226;}
struct FFontString {};
struct FFontStringDrawOrigin {float X=0,Y=0,Scale=0,Height=0;int Field10=0;};
int font=1;bool fontReady=true;unsigned G_RenderSurfaceWidth=1920,G_RenderSurfaceHeight=1080;
int* FindMenuFontImp(char const*){return fontReady?&font:nullptr;}
bool GetIdsStringWWithRawFallback(unsigned id,wchar_t* text,int){assert(id==238226);text[0]=L'x';return true;}
void FontStringSetText(FFontString*,wchar_t const*){}
void FontStringSetFont(FFontString*,int*){}
void FontStringGetExtent(FFontString*,int* size){size[0]=400;size[1]=20;}
int viewport[4]={2,3,900,700};unsigned color=0x12345678;int draws=0;
void Win3DGetViewport(int,int* result){std::copy(viewport,viewport+4,result);}
void UiOverlayPrepPipeline(){}
void Win3DSetViewportRect(int x,int y,int w,int h,char const*,int){viewport[0]=x;viewport[1]=y;viewport[2]=w;viewport[3]=h;}
unsigned FontAtlasDrawColor(){return color;}
void FontAtlasSetDrawColor(unsigned value){color=value;}
void FontStringDrawChildren(FFontStringDrawOrigin* origin,FFontString*,void*,void*){
    assert(viewport[0]==0&&viewport[1]==0&&viewport[2]==int(G_RenderSurfaceWidth));
    assert(origin->Field10==1&&origin->Y>0&&origin->Y<G_RenderSurfaceHeight);
    assert(origin->Scale==float(G_RenderSurfaceWidth)-32);++draws;
}
'''
checks = r'''
bool down(unsigned key,unsigned repeat=0){return CutsceneSkipHandleKey(WM_KEYDOWN,key,repeat);}
void release(unsigned key){assert(CutsceneSkipHandleKey(WM_KEYUP,key,0));}
void arm(){assert(down(VK_ESCAPE));release(VK_ESCAPE);}
int main(){
    assert(!down(VK_ESCAPE)&&!down(VK_RETURN));
    Script scripts[4];Entry entries[4];
    for(int i=0;i<4;++i)entries[i].Script=&scripts[i];
    FGfScriptSequence scene;scene.Entries=entries;scene.Count=4;
    G_GfScriptManager.Sequences={&scene};
    assert(!down(VK_RETURN));arm();assert(!scene.bSkip);
    for(unsigned width:{1024u,1920u,3440u}){
        G_RenderSurfaceWidth=width;CutsceneSkipDraw();
        assert(viewport[0]==2&&viewport[1]==3&&viewport[2]==900&&viewport[3]==700);
        assert(color==0x12345678);
    }
    assert(draws==6);fontReady=false;CutsceneSkipDraw();assert(draws==6);fontReady=true;
    assert(down(VK_ESCAPE));release(VK_ESCAPE);assert(!down(VK_RETURN));
    arm();assert(down(VK_RETURN,1u<<30));assert(!scene.bSkip);release(VK_RETURN);
    assert(down(VK_RETURN));assert(scene.bSkip&&hurried==1);
    assert(scene.Update(16));assert(scene.stops==1&&scene.Current==-1);
    for(auto const& script:scripts)assert(script.fast==1&&script.torn==1);
    assert(down(VK_RETURN,1u<<30));release(VK_RETURN);assert(!down(VK_RETURN));
    puts("PASS: Esc/Enter confirmation, repeat protection, native fast-forward and teardown, overlay/viewport");
    scene=FGfScriptSequence{};scene.Entries=entries;scene.Count=4;
    arm();scene.Current=1;assert(!down(VK_RETURN)); // Natural entry change cancels confirmation.
    arm();CutsceneSkipInvalidate(&scene);assert(!down(VK_RETURN));
    arm();paused=true;CutsceneSkipDraw();paused=false;assert(!down(VK_RETURN));
    arm();G_bNnScreenUp=true;CutsceneSkipDraw();G_bNnScreenUp=false;assert(!down(VK_RETURN));
    arm();CutsceneSkipHandleKey(WM_ACTIVATEAPP,0,0);assert(!down(VK_RETURN));
    assert(!CutsceneSkipHandleKey(WM_SYSKEYDOWN,VK_RETURN,0));
    for(int kind:{1,4,5,7,-1}){entries[1].Kind=kind;assert(!down(VK_ESCAPE));}
    entries[1].Kind=0;
    single=false;assert(!down(VK_ESCAPE));single=true;
    scene.bLoop=1;assert(!down(VK_ESCAPE));scene.bLoop=0;
    scene.bLetterbox=0;assert(!down(VK_ESCAPE));scene.bLetterbox=1;
    auto other=scene;other.Priority=10;G_GfScriptManager.Sequences.push_back(&other);
    arm();assert(down(VK_RETURN));release(VK_RETURN);assert(other.bSkip&&!scene.bSkip);
    other.bSkip=0;arm();G_GfScriptManager.Sequences.pop_back();assert(!down(VK_RETURN));
    puts("PASS: lifecycle cancellation, focus/pause/modal states, priorities, multiplayer/traffic exclusion");
    // Use the original skip-permission flag, not names, priorities or scene kinds.
    for(bool multiplayer:{false,true}){
        for(auto& entry:entries)entry.Kind=0;
        scene=FGfScriptSequence{};scene.Entries=entries;scene.Count=4;scene.Field_0x15=1;
        single=!multiplayer;int before=draws;
        assert(down(VK_ESCAPE));assert(scene.bSkip);CutsceneSkipDraw();assert(draws==before);
        assert(!down(VK_RETURN));assert(scene.Update(16));
        assert(down(VK_ESCAPE,1u<<30));release(VK_ESCAPE); // Don't leak repeats into UI.
        scene=FGfScriptSequence{};scene.Entries=entries;scene.Count=4;scene.Field_0x15=1;
        assert(CutsceneSkipRequest()&&scene.bSkip); // Bound/native skip event.
    }
    single=true;scene=FGfScriptSequence{};scene.Entries=entries;scene.Count=4;
    assert(CutsceneSkipRequest()&&!scene.bSkip); // Locked story still asks for Enter.
    scene.Field_0x15=1;assert(!down(VK_RETURN)); // Native permission change cancels a stale hint.
    puts("PASS: native scenes skip on Esc in SP/MP; only locked story scenes require Enter");
    // Exercise the real native update AND NextEntryIndex, stopping before choices/traffic.
    for(int boundary:{1,4,5,7}){
        for(auto& script:scripts)script=Script{};
        for(auto& entry:entries)entry.Kind=0;
        entries[1].Kind=boundary;
        scene=FGfScriptSequence{};scene.Entries=entries;scene.Count=4;scene.bSkip=1;
        assert(!scene.Update(16));assert(scene.Current==1&&!scene.bSkip&&!scene.stops);
        assert(scripts[0].fast==1&&scripts[1].fast==0&&scripts[2].fast==0);
        // Direct/native skip on a non-advancing entry cannot hang or choose an answer.
        scene.bSkip=1;assert(!scene.Update(16));assert(scene.Current==1&&!scene.bSkip);
    }
    puts("PASS: native skip stops at offer/info/traffic boundaries without auto-answering or looping");
    CutsceneSkipReset();
}
'''
source = '\n'.join(line for line in (client / 'cutscene_skip.cpp').read_text().splitlines()
                   if not line.startswith('#include'))
(out / 'check.cpp').write_text(stub + source + function('int FGfScriptSequence::NextEntryIndex() const')
                               + function('bool FGfScriptSequence::Update(int Ms)') + checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(str(p) for p in [vc / 'include', client] +
                        [sdk / 'Include' / version / x for x in ('ucrt', 'shared', 'um')])
env['LIB'] = ';'.join(str(p) for p in [vc / 'lib/x86'] +
                    [sdk / 'Lib' / version / x / 'x86' for x in ('ucrt', 'um')])
subprocess.run([str(vc / 'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W3', '/WX',
                '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe'], cwd=out, env=env, check=True)
subprocess.run([str(out / 'check.exe')], cwd=out, check=True, timeout=15)
