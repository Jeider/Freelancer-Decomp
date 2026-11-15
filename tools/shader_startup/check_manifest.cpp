#include "RP9ShaderManifest.h"
#include <cassert>
int main() {
    std::vector<Rp9Startup::FJob> full,low,mixed;
    std::string error;
    const char* dir="DATA_EXTRA/SHADERS/";
    assert(Rp9Startup::Build(dir,full,error,3,3,3));
    assert(Rp9Startup::Build(dir,low,error,1,2,0));
    assert(Rp9Startup::Build(dir,mixed,error,1,2,3));
    assert(Rp9Startup::SurfaceQualityPrefix(3,3).empty());
    assert(full.size()==low.size());
    unsigned pixelCount=0;
    for(size_t i=0;i<full.size();++i) {
        auto const& a=full[i];auto const& b=low[i];
        bool surface=a.Name=="surface_material.hlsl" && !strcmp(a.Profile,"ps_3_0");
        assert(b.Text==(surface ? Rp9Startup::SurfaceQualityPrefix(1,2)+a.Text:a.Text));
        pixelCount+=surface;
        bool found=false;
        for(auto const& candidate:mixed)
            if(candidate.Text==a.Text && !strcmp(candidate.Entry,a.Entry) && !strcmp(candidate.Profile,a.Profile)) found=true;
        assert(found);
    }
    assert(mixed.size()==full.size()+pixelCount);
    puts("PASS: startup and runtime quality source keys agree; full cache retained; room/space variants included once");
}
