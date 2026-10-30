"""Run production catalogue/input methods against a 50-ship market and UI doubles."""
from pathlib import Path
import os
import re
import subprocess

repo = Path(__file__).resolve().parents[2]
out = repo / 'src/obj/ship_trader_check'
out.mkdir(parents=True, exist_ok=True)
source = (repo / 'src/freelancer/Client/nn_ship_trader.cpp').read_text()

def function(signature):
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end] + '\n'

header = (repo / 'src/freelancer/Client/nn_ship_trader.h').read_text()
header = re.sub(r'^#include "[^\n]+\n|^#pragma once\n', '', header, flags=re.M)
header = header.replace('private:', 'public:')
stub = r'''
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cwchar>
#include <string>
#define FREELANCER_FLSHARP
struct Win3D {
    Win3D* parent = nullptr;
    virtual ~Win3D() = default;
    virtual bool Create(Win3D*, void*) { return true; }
    virtual void Update() {}
    virtual void Draw() {}
    virtual bool KeyEvent(unsigned, unsigned char*) { return false; }
    Win3D* GetParent() { return parent; }
    virtual bool HitTest(float const*) { return false; }
};
struct WinControl : Win3D {
    uintptr_t name = 0; bool checked = false, locked = false;
    std::string mesh;
    virtual intptr_t SetProperty(int msg, uintptr_t a, uintptr_t b) {
        if (msg == 0x1e) name = a;
        if (msg == 0xc) checked = a != 0;
        if (msg == 0x33) locked = b != 0;
        if (msg == 4) mesh = reinterpret_cast<char const*>(a);
        return 1;
    }
};
struct EventHandler { virtual bool OnEvent(unsigned) { return false; } };
class UiScroll : public WinControl { public: float value = 0; bool SetValue(float v) { value=v;return true; } };
struct GoodInfo {};
struct FClientMarket {} market;
int level = 0, bought = -1, closed = 0;
bool sp = true;
int GetPlayerRankLevelRetail() { return level; }
int GetClientLocationCurrentBase() { return 0; }
FClientMarket const* GetClientLocationBaseMarket(int) { return &market; }
float ClientMarketGetMinLevel(FClientMarket const*, unsigned id) { return id % 3 == 0 ? 10.f : 0.f; }
float ClientMarketGetMinRep(FClientMarket const*, unsigned id) { return id % 3 == 1 ? .8f : 0.f; }
bool SinglePlayer() { return sp; }
void NavBarCloseService(bool) {}
void NavBarShowDealerTab() {}
void NavBarOpenDealer(int index) { bought=index; }
void Win3DGetMouseRay(float*) {}
int G_ShipTraderClassIds[4] = {10,11,12,13};
template<class T> uintptr_t PointerArg(T const* ptr) { return reinterpret_cast<uintptr_t>(ptr); }
void FormatGroupedNumber(wchar_t* text, int value, int) { swprintf(text,100,L"%d",value); }
'''
methods = ''.join(function(sig) for sig in [
    'NnShipTrader::NnShipTrader()', 'NnShipTrader::~NnShipTrader()',
    'void NnShipTrader::RefreshRows()', 'int NnShipTrader::VisibleCount()',
    'void NnShipTrader::BindVisibleRows()', 'void NnShipTrader::ScrollTo(',
    'bool NnShipTrader::ScrollWheel(', 'bool NnShipTraderWheel(',
    'intptr_t NnShipTrader::SetProperty('])
