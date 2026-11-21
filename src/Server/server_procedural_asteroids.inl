// Included after the legacy population helpers. Cache contains only visited rocks.
namespace Proc {
namespace P = ProceduralAsteroids;
struct State {
    RockState body;unsigned model=0;float stamp=0;
    std::shared_ptr<BaseWatcher> watch;
    P::Entry published;
};
GameObject* Body(State const& state){
    auto* target=state.watch?state.watch->target():nullptr;
    return target?static_cast<GameObject*>(static_cast<IObjRW*>(const_cast<Watchable*>(target))):nullptr;
}
struct Subscriber {unsigned token=0; DWORD last=0;};
struct NebulaRegion {
    Universe::IZone const* zone=nullptr;
    std::vector<Universe::IZone const*> exclusions;
};
struct FieldCache {
    StarSystem* owner=nullptr;
    Universe::IZone const* zone=nullptr;
    unsigned system=0,zoneId=0,seed=0,epoch=0,revision=0;
    float elapsed=0;
    bool decorationsOnly=false;
    double clock=0,lastClock=0;
    std::vector<Vector> anchors;
    std::vector<P::Rock> candidates;
    std::vector<PlayerField> models;
    std::vector<NebulaRegion> nebulae;
    std::map<P::Key,State> states;
    std::map<unsigned,Subscriber> subscribers;
};
std::map<unsigned,FieldCache> Worlds;
unsigned Epoch=1;
constexpr int Limit=2048, SpawnBatch=32;
constexpr float NebulaActivate=1000.f;

void LoadNebulae(FieldCache& f,char const* systemFile) {
    f.nebulae.clear();char path[1024];Universe::get_filename(path,systemFile);
    INI_Reader reader;if(!reader.open(path,false))return;
    while(reader.read_header()){
        if(!reader.is_header("Nebula"))continue;
        std::string file,name;
        while(reader.read_value()){
            if(reader.is_value("file"))file=reader.get_value_string();
            else if(reader.is_value("zone"))name=reader.get_value_string();
        }
        if(file.empty()||name.empty())continue;
        NebulaRegion n;n.zone=Universe::get_zone(f.system,name.c_str());if(!n.zone)continue;
        GetFileSysPath(path,file.c_str(),DALib::Data);INI_Reader cloud;
        // A missing cloud file must not silently shrink the physical bubble.
        if(!cloud.open(path,false))continue;
        while(cloud.read_header())if(cloud.is_header("Exclusion Zones"))while(cloud.read_value()){
            if(!cloud.is_value("exclusion"))continue;
            auto* zone=Universe::get_zone(f.system,cloud.get_value_string());if(zone)n.exclusions.push_back(zone);
        }
        f.nebulae.push_back(std::move(n));
    }
}
float ActivationRadius(FieldCache const& f,Vector const& player) {
    float immersion=0;
    for(auto const& n:f.nebulae){
        float inside=float(n.zone->GetImmersion(player));if(inside<=0)continue;
        for(auto* hole:n.exclusions)inside=(std::min)(inside,1.f-float(hole->GetImmersion(player)));
        immersion=(std::max)(immersion,inside);
    }
    immersion=(std::max)(0.f,(std::min)(1.f,immersion));
    return P::Activate+(NebulaActivate-P::Activate)*immersion;
}
bool NearPlayers(Vector const& pos,std::vector<Vector> const& players,std::vector<float> const& radii,bool suspend=false){
    for(size_t i=0;i<players.size();++i){float radius=radii[i]*(suspend?P::Suspend/P::Activate:1.f);
        if(DistanceSquared(pos,players[i])<=radius*radius)return true;}
    return false;
}

P::Entry Entry(P::Key key,State const& state) {
    P::Entry e;e.key=key;e.object=state.body.id;
    e.flags=state.body.dead?P::Dead:(e.object?P::Active:0);
    std::memcpy(e.position,&state.body.pos.x,sizeof(e.position));
    auto const& q=state.body.orientation;
    e.rotation[0]=q.x;e.rotation[1]=q.y;e.rotation[2]=q.z;e.rotation[3]=q.w;
    e.stamp=state.stamp;std::memcpy(e.spin,&state.body.spin.x,12);
    return e;
}
P::Packet Packet(FieldCache const& f,unsigned kind,unsigned token) {
    P::Packet p;auto& h=p.header;
    h.kind=kind;h.system=f.system;h.zone=f.zoneId;h.seed=f.seed;h.models=unsigned(f.models.size());
    h.epoch=f.epoch;h.revision=f.revision;h.token=token;
    h.clock=float(f.clock);
    for(unsigned i=0;i<h.models;++i)h.archetypes[i]=f.models[i].settings.archetype;
    return p;
}
void Send(unsigned player,P::Packet const& p) {
    if(g_pChatClientInterface)g_pChatClientInterface->SendCommonChatMsg(CHAT_ID(player),CHAT_ID(P::Channel),P::Bytes(p),&p);
}
void Publish(FieldCache& f,std::vector<P::Entry> const& changes) {
    if(changes.empty()){
        if(f.clock-f.lastClock<2)return;f.lastClock=f.clock;++f.revision;
        for(auto const& sub:f.subscribers)if(Players.is_valid(sub.first)&&Players[sub.first].system_id==f.system)
            Send(sub.first,Packet(f,P::Delta,sub.second.token));
        return;
    }
    // One revision per bounded packet, identical for all subscribers.
    for(size_t start=0;start<changes.size();start+=P::Chunk){
        ++f.revision;
        for(auto it=f.subscribers.begin();it!=f.subscribers.end();){
            unsigned id=it->first;
            if(!Players.is_valid(id)||Players[id].system_id!=f.system){it=f.subscribers.erase(it);continue;}
            auto p=Packet(f,P::Delta,it->second.token);
            p.header.count=unsigned((std::min)(size_t(P::Chunk),changes.size()-start));
            std::copy_n(changes.begin()+start,p.header.count,p.entries);Send(id,p);++it;
        }
    }
}
void Request(unsigned player,unsigned size,void const* bytes) {
    P::Packet request;
    if(!g_pChatClientInterface||!Players.is_valid(player)||!P::Decode(bytes,size,request)||request.header.kind!=P::Request)return;
    auto found=Worlds.find(Players[player].system_id);
    if(found==Worlds.end())return;
    auto& f=found->second;auto const& h=request.header;
    if(!f.owner||h.system!=f.system||h.zone!=f.zoneId||f.models.empty())return;
    auto& sub=f.subscribers[player];DWORD now=GetTickCount();
    if(sub.token&&now-sub.last<1000)return;
    sub={h.token,now};
    Send(player,Packet(f,P::Begin,sub.token));
    auto p=Packet(f,P::Records,sub.token);
    for(auto const& item:f.states){
        p.entries[p.header.count++]=Entry(item.first,item.second);
        if(p.header.count==P::Chunk){Send(player,p);p.header.count=0;}
    }
    if(p.header.count)Send(player,p);
    Send(player,Packet(f,P::End,sub.token));
}
bool Load(StarSystem& system,Universe::IZone const& zone,std::vector<Field> const& recipes,
          std::vector<Universe::IZone const*> const& exclusions,std::vector<Universe::IZone const*> const& loot) {
    // Explicit opt-in for this prototype; there is no dependency on a nebula.
    if(zone.GetSystem()!=CreateID("om15")||zone.GetId()!=CreateID("Zone_om15_ast1_asteroids"))return false;
    if(recipes.empty()||recipes.size()>P::MaxModels)return false;
    std::vector<PlayerField> models;
    for(auto const& recipe:recipes){
        auto* arch=Archetype::GetSolar(recipe.archetype);
        if(!arch||!IsServerAsteroidType(arch->ObjectType))return false;
        arch->load();
        if(!arch->is_loaded()){arch->Release();return false;}
        PlayerField model;model.settings=recipe;model.settings.speed=model.settings.spin=0;
        model.loadedArch={arch,[](Archetype::Solar* a){a->Release();}};
        model.modelRadius=ModelRadius(arch);model.zone=&zone;model.exclusions=exclusions;model.lootZones=loot;
        model.rng.seed(recipe.seed^zone.GetId());models.push_back(std::move(model));
    }
    auto& f=Worlds[zone.GetSystem()];
    f.owner=&system;f.zone=&zone;f.system=zone.GetSystem();f.zoneId=zone.GetId();
    f.seed=recipes.front().seed^zone.GetId();if(!f.epoch)f.epoch=++Epoch;
    f.models=std::move(models);f.subscribers.clear();f.anchors.clear();f.candidates.clear();
    f.decorationsOnly=PortConfigInt("Render","procedural_asteroid_decor_only",0)!=0;
    LoadNebulae(f,system.SystemInfo->GetFile());
    FDUMP(0x100004,"ProceduralAsteroids: system %u zone %u, %u models, 6/km3, physics clear 2000/2400m nebula 1000/1200m, retained %u records",
          f.system,f.zoneId,unsigned(f.models.size()),unsigned(f.states.size()));
    if(f.decorationsOnly)FDUMP(0x100004,"ProceduralAsteroids: decorations-only diagnostic, no physical bodies");
    return true;
}
State Make(P::Rock const& r) {
    State s;s.model=r.model;s.body.pos=Vector{r.position[0],r.position[1],r.position[2]};
    s.body.orientation=Quaternion{r.rotation[3],r.rotation[0],r.rotation[1],r.rotation[2]};
    s.body.spin=Vector{0,P::SpinRate,0};return s;
}
void Advance(State& s,float clock){
    float q[4]={s.body.orientation.x,s.body.orientation.y,s.body.orientation.z,s.body.orientation.w};
    P::Spin(q,&s.body.spin.x,clock-s.stamp);s.body.orientation=Quaternion{q[3],q[0],q[1],q[2]};s.stamp=clock;
}
bool Changed(P::Entry const& a,P::Entry const& b){
    if(a.flags!=b.flags||a.object!=b.object)return true;
    float d=0;for(int k=0;k<3;++k){float v=a.position[k]-b.position[k];d+=v*v;}
    if(d>.0025f)return true;
    float q[4];std::memcpy(q,a.rotation,16);P::Spin(q,a.spin,b.stamp-a.stamp);
    float dot=0;for(int k=0;k<4;++k)dot+=q[k]*b.rotation[k];
    return std::fabs(dot)<.99999f;
}
bool InField(FieldCache const& f,State const& s) {
    if(f.zone->GetImmersion(s.body.pos)<=0.001)return false;
    auto const& model=f.models[s.model];
    for(auto* exclusion:model.exclusions)if(exclusion->InZone(s.body.pos,model.modelRadius))return false;
    return true;
}
void Update(StarSystem& system,std::vector<Vector> const& players,float dt) {
    auto found=Worlds.find(system.SystemInfo->GetId());
    if(found==Worlds.end()||found->second.owner!=&system||!std::isfinite(dt)||dt<=0)return;
    auto& f=found->second;f.clock+=dt;f.elapsed+=dt;if(f.elapsed<.1f)return;f.elapsed=0;
    // Keep the recipe and spin clock available to the visual field while the
    // requested diagnostic completely skips physical population work.
    if(f.decorationsOnly){Publish(f,{});return;}
    std::vector<float> radii;for(auto const& player:players)radii.push_back(ActivationRadius(f,player));
    std::vector<P::Entry> changes;int active=0;
    for(auto& item:f.states){auto& s=item.second;
        if(!s.body.id)continue;
        auto* obj=Body(s);
        if(!obj||obj->is_destroyed()) {s.body.id=0;s.body.dead=true;}
        else {
            Capture(s.body,obj);
            s.stamp=float(f.clock);
            if(!NearPlayers(s.body.pos,players,radii,true)&&obj->destroy(0,0))s.body.id=0;
            else ++active;
        }
        auto after=Entry(item.first,s);
        if(Changed(s.published,after)){changes.push_back(after);s.published=after;}
    }
    // Union of player bubbles, nearest first. A second player cannot duplicate a key.
    bool moved=f.anchors.size()!=players.size();
    if(!moved)for(size_t i=0;i<players.size();++i)if(DistanceSquared(players[i],f.anchors[i])>10000){moved=true;break;}
    if(moved){
        f.anchors=players;f.candidates.clear();std::map<P::Key,P::Rock> unique;
        for(auto const& player:players)if(f.zone->InZone(player,P::Activate+100))
            P::Around(&player.x,P::Activate+101,f.seed,unsigned(f.models.size()),[&](P::Rock const& r){unique.emplace(r.key,r);});
        for(auto const& item:unique)f.candidates.push_back(item.second);
    }
    std::map<P::Key,State> candidates;
    for(auto const& r:f.candidates)if(f.states.find(r.key)==f.states.end()){
        auto s=Make(r);if(NearPlayers(s.body.pos,players,radii)&&InField(f,s))candidates.emplace(r.key,std::move(s));
    }
    for(auto const& item:f.states)
        if(!item.second.body.id&&!item.second.body.dead&&NearPlayers(item.second.body.pos,players,radii)&&InField(f,item.second))
            candidates.emplace(item);
    std::vector<std::pair<float,P::Key>> order;
    for(auto const& item:candidates){float distance=1e30f;
        for(auto const& p:players)distance=(std::min)(distance,DistanceSquared(p,item.second.body.pos));
        order.emplace_back(distance,item.first);
    }
    std::sort(order.begin(),order.end());int budget=(std::min)(SpawnBatch,Limit-active);
    for(auto const& next:order){
        if(budget<=0)break;
        State s=candidates.at(next.second);auto& model=f.models[s.model];
        if(!ValidPlacement(*f.zone,model.exclusions,s.body.pos,model.modelRadius))continue;
        Advance(s,float(f.clock));
        if(!CreateRock(system,model.loadedArch.get(),model.settings,s.body))continue;
        s.watch=std::make_shared<BaseWatcher>();s.watch->set(Server_LookupGameObject(s.body.id));
        s.published=Entry(next.second,s);changes.push_back(s.published);f.states[next.second]=std::move(s);--budget;
    }
    Publish(f,changes);
}
bool Killed(StarSystem& system,unsigned id,Vector const& position) {
    auto found=Worlds.find(system.SystemInfo->GetId());if(found==Worlds.end())return false;
    auto& f=found->second;
    for(auto& item:f.states){auto& state=item.second;
        if(state.body.id!=id||state.body.dead)continue;
        state.body.id=0;state.body.dead=true;state.body.pos=position;state.watch.reset();
        Publish(f,{Entry(item.first,state)});
        auto& model=f.models[state.model];
        for(auto* zone:model.lootZones){
            if(!zone->InZone(position,0))continue;
            auto* loot=zone->GetLootableInfo();if(!loot||!loot->DynamicLootCommodityId.Id)continue;
            unsigned difficulty=unsigned((std::max)(1,(std::min)(100,loot->DynamicLootDifficulty)));
            if(std::uniform_int_distribution<unsigned>(1,difficulty)(model.rng)!=1)return true;
            int maximum=(std::max)(1,loot->DynamicLootCountMax),minimum=(std::max)(1,(std::min)(maximum,loot->DynamicLootCountMin));
            system.spawn_mined_loot(position,loot->DynamicLootContainerId.Id,loot->DynamicLootCommodityId.Id,
                                   std::uniform_int_distribution<int>(minimum,maximum)(model.rng));return true;
        }
        return true;
    }
    return false;
}
void Unload(StarSystem& system) {
    auto found=Worlds.find(system.SystemInfo->GetId());if(found==Worlds.end()||found->second.owner!=&system)return;
    auto& f=found->second;
    for(auto& item:f.states){auto& state=item.second;
        if(state.body.id){auto* obj=Body(state);if(obj&&!obj->is_destroyed()){Capture(state.body,obj);state.stamp=float(f.clock);}
            state.body.id=0;state.watch.reset();}
    }
    f.models.clear();f.subscribers.clear();f.owner=nullptr;f.zone=nullptr;
}
}
