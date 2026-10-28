"""Build and exercise the production XML reader with the installed subtitle corpora."""
from pathlib import Path
import os
import subprocess

root = Path(__file__).resolve().parents[2]
out = root / 'src/obj/subtitle_check'
out.mkdir(parents=True, exist_ok=True)
test = out / 'check.cpp'
test.write_text(r'''
#include "subtitle_data.h"
#include <cassert>
#include <fstream>
#include <iostream>
using namespace NativeSubtitles;
int wmain(int argc, wchar_t** argv) {
    assert(AudioKey(L"D:\\game\\DATA\\AUDIO\\Echo.utf|0xAbC") == L"echo.utf|0x00000abc");
    assert(AudioKey(L"AUDIO\\MOD\\m01\\line.wav") == L"mod/m01/line.wav");
    Entry entry; entry.parts={{.05,5.48,L"first"},{5.85,9.49,L"second"}};
    assert(entry.At(0).empty() && entry.At(.05)==L"first" && entry.At(5.48).empty());
    assert(entry.At(5.85)==L"second" && entry.At(10).empty());
    entry.parts.clear(); entry.text=L"static"; assert(entry.At(200)==L"static");
    Playback play{&entry};
    play.Sync(-1,false,false,1); assert(!play.started && play.time==0);
    play.Sync(-1,true,false,1); assert(play.started && play.time==1);
    play.Sync(-1,true,true,20); assert(play.time==1); // streamed pause freezes
    play.Sync(-1,true,false,.5f); assert(play.time==1.5);
    play.Sync(6,true,false,1); assert(play.time==6); // WAV follows audio, not frame delta
    play.Sync(.25,true,false,1); assert(play.time==.25); // seek/replay
    Database db; std::wstring error;
    auto load = [&](char const* xml) {
        {std::ofstream f("fixture.xml",std::ios::binary);f<<xml;}
        return ReadXml(L"fixture.xml",db,error);
    };
    assert(load("<Subtitles><Dynamic AudioFile='test.wav' TextArea='Cinematic'><Part Start='1:02.5' End='1:03'>A &amp; B</Part></Dynamic></Subtitles>"));
    assert(db.at(L"test.wav").At(62.5)==L"A & B");
    assert(!load("<Subtitles><Static AudioFile='test.wav' TextArea='Cinematic'>bad"));
    assert(db.at(L"test.wav").At(62.5)==L"A & B"); // failed parse is atomic
    assert(!load("<!DOCTYPE Subtitles [<!ENTITY a SYSTEM 'file:///C:/secret'>]><Subtitles><Static AudioFile='x' TextArea='Cinematic'>&a;</Static></Subtitles>"));
    assert(!load("<Subtitles><Dynamic AudioFile='test.wav' TextArea='Cinematic'><Part Start='2' End='1'>x</Part></Dynamic></Subtitles>"));
    assert(!load("<Subtitles><Static AudioFile='x' TextArea='Cinematic'/><Static AudioFile='x' TextArea='News'/></Subtitles>"));
    for(int i=1;i<argc;++i) {
        if(!ReadXml(argv[i],db,error)) {std::wcerr<<error<<L"\n";return 1;}
        assert(!db.empty());
        if(i==1) { assert(db.size()==896); assert(db.at(L"mod/m01/m01_intro_0010_trent.wav").text.front()==L'\u041f'); }
        if(i==2) assert(db.size()==9802 && !db.at(L"mixes/mix_s002xe.wav").parts.empty());
        std::wcout<<L"Parsed "<<db.size()<<L" entries: "<<argv[i]<<L"\n";
    }
    std::cout<<"PASS: keys, UTF IDs, intervals, entities, invalid XML, DTD rejection and atomic load\n";
}
''', encoding='utf-8')
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = os.environ.copy()
env['INCLUDE'] = ';'.join(map(str, [vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um','winrt')]))
env['LIB'] = ';'.join(map(str, [vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo','/std:c++17','/EHsc','/W4','/WX',
                '/I'+str(root/'src/freelancer/Client'), str(test),
                str(root/'src/freelancer/Client/subtitle_data.cpp'),'/Fecheck.exe','/link','ole32.lib'],cwd=out,env=env,check=True)
subprocess.run([str(out/'check.exe'), 'D:/games/FL_MOD/BUILDS/RU_NORMAL/EXE/subtitles.xml',
                'D:/work/Freelancer English Subtitles/EXE/subtitles.xml'],cwd=out,check=True)
