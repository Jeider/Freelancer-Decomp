"""Exercise the actual client answer/branch methods after campaign enrollment."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env
from check_transfer_docking import block


def main():
    source = (ROOT/'src/freelancer/Client/gf_script_object.cpp').read_text(encoding='utf-8')
    code = r'''
#include <cassert>
#include <cstdio>
#include "personal_story_offer.h"
bool sp=false; unsigned answered=77,acceptor=2,player=1;
bool SinglePlayer(){return sp;}
unsigned GetMissionOfferAnsweredRetail(){return answered;}
unsigned GetMissionOfferAcceptorIdRetail(){return acceptor;}
unsigned GetPlayerConnectionId(){return player;}
struct Script {void Pause(){}};
struct Entry {int Kind;struct Script* Script;};
struct FGfScriptSequence {
 int OfferType=PersonalStoryOfferType,OfferArg=77,OfferMissionId=0;
 int bOfferAnswered=0,bOfferAccepted=0,bOfferShown=0,bLetterbox=0,bInfoClosed=0;
 int* OfferDialog=nullptr;int Current=0,Count=4;
 Entry Entries[4]={{1,nullptr},{2,nullptr},{3,nullptr},{6,nullptr}};
 static void __cdecl OnOfferAnswer(void*,int);
 int NextEntryIndex()const;
 int FindNextOfKinds(int const*,int)const;
};
void SetMissionOfferSequenceRetail(FGfScriptSequence*){}
void SetLetterboxTarget(float,float){}
void SetClientMouseCursorDrawFlag(int){}
struct Server {
 int calls=0;unsigned who=0;bool accepted=false;
 void MissionResponse(unsigned offer,unsigned kind,bool yes,unsigned id){
   assert(offer==77&&kind==0);++calls;who=id;accepted=yes;
 }
} server;
Server* G_Server=&server;
'''
    for signature in ('void __cdecl FGfScriptSequence::OnOfferAnswer(',
                      'int FGfScriptSequence::NextEntryIndex()',
                      'int FGfScriptSequence::FindNextOfKinds('):
        code += block(source, signature)+'\n'
    code += r'''
int main(){
 // Reproduce the defect: pre-enrollment suppresses a retail group response.
 FGfScriptSequence old;old.OfferType=3;old.OnOfferAnswer(&old,0);
 assert(server.calls==0&&old.NextEntryIndex()==3);
 for(unsigned id: {1u,2u}) {
   player=id;FGfScriptSequence personal;
   personal.OnOfferAnswer(&personal,0);
   assert(server.who==id&&server.accepted&&personal.NextEntryIndex()==1);
   int once=server.calls;personal.OnOfferAnswer(&personal,0);assert(server.calls==once);
 }
 FGfScriptSequence declined;declined.OnOfferAnswer(&declined,1);
 assert(!server.accepted&&declined.NextEntryIndex()==2);
 answered=0;FGfScriptSequence pending;pending.OfferType=3;
 pending.OnOfferAnswer(&pending,0);assert(pending.NextEntryIndex()==0);
 sp=true;FGfScriptSequence solo;solo.OfferType=3;
 solo.OnOfferAnswer(&solo,0);assert(solo.NextEntryIndex()==1);
 puts("PASS actual client answer: enrollment bug reproduced; personal leader/guest acceptance, decline, no double send; retail MP wait and SP preserved");
}
'''
    code = '#include <initializer_list>\n'+code
    out=ROOT/'out/personal_offer/check'
    out.mkdir(parents=True,exist_ok=True)
    (out/'check.cpp').write_text(code,encoding='utf-8')
    compiler,env=compiler_env()
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/EHsc','/std:c++17',
                    '/I'+str(ROOT/'src/include'),'check.cpp','/Fe:check.exe'],cwd=out,env=env,check=True)
    subprocess.run([str(out/'check.exe')],cwd=out,env=env,check=True)


if __name__=='__main__':main()
