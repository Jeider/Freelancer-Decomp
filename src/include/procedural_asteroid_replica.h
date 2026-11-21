#pragma once
#include "procedural_asteroids.h"
#include <map>

namespace ProceduralAsteroids {
// A snapshot is transactional: interrupted/malformed streams never replace the
// last complete view. All later changes are ordered within that server epoch.
struct Replica {
    Header recipe{},pending{};
    std::map<Key,Entry> entries,staging;
    unsigned token=0;
    bool ready=false,receiving=false,refresh=false;
    static bool SameRecipe(Header const& a,Header const& b) {
        return a.system==b.system&&a.zone==b.zone&&a.epoch==b.epoch&&a.seed==b.seed&&a.models==b.models&&
               !std::memcmp(a.archetypes,b.archetypes,sizeof(a.archetypes));
    }
    bool Accept(Packet const& p) {
        auto const& h=p.header;
        if(h.token!=token)return false;
        if(h.kind==Begin){pending=h;staging.clear();receiving=true;return false;}
        if(h.kind==Records||h.kind==End){
            if(!receiving||!SameRecipe(h,pending)||h.revision!=pending.revision){receiving=false;refresh=true;return false;}
            if(h.kind==Records){
                if(staging.size()+h.count>500000){receiving=false;refresh=true;return false;}
                for(unsigned i=0;i<h.count;++i)
                    if(!staging.emplace(p.entries[i].key,p.entries[i]).second){receiving=false;refresh=true;return false;}
                return false;
            }
            entries.swap(staging);staging.clear();recipe=h;ready=true;receiving=false;refresh=false;return true;
        }
        if(h.kind==Delta){
            if(!ready||receiving||!SameRecipe(h,recipe)||h.revision!=recipe.revision+1){refresh=true;return false;}
            for(unsigned i=0;i<h.count;++i)entries[p.entries[i].key]=p.entries[i];
            recipe.revision=h.revision;recipe.clock=h.clock;return true;
        }
        return false;
    }
};
}
