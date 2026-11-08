"""Exercise the production native slider, live preview, cancellation and INI persistence."""
from pathlib import Path
import ast
import os
import subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/base_neural/checks/preferences'
OUT.mkdir(parents=True,exist_ok=True)
# Reuse only the narrow GUI mocks, without executing the other test runner.
tree=ast.parse((ROOT/'tools/graphics_settings/check.py').read_text())
stub=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
          and any(isinstance(t,ast.Name) and t.id=='stub' for t in n.targets))
stub=stub.replace('struct NnPreferences:WinControl {',r'''
struct UiScroll:WinControl {
 int value=0; void SetStepMode(bool){} void SetPageField(float){} void SetActiveField(bool){}
 intptr_t SetProperty(int msg,uintptr_t a,uintptr_t b)override{
  if(msg==0x38)value=int(a);return WinControl::SetProperty(msg,a,b);
 }
};
struct NnPreferences:WinControl {
 UiScroll* NeuralStrengthSlider=nullptr;NnTextControl* NeuralStrengthValue=nullptr;
 int NeuralStrength=100,NeuralStrengthOriginal=100;
 NnButtonControl* NeuralEnableToggle=nullptr;bool NeuralEnabled=false,NeuralEnabledOriginal=false;
 UiScroll* CreateUIScroll(char const*,float const* at,float,float,int,int,int,int){
  auto* c=Own(new UiScroll);memcpy(c->position,at,sizeof(c->position));return c;
 }
''')
common=(ROOT/'src/Common/graphics_settings.cpp').read_text().replace('#include "common_misc.h"','')
grade=(ROOT/'src/freelancer/Client/color_grade_preferences.cpp').read_text().replace('#include "common_misc.h"','').replace('#include "port_config.h"','')
prefs=(ROOT/'src/freelancer/Client/base_neural_preferences.cpp').read_text().replace('#include "common_misc.h"','')
prefs=prefs.replace('#include "port_config.h"','')
prefs='#define Preferences NeuralPreferencesState\n#define State NeuralState\n'+prefs+'\n#undef Preferences\n#undef State\n'
ui=(ROOT/'src/freelancer/Client/nn_preferences_graphics.cpp').read_text()
ui=ui[ui.index('namespace\n{'):]
perf=(ROOT/'src/freelancer/Client/perf_options.cpp').read_text()
save=perf[perf.index('void SavePerfOptions('):]
extra=r'''
#include "base_neural_preferences.h"
float __cdecl PortConfigFloat(char const*,char const*,float){return 1.f;}
'''
checks=r'''
void Write(char const* text){FILE* f=fopen("PerfOptions.ini","w");assert(f);fputs(text,f);fclose(f);}
int main(int argc,char** argv){
 using namespace BaseNeural;assert(argc==2);
 if(!strcmp(argv[1],"reload")){
  assert(ConfiguredEnabled()&&Enabled());
  assert(ConfiguredStrengthPercent()==73&&StrengthPercent()==73);puts("PASS restart persisted 73%");return 0;
 }
 if(!strcmp(argv[1],"invalid")){
  Write("[BaseNeural]\nstrength_percent=101garbage\n");assert(StrengthPercent()==100);puts("PASS invalid fallback");return 0;
 }
 Write("[BaseNeural]\nstrength_percent=42\n");
 assert(StrengthPercent()==42&&DefaultStrengthPercent()==100);
 NnPreferences p;assert(p.CreateGraphicsRows());p.SnapshotGraphics();p.SetGraphicsHidden(false);
 assert(p.NeuralStrength==42&&p.NeuralStrengthSlider->value==42&&!p.GraphicsDirty());
 assert(p.NeuralStrengthValue->text==L"42%");
 assert(!Enabled()&&!ConfiguredEnabled());
 p.GraphicsProperty(0x30,p.NeuralEnableToggle,0);assert(Enabled()&&!ConfiguredEnabled());
 p.RevertGraphics();assert(!Enabled());
 // In-game preferences retain Anim=-2; only the main menu animates it to +1.
 p.Anim=-2;assert(!p.GraphicsProperty(0x3e,p.NeuralStrengthSlider,0));
 assert(StrengthPercent()==42);p.bInGame=true;
 assert(p.NeuralStrengthSlider->position[1]<p.GraphicsCells[8].Label->position[1]-.03f);
 assert(p.GraphicsHint->position[1]<p.NeuralStrengthSlider->position[1]-.03f);
 assert(p.GraphicsProperty(0x3e,p.NeuralStrengthSlider,0));
 assert(StrengthPercent()==0&&ConfiguredStrengthPercent()==42&&p.bDirty);
 SavePerfOptions("PerfOptions.ini");
 char path[MAX_PATH];GetFullPathNameA("PerfOptions.ini",MAX_PATH,path,nullptr);
 assert(GetPrivateProfileIntA("BaseNeural","strength_percent",999,path)==42);
 p.RevertGraphics();assert(StrengthPercent()==42&&!p.GraphicsDirty());
 p.bConfirmMode=true;assert(!p.GraphicsProperty(0x3e,p.NeuralStrengthSlider,100));assert(StrengthPercent()==42);p.bConfirmMode=false;
 p.GraphicsProperty(0x3e,p.NeuralStrengthSlider,100);assert(StrengthPercent()==100);
 p.GraphicsProperty(0x3e,p.NeuralStrengthSlider,73);p.CommitGraphics();p.SnapshotGraphics();
 assert(ConfiguredStrengthPercent()==73&&!p.GraphicsDirty());
 p.GraphicsProperty(0x26,p.DefaultsButton,0);assert(StrengthPercent()==100);p.RevertGraphics();assert(StrengthPercent()==73);
 p.SetGraphicsHidden(true);assert(p.NeuralStrengthSlider->mockHidden);p.SetGraphicsHidden(false);
 PreviewStrength(-1);assert(StrengthPercent()==0);PreviewStrength(101);assert(StrengthPercent()==100);
 CancelStrengthPreview();assert(StrengthPercent()==73);
 p.GraphicsProperty(0x30,p.NeuralEnableToggle,0);p.CommitGraphics();assert(Enabled());
 SavePerfOptions("PerfOptions.ini");
 assert(GetPrivateProfileIntA("BaseNeural","strength_percent",999,path)==73);
 puts("PASS in-game Anim=-2 input, menu animation guard, native slider, preview/cancel/defaults/persistence");
}
'''
(OUT/'check.cpp').write_text('#define FREELANCER_DLSS5\n'+stub+extra+common+grade+prefs+save+ui+checks)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc','/MT',
               f'/I{ROOT/"src/include"}',f'/I{ROOT/"src/freelancer/Client"}','check.cpp','/Fecheck.exe'],cwd=OUT,env=env,check=True)
for mode in ('exercise','reload','invalid'):
    subprocess.run([str(OUT/'check.exe'),mode],cwd=OUT,check=True)
