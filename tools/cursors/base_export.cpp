#include "base_icon_art.h"
#include <fstream>
#include <string>
#include <cstdio>
int main(int argc,char** argv) {
    if(argc!=2)return 1;
    for(auto const& icon:BaseIconArt::Shapes())for(int size:{32,64,128,256,512}) {
        auto pixels=CursorVectorArt::Rasterize(icon,size);
        std::ofstream f(std::string(argv[1])+"/"+icon.name+"_"+std::to_string(size)+".bgra",std::ios::binary);
        f.write(reinterpret_cast<char const*>(pixels.data()),pixels.size()*4);
        if(!f)return 2;
    }
    std::puts("PASS: seven BASESIDE vector sources rasterized at five sizes");
}
