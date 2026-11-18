#include "lua.h"
#include <stdio.h>
#define lua_getindexed(o,n) (lua_pushobject(o),lua_pushnumber(n),lua_gettable())
#define lua_getfield(o,f) (lua_pushobject(o),lua_pushstring(f),lua_gettable())
/* Standalone equivalents of ThornModernAdapters' three Lua hooks. */
int ThornModernIsLuaTableTag(int t){return t==-3;}
int ThornModernNormalizeVarargCount(int n){return n<0?0:n;}
char* ThornModernGetArithmeticDiagnostic(void){return "unexpected type in arithmetic operation";}
static lua_Object field(lua_Object o,char *key){return lua_getfield(o,key);}
static void vector(lua_Object o){int j;if(!lua_istable(o)){printf("null");return;}printf("[");for(j=1;j<=3;j++){if(j>1)printf(",");printf("%g",lua_getnumber(lua_getindexed(o,j)));}printf("]");}
int main(int argc,char**argv){int i;lua_Object entities;if(argc!=2)return 2;lua_open();if(lua_dofile(argv[1]))return 3;entities=lua_getglobal("entities");if(!lua_istable(entities))return 4;
 for(i=1;i<300;i++){lua_Object e,props;lua_beginblock();e=lua_getindexed(entities,i);if(!lua_istable(e)){lua_endblock();break;}props=field(e,"lightprops");if(lua_istable(props)){char* keys[]={"ambient","diffuse","specular","atten"};int k;printf("%s",lua_getstring(field(e,"entity_name")));for(k=0;k<4;k++){printf(" %s=",keys[k]);vector(field(props,keys[k]));}printf(" range=%g\n",lua_getnumber(field(props,"range")));}lua_endblock();}lua_close();return 0;}
