#pragma once

#include <cerrno>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <initializer_list>

namespace PortConsoleParse {
inline bool Money(char const* text,int& mode,int& amount) {
    mode=0;amount=0;
    if(!*text)return true;
    mode=(*text=='+' || *text=='-')?2:1;
    errno=0;char* end=nullptr;
    long long value=std::strtoll(text,&end,10);
    if(end==text || errno==ERANGE)return false;
    const bool thousands=*end=='k' || *end=='K';
    if(thousands)++end;
    while(*end==' ')++end;
    if(*end || value<-999999999LL || value>999999999LL)return false;
    if(thousands)value*=1000;
    if(value<-999999999LL || value>999999999LL)return false;
    amount=static_cast<int>(value);return true;
}
inline bool Rep(char const* text,float& value) {
    struct Named {char const* name;float value;};
    for(auto const& named:{Named{"H",-.9f},Named{"h",-.6f},Named{"nh",-.2f},
                          Named{"n",0.f},Named{"nf",.2f},Named{"f",.6f},Named{"F",.9f}})
        if(std::strcmp(text,named.name)==0){value=named.value;return true;}
    errno=0;char* end=nullptr;
    double number=std::strtod(text,&end);
    if(end==text || errno==ERANGE || !std::isfinite(number))return false;
    while(*end==' ')++end;
    if(*end)return false;
    if(number<-1 || number>1)number/=100;
    value=static_cast<float>(number<-1?-1:number>1?1:number);
    return true;
}
}
