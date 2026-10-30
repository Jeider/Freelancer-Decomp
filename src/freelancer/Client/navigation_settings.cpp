#include "navigation_settings.h"
#include "port_config.h"
#include "common_misc.h"
#include "dacom.h"
#include <windows.h>
#include <cstring>

namespace NavigationSettings {
namespace {
char const* const keys[Count]={"route_generator","autopilot","auto_dock"};
char path[MAX_PATH]={};
int values[Count]={-1,-1,-1};
bool loaded=false;
void load() {
    if(loaded) return;
    loaded=true;
    if(!GetUserDataPath(path)) {path[0]=0;return;}
    strcat_s(path,"\\navigation.ini");
    for(int i=0;i<Count;++i) {
        char text[32]={};
        GetPrivateProfileStringA("Navigation",keys[i],"",text,sizeof(text),path);
        if(i==Generator) {
            if(_stricmp(text,"beta")==0) values[i]=1;
            else if(_stricmp(text,"retail")==0) values[i]=0;
        } else if(std::strcmp(text,"0")==0 || std::strcmp(text,"1")==0) values[i]=text[0]-'0';
    }
}
}
int Default(Setting setting) {
    if(setting==Generator) {
        char text[32]; PortConfigString("Navigation",keys[setting],"beta",text,sizeof(text));
        return _stricmp(text,"retail")!=0;
    }
    return PortConfigInt("Navigation",keys[setting],1)!=0;
}
int Get(Setting setting) {
    load();
    return values[setting]<0 ? Default(setting) : values[setting];
}
bool Set(Setting setting,int value) {
    load(); value=value!=0;
    char const* text=setting==Generator ? (value?"beta":"retail") : (value?"1":"0");
    if(!path[0] || !WritePrivateProfileStringA("Navigation",keys[setting],text,path)) {
        FDUMP(0x100001,"Navigation: could not save preferences (%lu)\n",GetLastError());
        return false;
    }
    values[setting]=value;
    return true;
}
}
