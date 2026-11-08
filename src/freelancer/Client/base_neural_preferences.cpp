#include "base_neural_preferences.h"
#include "port_config.h"
#include "common_misc.h"
#include <windows.h>
#include <cmath>
#include <cstdlib>

namespace
{
    int ClampPercent(int value) { return value<0?0:value>100?100:value; }
    struct Preferences
    {
        int saved, preview;
        bool savedEnabled=false,previewEnabled=false;
        Preferences()
        {
            saved=BaseNeural::DefaultStrengthPercent();
            savedEnabled=PortConfigInt("BaseNeural","enabled",0)==1;
            char directory[MAX_PATH]={},path[MAX_PATH]={},text[64]={};
            if(GetUserDataPath(directory))
            {
                _snprintf_s(path,sizeof(path),_TRUNCATE,"%s\\PerfOptions.ini",directory);
                savedEnabled=GetPrivateProfileIntA("BaseNeural","enabled",savedEnabled?1:0,path)==1;
                GetPrivateProfileStringA("BaseNeural","strength_percent","",text,sizeof(text),path);
                char* end=nullptr;long parsed=std::strtol(text,&end,10);
                while(end&&(*end==' '||*end=='\t'))++end;
                if(end!=text&&(*end==0||*end==';')&&parsed>=0&&parsed<=100)saved=static_cast<int>(parsed);
            }
            preview=saved;
            previewEnabled=savedEnabled;
        }
    };
    Preferences& State() { static Preferences value;return value; }
}

int BaseNeural::DefaultStrengthPercent()
{
    float value=PortConfigFloat("BaseNeural","blend_strength",.35f);
    if(!std::isfinite(value))value=.35f;
    value=value<0?0:value>1?1:value;
    return static_cast<int>(std::lround(value*100));
}
int BaseNeural::StrengthPercent() { return State().preview; }
int BaseNeural::ConfiguredStrengthPercent() { return State().saved; }
void BaseNeural::PreviewStrength(int percent) { State().preview=ClampPercent(percent); }
void BaseNeural::CommitStrength(int percent) { State().saved=State().preview=ClampPercent(percent); }
bool BaseNeural::Enabled(){return State().previewEnabled;}
bool BaseNeural::ConfiguredEnabled(){return State().savedEnabled;}
void BaseNeural::PreviewEnabled(bool value){State().previewEnabled=value;}
void BaseNeural::CommitEnabled(bool value){State().savedEnabled=State().previewEnabled=value;}
void BaseNeural::CancelStrengthPreview() { State().preview=State().saved;State().previewEnabled=State().savedEnabled; }
void BaseNeural::WritePreferences(FILE* file)
{
    if(file)std::fprintf(file,"\n[BaseNeural]\nenabled = %d\nstrength_percent = %d\n",ConfiguredEnabled()?1:0,ConfiguredStrengthPercent());
}
