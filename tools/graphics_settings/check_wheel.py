"""Exercise the real WheelScroll routing without starting the game."""
from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/obj/graphics_wheel_check'
OUT.mkdir(parents=True, exist_ok=True)
source = (ROOT / 'src/freelancer/Client/flplusplus.cpp').read_text()
source = source[source.index('bool FlplusplusHasWheelScroll('):source.rindex('#endif')]
stub = r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <typeinfo>
struct Win3D {
 virtual ~Win3D()=default;
 Win3D* parent=nullptr;const char* name="";
 Win3D* GetParent()const{return parent;}const char* GetName()const{return name;}
};
struct UiScroll:Win3D {
 bool shown=true;int value=0,max=20,calls=0;
 bool IsShown()const{return shown;}
 void WheelStep(bool up){++calls;value+=up?-1:1;if(value<0)value=0;if(value>max)value=max;}
};
struct BaseRichTextWin:Win3D {UiScroll* ScrollBarV=nullptr;};
struct RichTextWin:BaseRichTextWin {};struct UiRichTextWin:BaseRichTextWin {};
struct NnTextControl:Win3D {};struct UiFastTable:Win3D {};struct UiListBox:Win3D {};
struct WireButtonControl:Win3D {};struct NnButtonControl:Win3D {};
struct NnInventory:Win3D {UiScroll* InventoryScroll=nullptr;};
struct NnMissionVendor:Win3D {UiScroll* SummaryScroll=nullptr;};
struct NnNews:Win3D {UiScroll* Scroll=nullptr;};
struct NnLoadSave:Win3D {UiScroll* Scroll=nullptr;};
struct PageCharacterSelectSingle:Win3D {UiScroll* CharScroll=nullptr;};
struct PageServerSelect:Win3D {UiScroll* ServerScroll=nullptr;};
struct NnPreferences:Win3D {
 int CurPage=2,GraphicsTab=0;UiScroll* KeyScroll=nullptr;UiScroll* GraphicsScroll=nullptr;
};
struct NeuroNetNavMap:Win3D {UiScroll* ObjectiveScroll=nullptr;UiScroll* BaseListScroll=nullptr;};
'''
checks = r'''
bool Wheel(Win3D* window,int value){return FlplusplusHasWheelScroll(window)&&FlplusplusWindowWheel(window,value);}
int main(){
 NnPreferences prefs;prefs.name="NN_Preferences";
 UiScroll graphics,keys;graphics.parent=keys.parent=&prefs;graphics.max=3;
 prefs.GraphicsScroll=&graphics;prefs.KeyScroll=&keys;
 NnButtonControl toggle;toggle.parent=&prefs;
 WireButtonControl choice;choice.parent=&prefs;
 Win3D child;child.parent=&toggle;
 for(Win3D* origin:{static_cast<Win3D*>(&graphics),static_cast<Win3D*>(&prefs),
                  static_cast<Win3D*>(&toggle),static_cast<Win3D*>(&choice),&child}){
  graphics.value=0;assert(Wheel(origin,-1));assert(graphics.value==1);
  assert(Wheel(origin,-1));assert(graphics.value==2);
  assert(Wheel(origin,-1));assert(graphics.value==3);
  assert(Wheel(origin,-1));assert(graphics.value==3);
  assert(Wheel(origin,1));assert(graphics.value==2);
  int calls=graphics.calls;assert(!Wheel(origin,0));assert(graphics.calls==calls);
 }
 graphics.shown=false;int calls=graphics.calls;
 assert(!Wheel(&toggle,-1)&&!Wheel(&graphics,-1));assert(graphics.calls==calls);
 prefs.CurPage=0;assert(Wheel(&toggle,-1));assert(keys.value==2);
 prefs.CurPage=1;assert(!Wheel(&toggle,-1));
 prefs.CurPage=2;prefs.GraphicsTab=1;assert(!Wheel(&toggle,-1));
 // Existing rich text / inventory routes keep the plugin's two steps per notch.
 UiScroll other;RichTextWin text;text.ScrollBarV=&other;
 assert(Wheel(&text,-1));assert(other.value==2);
 NnInventory inventory;inventory.name="NN_Inventory";inventory.InventoryScroll=&other;
 WireButtonControl item;item.parent=&inventory;
 assert(Wheel(&item,-1));assert(other.value==4);
 NnButtonControl unrelated;assert(!Wheel(&unrelated,-1));
 puts("PASS wheel over scrollbar, controls and descendants; bounds, hidden pages, legacy routes");
}
'''
(OUT / 'check.cpp').write_text('#include <initializer_list>\n' + stub + source + checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(map(str, [vc/'include'] + [sdk/'Include'/version/x for x in ('ucrt','shared','um')]))
env['LIB'] = ';'.join(map(str, [vc/'lib/x86'] + [sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX', '/EHsc', '/MT',
                'check.cpp', '/Fecheck.exe'], cwd=OUT, env=env, check=True)
subprocess.run([str(OUT/'check.exe')], cwd=OUT, check=True)
