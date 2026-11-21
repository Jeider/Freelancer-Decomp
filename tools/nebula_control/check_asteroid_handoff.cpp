// Appended to the production server spawner compiled with engine fixtures.
#include "procedural_asteroid_replica.h"
#include <chrono>
#include <set>

void Step(StarSystem& system,std::vector<Vector> const& players,float dt){
    for(auto* obj:system.objects)if(!obj->destroyed){
        auto& b=obj->raw;auto& q=b.Orientation.q;float xyzw[4]={q.x,q.y,q.z,q.w};
        ProceduralAsteroids::Spin(xyzw,&b.spin.x,dt);q={xyzw[3],xyzw[0],xyzw[1],xyzw[2]};
        b.pos.x+=b.velocity.x*dt;b.pos.y+=b.velocity.y*dt;b.pos.z+=b.velocity.z*dt;
    }
    Proc::Update(system,players,dt);
}

int main(){
    LegacyMain();
    using namespace ProceduralAsteroids;
    auto start=std::chrono::steady_clock::now();
    std::map<Key,Rock> a,b;
    float eye[3]={30000,0,20000},next[3]={31000,0,20000};
    Around(eye,View,802,3,[&](Rock const& r){assert(a.emplace(r.key,r).second);});
    Around(next,View,802,3,[&](Rock const& r){b.emplace(r.key,r);});
    double recipeMs=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
    unsigned overlap=0;
    for(auto const& it:a){auto found=b.find(it.first);if(found!=b.end()){
        assert(!memcmp(it.second.position,found->second.position,12));
        assert(!memcmp(it.second.rotation,found->second.rotation,16));++overlap;}}
    assert(a.size()>5000&&a.size()<5900&&overlap>4000);
    for(auto const& item:a)for(auto const& other:a)if(item.first<other.first){
        double distance2=0;for(int k=0;k<3;++k){double d=item.second.position[k]-other.second.position[k];distance2+=d*d;}
        assert(distance2>=200.*200.);
    }
    assert(Cell(-.01f)==-1&&Cell(-1000)==-1&&Cell(-1000.1f)==-2);
    auto negative=Generate(Id(-30,-2,-20,5),802,3);assert(negative.position[0]<-29000&&negative.position[0]>=-30000);
    printf("PASS recipe: %zu rocks in 6 km, %u unchanged across 1 km travel; generation %.3f ms\n",a.size(),overlap,
           recipeMs);

    auto& zone=Universe::zone;zone.system=CreateID("om15");zone.id=CreateID("Zone_om15_ast1_asteroids");zone.radius=50000;
    Universe::excluded.pos={1000,0,0};Universe::excluded.radius=400;
    StarSystem system;system.SystemInfo->id=zone.system;Archetype::arch.loaded=true;
    Field recipe;recipe.archetype=CreateID("rock");recipe.seed=801;recipe.count=60;recipe.fromPlayer=true;
    CmnAsteroid::LootableZoneEntry loot;loot.DynamicLootContainerId.Id=11;loot.DynamicLootCommodityId.Id=12;zone.loot=&loot;
    assert(Proc::Load(system,zone,{recipe,recipe,recipe},{&Universe::excluded},{&zone}));
    assert(!Populations.count(&system)); // no legacy random stream in the opted-in field
    auto& f=Proc::Worlds.at(zone.system);
    std::vector<Vector> players{{0,0,0},{0,0,0}};
    PhySys::blocked=true;Step(system,players,.1f);assert(f.states.empty());PhySys::blocked=false;
    Step(system,players,.1f);assert(f.states.size()==32);
    for(int n=0;n<35;++n)Step(system,players,.1f);
    size_t initial=f.states.size();assert(initial>160&&initial<240);
    std::set<unsigned> ids;
    for(auto const& item:f.states){auto const& state=item.second;
        assert(ids.insert(state.body.id).second);assert(length(state.body.pos)<=Activate);
        assert(!Universe::excluded.InZone(state.body.pos,50));
        auto rock=Generate(item.first,f.seed,3);
        assert(!memcmp(rock.position,&state.body.pos.x,12));
        ProceduralAsteroids::Spin(rock.rotation,state.stamp);
        auto const& q=state.body.orientation;
        assert(std::fabs(rock.rotation[0]*q.x+rock.rotation[1]*q.y+rock.rotation[2]*q.z+rock.rotation[3]*q.w)>.99999f);}
    auto* cachedCandidates=f.candidates.data();unsigned lookups=objectLookups;
    auto oldRevision=f.revision;start=std::chrono::steady_clock::now();
    for(int n=0;n<300;++n)Step(system,players,.1f);
    double populationMs=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count()/300;
    assert(objectLookups==lookups&&cachedCandidates==f.candidates.data());
    assert(f.revision-oldRevision<=16); // only two-second clocks, no pose flood for uniform spin
    printf("PASS server steady state: %zu rotating bodies %.4f ms/tick; zero object lookups or candidate rebuilds\n",initial,populationMs);
    Step(system,{{10000,0,0},{0,0,0}},.1f);
    for(auto const& item:f.states)if(length(item.second.body.pos)<=Activate)assert(item.second.body.id); // other player retains
    auto key=f.states.begin()->first;auto& damaged=f.states.at(key);
    auto* body=Server_LookupGameObject(damaged.body.id);body->raw.hp=1234;body->raw.pos.x+=17;
    // Collision impulse must still translate the rock and preserve arbitrary spin.
    body->raw.velocity={10,0,0};body->raw.spin={.1f,.2f,.3f};float px=body->raw.pos.x;
    Step(system,players,.1f);assert(std::fabs(body->raw.pos.x-px-1)<.001f);
    body->raw.velocity={}; // Keep the original pose-retention assertions exact below.
    Vector retained=body->raw.pos;auto deadKey=std::next(f.states.begin())->first;auto deadId=f.states.at(deadKey).body.id;
    auto deadPos=f.states.at(deadKey).body.pos;
    OnServerAsteroidKilled(system,deadId,deadPos);assert(f.states.at(deadKey).body.dead&&system.drops.size()==1);
    OnServerAsteroidKilled(system,deadId,deadPos);assert(system.drops.size()==1);
    Server_LookupGameObject(deadId)->destroy(1,0);
    Step(system,{},.1f);assert(damaged.body.id==0&&!damaged.body.dead&&damaged.body.hitPoints==1234);
    assert(!memcmp(&retained,&damaged.body.pos,sizeof(Vector)));
    Proc::Unload(system);system.clear();
    assert(f.owner==nullptr&&f.states.at(deadKey).body.dead);
    assert(Proc::Load(system,zone,{recipe,recipe,recipe},{&Universe::excluded},{&zone}));
    for(int n=0;n<35;++n)Step(system,players,.1f);
    assert(f.states.at(deadKey).body.dead&&!f.states.at(deadKey).body.id);
    assert(damaged.body.id&&Server_LookupGameObject(damaged.body.id)->raw.hp==1234);
    assert(Server_LookupGameObject(damaged.body.id)->raw.spin.x==.1f);
    assert(!memcmp(&retained,&damaged.body.pos,sizeof(Vector)));
    printf("PASS lifecycle: %zu near bodies; shared players, exclusions, bounded spawn, HP/pose restored across unload, one loot roll, death retained\n",initial);

    // Exercise actual server snapshot sender and client transaction decoder.
    Players[1].system_id=zone.system;sent.clear();Packet request;request.header.kind=Request;
    request.header.system=zone.system;request.header.zone=zone.id;request.header.token=7;
    ServerProceduralAsteroidRequest(1,Bytes(request),&request);assert(sent.size()>2);
    Replica replica;replica.token=7;
    for(auto const& wire:sent){Packet p;assert(Decode(wire.data(),unsigned(wire.size()),p));replica.Accept(p);}
    assert(replica.ready&&replica.entries.size()==f.states.size()&&(replica.entries.at(deadKey).flags&Dead));
    auto before=replica.entries.size();auto p=Proc::Packet(f,Begin,7);replica.Accept(p);
    p=Proc::Packet(f,Records,7);p.header.count=1;p.entries[0]=Proc::Entry(key,damaged);replica.Accept(p);
    assert(replica.entries.size()==before);p=Proc::Packet(f,End,7);p.header.epoch++;replica.Accept(p);
    assert(replica.entries.size()==before&&replica.refresh);
    sent.clear();f.subscribers.clear();request.header.token=8;ServerProceduralAsteroidRequest(1,Bytes(request),&request);
    replica.token=8;for(auto const& wire:sent){Packet decoded;assert(Decode(wire.data(),unsigned(wire.size()),decoded));replica.Accept(decoded);}
    sent.clear();OnServerAsteroidKilled(system,damaged.body.id,damaged.body.pos);
    for(auto const& wire:sent){Packet decoded;assert(Decode(wire.data(),unsigned(wire.size()),decoded));replica.Accept(decoded);}
    assert(replica.entries.at(key).flags&Dead);
    p=Proc::Packet(f,Delta,8);p.header.revision+=2;replica.Accept(p);assert(replica.refresh);
    Packet bad=Proc::Packet(f,Delta,8),decoded;bad.header.count=1;bad.entries[0]=Proc::Entry(key,damaged);
    assert(Decode(&bad,Bytes(bad),decoded));bad.entries[0].rotation[0]=NAN;assert(!Decode(&bad,Bytes(bad),decoded));
    bad=Proc::Packet(f,Delta,8);bad.header.count=17;assert(!Decode(&bad,sizeof(bad),decoded));
    assert(!Decode(&request,Bytes(request)-1,decoded));
    sent.clear();request.header.system=123;ServerProceduralAsteroidRequest(1,Bytes(request),&request);assert(sent.empty());
    printf("PASS protocol: authenticated system, bounded packets, snapshot commit, stale epoch/token and gap rejection, authoritative destruction\n");

    // No respawn decisions on the client. Cap exhausted leaves the seed proxies intact.
    std::vector<Vector> crowd;
    for(int x=-1;x<=1;++x)for(int y=-1;y<=1;++y)crowd.push_back({x*9000.f,y*9000.f,0});
    crowd.push_back({0,0,9000});crowd.push_back({0,0,-9000});crowd.push_back({9000,9000,9000});
    for(int n=0;n<110;++n)Step(system,crowd,.1f);
    int count=0;for(auto const& item:f.states)if(item.second.body.id)++count;
    assert(count==Proc::Limit);
    auto oldEpoch=f.epoch;ResetServerProceduralAsteroids();assert(f.states.empty()&&f.epoch!=oldEpoch&&f.owner==&system);
    Step(system,players,.1f);assert(f.states.size()==32);
    Proc::Unload(system);Proc::Worlds.clear();system.clear();
    puts("PASS budget: 2048 maximum physical bodies; save/world reset keeps loaded recipe and removes old state");

    // Parse real-shaped system/cloud INI definitions; switch radii without any
    // camera travel so the cached candidates cannot hide a boundary bug.
    files["system"]={{"Nebula",{{"file","cloud"},{"zone","nebula"}}},
                     {"Nebula",{{"file","missing"},{"zone","nebula"}}}};
    files["cloud"]={{"Exclusion Zones",{{"exclusion","clearing"}}}};
    Universe::nebula.radius=5000;Universe::nebula.pos={};
    Universe::clearing.radius=300;Universe::clearing.pos={10000,0,0};
    assert(Proc::Load(system,zone,{recipe,recipe,recipe},{&Universe::excluded},{&zone}));
    auto& fog=Proc::Worlds.at(zone.system);assert(fog.nebulae.size()==1);
    assert(Proc::ActivationRadius(fog,{0,0,0})==1000&&Proc::ActivationRadius(fog,{7000,0,0})==2000);
    auto activeCount=[&](){unsigned n=0;for(auto const& item:fog.states)if(item.second.body.id)++n;return n;};
    for(int n=0;n<12;++n)Step(system,{{0,0,0}},.1f);
    unsigned fogCount=activeCount();assert(fogCount>=15&&fogCount<=40);
    for(auto const& item:fog.states)if(item.second.body.id)assert(length(item.second.body.pos)<=1000);
    // A clear pocket restores the larger bubble even though the player did not move.
    Universe::clearing.pos={};assert(Proc::ActivationRadius(fog,{0,0,0})==2000);
    for(int n=0;n<12;++n)Step(system,{{0,0,0}},.1f);
    unsigned clearCount=activeCount();assert(clearCount==initial);
    Universe::clearing.pos={10000,0,0};Step(system,{{0,0,0}},.1f);
    unsigned kept=activeCount();assert(kept<clearCount&&kept>=fogCount);
    for(auto const& item:fog.states)if(item.second.body.id)assert(length(item.second.body.pos)<=1200.01f);
    // Mixed players: an outside observer keeps their own 2 km sphere.
    assert(Proc::NearPlayers({6800,0,0},{{0,0,0},{8500,0,0}},{1000,2000}));
    assert(!Proc::NearPlayers({1300,0,0},{{0,0,0},{8500,0,0}},{1000,2000},true));
    assert(Proc::NearPlayers({1100,0,0},{{0,0,0}},{1000},true));
    printf("PASS adaptive physics: clear %u bodies at 2 km, nebula %u at 1 km; %u retained within 1.2 km after shrink; exclusions/multiple players\n",clearCount,fogCount,kept);
    Proc::Unload(system);Proc::Worlds.clear();system.clear();
    decorationsOnly=1;
    assert(Proc::Load(system,zone,{recipe,recipe,recipe},{&Universe::excluded},{&zone}));
    auto& decor=Proc::Worlds.at(zone.system);auto allocated=CFLIDMaker::GetInstance()->next;auto priorLookups=objectLookups;
    for(int n=0;n<200;++n)Step(system,{{n*100.f,0,0},{0,n*100.f,0}},.1f);
    assert(decor.decorationsOnly&&decor.states.empty()&&decor.candidates.empty()&&system.objects.empty());
    assert(CFLIDMaker::GetInstance()->next==allocated&&objectLookups==priorLookups&&decor.clock>19);
    sent.clear();request.header.system=zone.system;request.header.token=77;
    ServerProceduralAsteroidRequest(1,Bytes(request),&request);assert(sent.size()==2);
    Replica empty;empty.token=77;
    for(auto const& bytes:sent){Packet wire;assert(Decode(bytes.data(),unsigned(bytes.size()),wire));empty.Accept(wire);}
    assert(empty.ready&&empty.entries.empty()&&empty.recipe.models==3&&empty.recipe.clock>19);
    puts("PASS decorations-only: zero physical bodies/IDs/lookups/candidates; valid empty snapshot supplies mesh recipe and advancing spin clock");
    Proc::Unload(system);Proc::Worlds.clear();system.clear();decorationsOnly=0;
    return 0;
}
