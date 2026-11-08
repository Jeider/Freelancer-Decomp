"""Exercise production dialog parser, IDS access and selected wagon argument."""
from pathlib import Path
import json
import subprocess
import sys
from check_orders import function
from export import sections,one

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env


def main():
    source=(ROOT/'src/Content/RpgDialog.cpp').read_text(encoding='utf-8')
    structs='\n'.join(function(source,'struct '+name)+';' for name in ('Choice','Node','Dialog'))
    names=['std::wstring const& Localized(','Dialog* FindDialog(','Node* FindNode(',
           'void ReadNode(','void ReadChoice(','extern "C" unsigned __cdecl RpgDialogChoose(',
           'extern "C" int __cdecl RpgDialogChoiceCount(',
           'extern "C" unsigned __cdecl RpgDialogNodeTextIds(',
           'extern "C" unsigned __cdecl RpgDialogChoiceTextIds(']
    methods='\n'.join(function(source,n) for n in names)
    contact=sections(ROOT/'out/train_courier/payload/DATA/RPG/rh_biz_contact.ini')
    fixture=[]
    for kind,values in contact:
        if kind not in ('dialognode','dialogchoice'):continue
        rows='{'+','.join('{'+json.dumps(k)+','+json.dumps(v,ensure_ascii=True)+'}' for k,vs in values.items() for v in vs)+'}'
        fixture.append('{INI_Reader reader('+rows+');'+('ReadNode' if kind=='dialognode' else 'ReadChoice')+'(reader,G_Dialogs[1]);}')
    text=r'''
#include <cassert>
#include <string>
#include <unordered_map>
#include <vector>
#include <cstring>
#include <cstdio>
#include <windows.h>
char const* language="en";
char const* PortLanguage(){return language;}
unsigned CreateID(char const* s){unsigned n=2166136261;while(*s)n=(n^*s++)*16777619;return n;}
std::wstring Widen(char const* s){int n=MultiByteToWideChar(CP_UTF8,0,s,-1,0,0);std::wstring r(n,0);MultiByteToWideChar(CP_UTF8,0,s,-1,&r[0],n);r.resize(n-1);return r;}
struct INI_Reader {
    std::vector<std::pair<std::string,std::string>> rows;int i=-1;
    INI_Reader(std::vector<std::pair<std::string,std::string>> r):rows(r){}
    bool read_value(){return ++i<int(rows.size());}
    bool is_value(char const* k){return rows[i].first==k;}
    bool is_value_empty(int){return rows[i].second.empty();}
    int get_value_int(int){return std::stoi(rows[i].second);}
    char const* get_value_string(){return rows[i].second.c_str();}
};
unsigned picked=0,started=0;
void StartScript(char const*,unsigned,bool courier=false,unsigned first=0){++started;picked=first;}
'''+structs+r'''
std::unordered_map<unsigned,Dialog> G_Dialogs;
'''+methods+'\nint main(){\n'+'\n'.join(fixture)+r'''
    unsigned node=CreateID("tc_offer");
    assert(RpgDialogChoiceCount(1,node)==4);
    assert(RpgDialogNodeTextIds(1,node)==238278);
    unsigned counts[]={2,10,20};
    for(int i=0;i<3;++i){
        assert(RpgDialogChoiceTextIds(1,node,i)==238279+i);
        assert(RpgDialogChoose(1,node,i,1)==0 && picked==counts[i] && started==unsigned(i+1));
    }
    RpgDialogChoose(1,node,3,1);assert(started==3); // decline
    RpgDialogChoose(1,node,-1,1);RpgDialogChoose(1,node,4,1);assert(started==3);
    assert(RpgDialogChoiceTextIds(1,node,4)==0 && RpgDialogNodeTextIds(7,node)==0);
    std::wstring ru=L"RU",en=L"EN";assert(Localized(ru,en)==en);
    language="ru";assert(Localized(ru,en)==ru);
    puts("PASS: production vendor parser; resource IDs; 2/10/20 selected arguments; decline; bounds; RU/EN inline fallback");
}
'''
    out=ROOT/'src/obj/train_courier/vendor';out.mkdir(parents=True,exist_ok=True)
    cpp=out/'check.cpp';cpp.write_text(text,encoding='utf-8')
    compiler,env=compiler_env();exe=out/'check.exe'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2',str(cpp),
                    '/Fo'+str(out/'check.obj'),'/Fe'+str(exe)],env=env,cwd=out,check=True)
    subprocess.run([str(exe)],cwd=out,check=True)


if __name__=='__main__':main()
