#include "../../src/freelancer/Client/route_geometry.h"
#include <cassert>
#include <cstdio>
using namespace RouteGeometry;
using FlightActionMath::Pi;

static void passage() {
    for(float fps:{30.f,60.f,144.f}) for(float speed:{80.f,300.f,1800.f}) {
        V position{-500,0,0}; int next=0;
        V goals[]={{0,0,0},{1000,0,0},{2000,0,0}};
        for(int frame=0;frame<static_cast<int>(fps*50) && next<3;++frame) {
            V previous=position; position.x+=speed/fps;
            if(passed(previous,position,goals[next],150)) ++next;
        }
        assert(next==3);
    }
    assert(passed({-500,0,0},{500,0,0},{0,0,0},150)); // long frame: swept passage
    assert(!passed({-500,300,0},{500,300,0},{0,0,0},150)); // never consume a distant point
    assert(!passed({0,0,0},{100,0,0},{1000,0,0},150));
}
static void beta() {
    // Reversed first segment and a gap: beta joins the nearest ends at their midpoint.
    auto points=betaPath({{2,{10000,0,0},{20000,0,0}}, {1,{8000,0,0},{0,0,0}}});
    assert(points.size()==3);
    assert(length(points[0])<.01f && std::abs(points[1].x-9000)<.01f);
    assert(std::abs(points[2].x-20000)<.01f);
    auto loop=betaPath({{1,{0,0,0},{10000,0,0}}, {2,{10000,0,0},{0,0,1000}}});
    assert(length(loop.front()-loop.back())<.01f);
    assert(std::abs(betaCost({{0,0,0},1,0},{{300,0,0},1,1})-1)<.01f);
    assert(std::abs(betaCost({{0,0,0},1,0},{{300,0,0},2,1})-7.5f)<.01f);
}
static void avoidance() {
    assert(!sphereClear({-10000,0,0},{10000,0,0},{},4200));
    assert(sphereClear({-10000,5000,0},{10000,5000,0},{},4200));
    assert(sphereClear({4100,0,0},{6000,0,0},{},4500)); // outward escape
    assert(!sphereClear({4100,0,0},{-6000,0,0},{},4500));
    assert(!sphereClear({6000,0,0},{4100,0,0},{},4500));
    for(float radius:{300.f,4200.f,11000.f}) {
        std::vector<Vertex> graph{{{-radius*3,0,0}},{{radius*3,0,0}}};
        for(int i=0;i<16;++i) {
            float angle=2*Pi*i/16.f,r=(radius+700)*1.09f;
            graph.push_back({{r*std::cos(angle),0,r*std::sin(angle)}});
        }
        std::vector<V> path;
        auto clear=[=](V a,V b){return sphereClear(a,b,{},radius+300);};
        assert(search(graph,clear,path) && path.size()>1);
        V previous=graph[0].position;
        for(V point:path) {assert(segmentDistance({},previous,point)>radius+300);previous=point;}
        assert(length(path.back()-graph[1].position)<.01f);
        assert(!search(graph,[](V,V){return false;},path) && path.empty());
    }
    std::vector<Vertex> graph{{{0,0,0}},{{10000,0,0}},{{0,0,1000},7,0},{{10000,0,1000},7,1}};
    std::vector<V> path;
    assert(search(graph,[](V,V){return true;},path));
    assert(path.size()==3); // beta's safe-corridor preference beats the short direct leg
    graph.resize(1025);
    assert(!search(graph,[](V,V){return true;},path));
}
static bool clearSpheres(std::vector<Sphere> const& hazards,V a,V b) {
    for(auto const& h:hazards) if(!sphereClear(a,b,h.center,h.radius)) return false;
    return true;
}
static void checkPath(std::vector<Sphere> const& hazards,V from,std::vector<V> const& path) {
    assert(!path.empty());
    for(V point:path) {
        assert(clearSpheres(hazards,from,point));
        from=point;
    }
}
static void miners() {
    // OM15's seven actual miner positions and the cargo/asteroid offsets from
    // SYSTEMS_MOD/OMEGA15/om15.ini. Conservative spherical fixture, not a live
    // physics capture: station 800 m, cargo 25 m, rotated rock enclosed by 355 m
    // (VMeshRef radius 324.642 + its 26.6 m centre offset), clearance+hull 350 m.
    V centers[]={{45000,0,5000},{28000,0,31000},{41000,0,31000},{19000,0,42000},
                 {13000,0,30000},{19000,0,15000},{24000,0,1000}};
    std::vector<Sphere> hazards{{{},11350},{{-8000,0,-25000},3500},{{-10000,0,35000},3500}};
    for(V center:centers) {
        hazards.push_back({center,1150});
        hazards.push_back({center+V{0,5,0},375});
        hazards.push_back({center+V{0,5,-235},705});
    }
    auto clear=[&](V a,V b){return clearSpheres(hazards,a,b);};
    std::vector<V> origins{{35000,0,-25000},{-30000,0,0}};
    for(V center:centers) origins.push_back(center+V{0,2000,0});
    unsigned routes=0;
    for(V from:origins) for(V center:centers) {
        // Ignoring only the dock target still leaves its endpoint in the rock.
        assert(!sphereClear(from,center,center+V{0,5,-235},705));
        auto goals=dockingGoals(from,center,2000,[&](V p){return clear(p,p);});
        std::vector<V> path;
        assert(planVisibility(from,center,goals,{},hazards,clear,path));
        checkPath(hazards,from,path);
        assert(length(path.back()-center)>1150 && length(path.back()-center)<=2000.1f);
        // On arrival, re-planning the final object must hand off here, without
        // adding a leg into the base centre or sending the ship away again.
        auto arrived=dockingGoals(path.back(),center,2000.1f,[&](V p){return clear(p,p);});
        assert(arrived.size()==1 && length(arrived.front()-path.back())<.01f);
        ++routes;
    }
    std::printf("PASS: %u OM15 miner approaches (7 bases, composite solids, sun/planet guards).\n",routes);
}
static void denseGeometry() {
    std::vector<Sphere> hazards;
    for(int i=0;i<80;++i) hazards.push_back({{static_cast<float>(i*25-1000),0,0},500});
    V from{-10000,0,0},to{10000,0,0};
    auto clear=[&](V a,V b){return clearSpheres(hazards,a,b);};
    std::vector<V> path;
    assert(planVisibility(from,to,{to},{},hazards,clear,path) && path.size()>1);
    checkPath(hazards,from,path);
    for(auto& h:hazards) h.center.z=1500;
    assert(planVisibility(from,to,{to},{},hazards,clear,path) && path.size()==1);
    checkPath(hazards,from,path);

    // A blocked base remains unreachable; no unchecked direct fallback.
    auto goals=dockingGoals(from,{},2000,[](V){return false;});
    assert(!planVisibility(from,{},goals,{},hazards,clear,path) && path.empty());
    goals=dockingGoals(from,{},2000,[](V p){return length(p)>3200;});
    assert(!goals.empty() && std::abs(length(goals.front())-4000)<.1f);

    // Approach region on the far side of a planet: neither the route nor its
    // final native-Dock segment may use the tempting near-side shortcut.
    Sphere planet{{0,0,0},6000}; V center{6500,0,0}; from={-20000,0,0};
    hazards={planet,{center,400}};
    goals=dockingGoals(from,center,2000,[&](V p) {
        return clear(p,p) && sphereClear(p,center,planet.center,planet.radius);
    });
    assert(planVisibility(from,center,goals,{},hazards,clear,path));
    checkPath(hazards,from,path);
    assert(sphereClear(path.back(),center,planet.center,planet.radius));
}
static void stationDeparture() {
    // Tokyo core and forward dock overlap after hull/clearance expansion.
    // Between their centres, a valid escape can be tangent to both guards;
    // detour points on the merged sphere need not include that plane.
    for(V axis:{V{0,0,1},unit(V{1,2,3})}) {
        V center{-50000,0,-41560};
        std::vector<Sphere> hazards{{center,2000},{center+axis*1560,1100}};
        V from=center+axis*700;
        V to=center+V{25000,3000,19000};
        auto clear=[&](V a,V b){return clearSpheres(hazards,a,b);};
        std::vector<V> path;
        assert(!clear(from,to));
        assert(planVisibility(from,to,{to},{},hazards,clear,path));
        checkPath(hazards,from,path);
        assert(path.size()>1 && clear(path.front(),path.front()));
        // A destination inside the station remains invalid.
        assert(!planVisibility(to,from,{from},{},hazards,clear,path));
    }
}
int main() {
    passage(); beta(); avoidance(); miners(); denseGeometry(); stationDeparture();
    std::puts("PASS: waypoint passage at 30/60/144 Hz, long-frame crossing, beta path joints/costs, atmosphere detours, outward escape, no-path, crowded geometry and graph bounds.");
}
