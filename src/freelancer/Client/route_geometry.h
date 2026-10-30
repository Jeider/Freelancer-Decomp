#pragma once
#include "flight_action_math.h"
#include <vector>
#include <limits>

// Independent of the engine: route passage and visibility graph search.
namespace RouteGeometry {
using FlightActionMath::V;
using FlightActionMath::dot;
using FlightActionMath::length;
using FlightActionMath::unit;
inline float segmentDistance(V p,V a,V b) {
    V d=b-a;
    float t=std::clamp(dot(p-a,d)/(std::max)(dot(d,d),0.0001f),0.f,1.f);
    return length(p-(a+d*t));
}
inline bool passed(V previous,V current,V target,float radius) {
    return segmentDistance(target,previous,current)<=radius;
}
inline bool sphereClear(V a,V b,V center,float radius) {
    if(segmentDistance(center,a,b)>radius) return true;
    // Starting near a station/inside a hazard: admit an outward escape only.
    // This never permits entering the sphere from outside or crossing its core.
    return length(a-center)<radius && length(b-center)>radius && dot(a-center,b-a)>=0;
}
struct CorridorSegment { int order; V a,b; };
inline std::vector<V> betaPath(std::vector<CorridorSegment> steps) {
    if(steps.empty()) return {};
    std::sort(steps.begin(),steps.end(),[](auto const& a,auto const& b){return a.order<b.order;});
    V first=steps[0].a,current=steps[0].b;
    if(steps.size()>1 && segmentDistance(first,steps[1].a,steps[1].b)<segmentDistance(current,steps[1].a,steps[1].b))
        std::swap(first,current);
    std::vector<V> points{first};
    for(size_t i=1;i<steps.size();++i) {
        auto const& s=steps[i];
        bool nearA=length(current-s.a)<length(current-s.b);
        points.push_back((current+(nearA?s.a:s.b))*.5f);
        current=nearA?s.b:s.a;
    }
    if(steps.size()>1 && length(current-first)<5000) points[0]=current=(first+current)*.5f;
    points.push_back(current);
    return points;
}
struct Vertex { V position; int corridor=-1; int order=0; };

// Beta Content 06EDB320 values: off-corridor travel costs distance / 40,
// travel along a patrol path costs distance / 300. The graph search is new;
// unlike the beta's greedy walk it can connect several unobstructed corridors.
inline float betaCost(Vertex const& a,Vertex const& b) {
    bool along=a.corridor>=0 && a.corridor==b.corridor && std::abs(a.order-b.order)==1;
    return length(b.position-a.position)/(along ? 300.f : 40.f);
}
template<class Clear> bool search(std::vector<Vertex> const& vertices,Clear clear,
                                 std::vector<V>& result,size_t goalCount=1) {
    result.clear();
    size_t n=vertices.size();
    if(n<2 || n>1024 || goalCount==0 || goalCount>=n) return false;
    std::vector<float> cost(n,std::numeric_limits<float>::infinity());
    std::vector<int> parent(n,-1);
    std::vector<bool> closed(n,false);
    cost[0]=0;
    for(size_t step=0;step<n;++step) {
        size_t best=n;
        for(size_t i=0;i<n;++i) if(!closed[i] && (best==n || cost[i]<cost[best])) best=i;
        if(best==n || !std::isfinite(cost[best])) return false;
        if(best>0 && best<=goalCount) {
            for(int i=static_cast<int>(best);i!=0;i=parent[i]) result.push_back(vertices[i].position);
            std::reverse(result.begin(),result.end());
            return true;
        }
        closed[best]=true;
        for(size_t i=0;i<n;++i) if(!closed[i] && i!=best) {
            float candidate=cost[best]+betaCost(vertices[best],vertices[i]);
            if(candidate<cost[i] && clear(vertices[best].position,vertices[i].position)) {
                cost[i]=candidate; parent[i]=static_cast<int>(best);
            }
        }
    }
    return false;
}

// A dockable object is an arrival region, not a request to fly into its mesh.
// Keep several approach directions: cargo/asteroids can cover the near side.
template<class CanDock> std::vector<V> dockingGoals(V from,V center,float range,CanDock canDock) {
    if(length(from-center)<=range && canDock(from)) return {from};
    std::vector<V> goals;
    for(float scale:{1.f,1.5f,2.f}) {
        auto add=[&](V direction) {
            if(length(direction)<.01f) return;
            V point=center+unit(direction)*(range*scale);
            if(canDock(point)) goals.push_back(point);
        };
        add(from-center);
        for(int x=-1;x<=1;++x) for(int y=-1;y<=1;++y) for(int z=-1;z<=1;++z)
            add({static_cast<float>(x),static_cast<float>(y),static_cast<float>(z)});
        if(!goals.empty()) break;
    }
    return goals;
}

struct Sphere { V center; float radius; };
inline Sphere enclosing(Sphere a,Sphere b) {
    float d=length(b.center-a.center);
    if(a.radius>=d+b.radius) return a;
    if(b.radius>=d+a.radius) return b;
    float radius=(d+a.radius+b.radius)*.5f;
    return {a.center+unit(b.center-a.center)*(radius-a.radius),radius};
}

// A ship can be outside the mesh but inside several overlapping clearance
// spheres. Seed exits relative to the ship, not just the merged sphere centre:
// that sphere's fixed rings can miss the narrow common outward direction.
template<class Clear> void addDepartureVertices(V from,V target,std::vector<Sphere> const& bounds,
        Clear clear,std::vector<Vertex>& vertices) {
    if(clear(from,from)) return;
    std::vector<Sphere> containing;
    std::vector<V> normals;
    for(auto const& bound:bounds) if(length(from-bound.center)<=bound.radius) {
        containing.push_back(bound);
        V n=unit(from-bound.center);
        if(length(n)>.5f && normals.size()<32 &&
           std::none_of(normals.begin(),normals.end(),[&](V other){return dot(n,other)>.9999f;}))
            normals.push_back(n);
    }
    if(containing.empty()) return;
    size_t limit=(std::min)(vertices.size()+128,size_t(640));
    auto add=[&](V direction) {
        if(vertices.size()>=limit || length(direction)<.0001f) return;
        direction=unit(direction);
        float distance=0;
        for(auto const& bound:containing) {
            V offset=from-bound.center;
            float along=dot(offset,direction);
            float exit=-along+std::sqrt((std::max)(0.f,
                along*along+bound.radius*bound.radius-dot(offset,offset)));
            distance=(std::max)(distance,exit);
        }
        V point=from+direction*(distance+400.f);
        // Candidate generation grants no exemptions: other solids, atmospheres
        // and damage volumes are checked by the same predicate as every leg.
        if(clear(point,point) && clear(from,point) &&
           std::none_of(vertices.begin(),vertices.end(),[&](Vertex const& v){return length(v.position-point)<1.f;}))
            vertices.push_back({point});
    };
    add(target-from);
    V outward{};
    for(V n:normals) {outward=outward+n;add(n);}
    add(outward);
    for(int x=-1;x<=1;++x) for(int y=-1;y<=1;++y) for(int z=-1;z<=1;++z)
        add({static_cast<float>(x),static_cast<float>(y),static_cast<float>(z)});
    auto tangent=[&](V a,V b) {
        V d=FlightActionMath::cross(a,b);
        add(d);add(d*-1.f);
    };
    for(size_t i=0;i<normals.size();++i) {
        for(V axis:{V{1,0,0},V{0,1,0},V{0,0,1}}) tangent(normals[i],axis);
        for(size_t j=0;j<i;++j) tangent(normals[i],normals[j]);
    }
}

// Bound candidate generation, not the number of physical obstacles checked.
// Overlapping components share detour candidates, but collision checks still
// use every original volume. Dense stations cannot exhaust the graph up front.
template<class Clear> bool planVisibility(V from,V target,std::vector<V> const& goals,
        std::vector<Vertex> const& corridors,std::vector<Sphere> const& bounds,
        Clear clear,std::vector<V>& result) {
    result.clear();
    if(goals.empty() || goals.size()>128) return false;
    std::vector<Vertex> vertices{{from}};
    float endRange=0;
    for(V goal:goals) {
        vertices.push_back({goal});
        endRange=(std::max)(endRange,length(goal-target));
    }
    float span=length(target-from);
    for(auto const& point:corridors)
        if(vertices.size()<480 && length(point.position-from)+length(point.position-target)<span*1.8f+endRange+10000)
            vertices.push_back(point);
    if(search(vertices,clear,result,goals.size())) return result.size()<=99;
    addDepartureVertices(from,target,bounds,clear,vertices);

    std::vector<Sphere> clusters;
    for(auto bound:bounds) {
        if(segmentDistance(bound.center,from,target)>bound.radius+endRange+2000) continue;
        for(size_t i=0;i<clusters.size();) {
            if(length(bound.center-clusters[i].center)<=bound.radius+clusters[i].radius) {
                bound=enclosing(bound,clusters[i]);
                clusters.erase(clusters.begin()+i); i=0;
            } else ++i;
        }
        clusters.push_back(bound);
    }
    std::stable_sort(clusters.begin(),clusters.end(),[&](auto const& a,auto const& b) {
        return segmentDistance(a.center,from,target)-a.radius < segmentDistance(b.center,from,target)-b.radius;
    });
    for(auto const& bound:clusters) {
        float radius=(bound.radius+400)*1.09f; // chords stay outside the guard volume
        for(int plane=0;plane<3;++plane) for(int i=0;i<16 && vertices.size()<1000;++i) {
            float angle=2*FlightActionMath::Pi*i/16.f;
            float a=std::cos(angle)*radius,b=std::sin(angle)*radius;
            V d=plane==0?V{a,0,b}:plane==1?V{a,b,0}:V{0,a,b};
            V point=bound.center+d;
            if(clear(point,point)) vertices.push_back({point});
        }
    }
    if(!search(vertices,clear,result,goals.size())) return false;
    return result.size()<=99;
}
}
