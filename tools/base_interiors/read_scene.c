#include "lua.h"
#include <stdio.h>
int ThornModernIsLuaTableTag(int t){return t==-3;}
int ThornModernNormalizeVarargCount(int n){return n<0?0:n;}
char* ThornModernGetArithmeticDiagnostic(void){return "unexpected type in arithmetic operation";}
static void string(char*s){unsigned char*c=(unsigned char*)s;putchar('"');if(c)for(;*c;c++){if(*c=='"'||*c=='\\')putchar('\\');if(*c<32)printf("\\u%04x",*c);else putchar(*c);}putchar('"');}
static void dump(lua_Object o,int depth){int i=0,comma=0;if(depth>15){printf("null");return;}if(lua_istable(o)){putchar('{');while(1){lua_beginblock();i=lua_next(o,i);if(!i){lua_endblock();break;}lua_Object key=lua_getresult(1),value=lua_getresult(2);if(comma++)putchar(',');string(lua_getstring(key));putchar(':');dump(value,depth+1);lua_endblock();}putchar('}');}else if(lua_isnumber(o))printf("%.10g",lua_getnumber(o));else if(lua_isstring(o))string(lua_getstring(o));else printf("null");}
int main(int argc,char**argv){int i;char* keys[]={"entities","events","duration"};if(argc!=2)return 2;lua_open();if(lua_dofile(argv[1]))return 3;putchar('{');for(i=0;i<3;i++){if(i)putchar(',');string(keys[i]);putchar(':');dump(lua_getglobal(keys[i]),0);}putchar('}');lua_close();return 0;}