checks = r'''
bool NnShipTrader::Create(Win3D*, void*) { return true; }
void NnShipTrader::Update() {}
void NnShipTrader::Draw() {}
bool NnShipTrader::KeyEvent(unsigned, unsigned char*) { return false; }
bool NnShipTrader::OnEvent(unsigned) { return false; }
void NnShipTrader::SelectRow(int row) { Selected=row; BindVisibleRows(); }
void NnShipTrader::Close() { ++closed; }

int main() {
    NnShipTrader t;
    WinControl controls[3][7], buy, current, cancel, currentFrame, description;
    UiScroll scroll;
    scroll.parent=&t; description.parent=&t;
    t.ListScroll=&scroll;t.BuyButton=&buy;t.CancelButton=&cancel;
    t.CurrentShipButton=&current;t.CurrentShipFrame=&currentFrame;
    t.Selected=-1;t.Hovered=-1;t.RowCount=50;t.PlayerWorth=100000;t.BaseFeeling=.5f;
    t.Entries.resize(50);
    for(int i=0;i<50;++i) {
        auto& e=t.Entries[i];e.GoodId=unsigned(100+i);e.NameId=1000+i;
        e.MarketIndex=i;e.Price=1000+i;e.MeshPath="ship.3db";
    }
    for(int i=0;i<3;++i) {
        for(auto& c:controls[i]) c.parent=&t;
        t.NameFrames[i]=&controls[i][0];t.NameIconFrames[i]=&controls[i][1];
        t.ShipMeshes[i]=&controls[i][2];t.ShipNames[i]=&controls[i][3];
        t.RowClassTexts[i]=&controls[i][4];t.ShipPrices[i]=&controls[i][5];
    }
    t.RefreshRows();
    assert(t.RowCount==50 && t.Entries.front().Status==0 && t.Entries.back().Status==2);
    for(auto const& e:t.Entries) {
        assert(e.GoodId==unsigned(100+e.MarketIndex));
        assert(e.NameId==1000+e.MarketIndex);
        assert(e.RepPercent==(e.GoodId%3==1 ? 80 : 0));
    }
    // Every package is reachable through a visible row, with correct labels and selection.
    for(int i=0;i<50;++i) {
        t.ScrollTo(i);int slot=i-t.FirstVisible;
        assert(slot>=0&&slot<3);
        assert(t.ShipNames[slot]->name==uintptr_t(t.Entries[i].NameId));
        t.SetProperty(0x26,PointerArg(t.NameFrames[slot]),0);
        assert(t.Selected==i&&t.NameFrames[slot]->checked);
        bought=-1;t.SetProperty(0x26,PointerArg(&buy),0);
        assert(bought==(t.Entries[i].Status ? -1 : t.Entries[i].MarketIndex));
    }
    // Scrollbar endpoints, wheel over text/icons, no wheel stealing from descriptions.
    t.SetProperty(0x3e,PointerArg(&scroll),0);assert(t.FirstVisible==0);
    assert(!NnShipTraderWheel(&description,-1));assert(t.FirstVisible==0);
    assert(NnShipTraderWheel(t.ShipNames[0],-3));assert(t.FirstVisible==1);
    assert(NnShipTraderWheel(t.NameIconFrames[0],1));assert(t.FirstVisible==0);
    t.SetProperty(0x3e,PointerArg(&scroll),1000);assert(t.FirstVisible==47);
    assert(NnShipTraderWheel(&scroll,-1)&&t.FirstVisible==47);
    t.ScrollTo(-100);assert(t.FirstVisible==0);
    // Re-sorting retains both the selected package and original purchase index.
    int locked=0;while(t.Entries[locked].Status!=1)++locked;
    t.SelectRow(locked);unsigned selectedId=t.Entries[locked].GoodId;
    int marketIndex=t.Entries[locked].MarketIndex;
    level=20;t.RefreshRows();assert(t.Entries[t.Selected].GoodId==selectedId);
    t.ScrollTo(47);bought=-1;t.SetProperty(0x26,PointerArg(&buy),0);
    assert(bought==marketIndex); // Selected ship stays purchasable while off screen.
    t.ScrollTo(t.Selected);int slot=t.Selected-t.FirstVisible;
    bought=-1;t.SetProperty(0x27,PointerArg(t.NameIconFrames[slot]),0);
    assert(bought==marketIndex);
    t.PlayerWorth=0;bought=-1;
    t.SetProperty(0x27,PointerArg(t.NameFrames[slot]),0);assert(bought==-1);
    t.SetProperty(0x26,PointerArg(&buy),0);assert(bought==-1);
    t.Selected=-2;t.SetProperty(0x26,PointerArg(&buy),0);assert(bought==-1);
    t.Selected=-1;t.SetProperty(0x26,PointerArg(&buy),0);assert(bought==-1);
    // A small market has no scroll range and never touches uncreated row controls.
    t.RowCount=1;t.Entries.resize(1);t.FirstVisible=0;t.Selected=-1;
    t.ScrollTo(100);t.RefreshRows();assert(t.VisibleCount()==1&&t.FirstVisible==0);
    assert(!NnShipTraderWheel(&scroll,-1));
    puts("PASS: 50 ships, stable package identity, purchase mapping, locks, wheel routing and limits");
}
'''
(out/'check.cpp').write_text(stub+header+methods+checks)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10'); version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(str(p) for p in [vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')])
env['LIB']=';'.join(str(p) for p in [vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')])
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX',
                '/EHsc','/MT','/fsanitize=address','/Zi','check.cpp','/Fecheck.exe'],cwd=out,env=env,check=True)
env['PATH']=str(vc/'bin/Hostx64/x86')+';'+env['PATH']
subprocess.run([str(out/'check.exe')],cwd=out,env=env,check=True)
