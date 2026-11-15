// Offline preparation uses the exact same manifest, flags and verified disk cache as game startup.
#include "RP9ShaderStartup.h"
#include <cstdio>
int main(int argc,char** argv) {
    const std::string Directory=argc>1?argv[1]:"DATA_EXTRA/SHADERS/";
    std::vector<Rp9Startup::FJob> Jobs;std::string Error;
    if(!Rp9Startup::Build(Directory,Jobs,Error)) {puts(Error.c_str());return 1;}
    std::vector<Rp9Startup::Result> Results;
    unsigned Last=~0u;
    if(!Rp9Startup::Prepare(Jobs,Directory,Results,[&](unsigned Done,unsigned Total) {
        if(Done!=Last) {printf("Caching shaders: %u/%u\n",Done,Total);fflush(stdout);Last=Done;}return true;
    })) return 1;
    bool Ok=true;
    for(size_t I=0;I<Jobs.size();++I) {
        const auto& R=Results[I]; const auto& J=Jobs[I];
        printf("%s %s %s: %s\n",J.Name.c_str(),J.Entry,J.Profile,
            FAILED(R.Hr)?"FAILED":R.Hit?"HIT":"stored and verified");
        if(FAILED(R.Hr)) {puts(R.Message.c_str());Ok=false;}
    }
    return Ok?0:1;
}
