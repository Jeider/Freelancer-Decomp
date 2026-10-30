#include "graphics_policy.h"
#include "common_misc.h"
#include <windows.h>
#include <cstdlib>
#include <cstdio>
#include <mutex>

namespace
{
    struct Preferences
    {
        int Active[GraphicsSettings::Count];
        int Configured[GraphicsSettings::Count];
        Preferences()
        {
            char folder[MAX_PATH]={}, path[MAX_PATH]={};
            if (GetUserDataPath(folder))
                _snprintf_s(path,sizeof(path),_TRUNCATE,"%s\\PerfOptions.ini",folder);
            char port[MAX_PATH]={};
            GetModuleFileNameA(nullptr,port,MAX_PATH);
            if (char* slash=std::strrchr(port,'\\')) strcpy_s(slash+1,sizeof(port)-size_t(slash+1-port),"port.ini");
            for (int i=0;i<GraphicsSettings::Count;++i)
            {
                int value=GraphicsSettings::Default(i);
                // Migrate existing synchronization/filtering preferences on first run.
                if (i==GraphicsSettings::VSync) value=GetPrivateProfileIntA("Render","vsync",1,port)!=0;
                if (i==GraphicsSettings::Anisotropy) {
                    int af=int(GetPrivateProfileIntA("Render","anisotropy",16,port));
                    value=0;while (value<4 && (1<<(value+1))<=af) ++value;
                }
                if (i==GraphicsSettings::FpsLimit) {
                    int fps=int(GetPrivateProfileIntA("Render","fps_limit",144,port));
                    if (fps==0 || fps>180) value=GraphicsSettings::Maximum(i);
                    for(int index=1;index<=GraphicsSettings::Maximum(i);++index)
                        if (GraphicsSettings::Fps(index)==fps) value=index;
                }
                char text[64]={};
                if (path[0]) GetPrivateProfileStringA("Graphics",GraphicsSettings::Key(i),"",text,sizeof(text),path);
                char* end=nullptr;
                long const parsed=std::strtol(text,&end,10);
                while (end && (*end==' ' || *end=='\t')) ++end;
                if (end!=text && (*end==0 || *end==';') && parsed>=0 && parsed<=GraphicsSettings::Maximum(i)) value=int(parsed);
                // Keep old choice indices stable; unlimited/240/360 migrate to 180.
                if (i==GraphicsSettings::FpsLimit && end!=text && (*end==0 || *end==';') &&
                    (parsed==0 || parsed==9 || parsed==10)) value=GraphicsSettings::Maximum(GraphicsSettings::FpsLimit);
                Active[i]=Configured[i]=value;
            }
        }
    };
    Preferences& State() { static Preferences state; return state; }
    std::mutex ConfiguredMutex;
}

int __cdecl GraphicsSettings::Get(int setting, bool configured)
{
    if (setting<0 || setting>=Count) return 0;
    auto& state=State();
    if (!configured) return state.Active[setting];
    std::lock_guard<std::mutex> lock(ConfiguredMutex);
    return state.Configured[setting];
}
void __cdecl GraphicsSettings::Set(int setting, int value)
{
    if (setting==FpsLimit && (value==0 || value==9 || value==10)) value=Maximum(FpsLimit);
    if (setting<0 || setting>=Count || value<0 || value>Maximum(setting)) return;
    auto& state=State();
    std::lock_guard<std::mutex> lock(ConfiguredMutex);
    state.Configured[setting]=value;
}
bool __cdecl GraphicsSettings::RestartRequired()
{
    auto& state=State();
    std::lock_guard<std::mutex> lock(ConfiguredMutex);
    for (int i=0;i<Count;++i) if (state.Active[i]!=state.Configured[i]) return true;
    return false;
}
float __cdecl PortGraphicsRenderValue(char const* key, float authored)
{
    return key ? GraphicsSettings::RenderValue(State().Active,key,authored) : authored;
}
