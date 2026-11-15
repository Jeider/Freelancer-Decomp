#pragma once
// Narrow phase for hollow static solars. Internal BVH wrap hulls are not walls.
#include "../IVP/ivp_collision/ivp_compact_surface.h"
#include <algorithm>
#include <cmath>
#include <limits>

namespace SolarAvoidanceGeometry {
struct V { double x,y,z; };
inline V add(V a,V b) { return {a.x+b.x,a.y+b.y,a.z+b.z}; }
inline V sub(V a,V b) { return {a.x-b.x,a.y-b.y,a.z-b.z}; }
inline V mul(V a,double s) { return {a.x*s,a.y*s,a.z*s}; }
inline double dot(V a,V b) { return a.x*b.x+a.y*b.y+a.z*b.z; }
inline V cross(V a,V b) { return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x}; }
inline double clamp(double x) { return (std::max)(0.,(std::min)(1.,x)); }
inline V point(float const* p) { return {p[0],p[1],p[2]}; }

inline V closestTriangle(V p,V a,V b,V c) {
    V ab=sub(b,a),ac=sub(c,a),ap=sub(p,a);
    double d1=dot(ab,ap),d2=dot(ac,ap);
    if(d1<=0 && d2<=0) return a;
    V bp=sub(p,b); double d3=dot(ab,bp),d4=dot(ac,bp);
    if(d3>=0 && d4<=d3) return b;
    double vc=d1*d4-d3*d2;
    if(vc<=0 && d1>=0 && d3<=0) return add(a,mul(ab,d1/(d1-d3)));
    V cp=sub(p,c); double d5=dot(ab,cp),d6=dot(ac,cp);
    if(d6>=0 && d5<=d6) return c;
    double vb=d5*d2-d1*d6;
    if(vb<=0 && d2>=0 && d6<=0) return add(a,mul(ac,d2/(d2-d6)));
    double va=d3*d6-d5*d4;
    if(va<=0 && d4-d3>=0 && d5-d6>=0)
        return add(b,mul(sub(c,b),(d4-d3)/((d4-d3)+(d5-d6))));
    double sum=va+vb+vc;
    if(std::abs(sum)<1e-20) return a;
    return add(a,add(mul(ab,vb/sum),mul(ac,vc/sum)));
}

struct Distance { double squared,along; V wall; };
inline void consider(Distance& best,V p,V q,double t) {
    double d=dot(sub(p,q),sub(p,q));
    if(d<best.squared) best={d,t,q};
}
inline void segmentEdge(Distance& best,V a,V b,V c,V d) {
    V u=sub(b,a),v=sub(d,c),r=sub(a,c);
    double aa=dot(u,u),bb=dot(u,v),cc=dot(v,v),dd=dot(u,r),ee=dot(v,r),s=0,t=0;
    if(aa<1e-20) t=cc>1e-20?clamp(ee/cc):0;
    else if(cc<1e-20) s=clamp(-dd/aa);
    else {
        double denom=aa*cc-bb*bb;
        if(denom>1e-20) s=clamp((bb*ee-cc*dd)/denom);
        t=(bb*s+ee)/cc;
        if(t<0) {t=0;s=clamp(-dd/aa);}
        else if(t>1) {t=1;s=clamp((bb-dd)/aa);}
    }
    consider(best,add(a,mul(u,s)),add(c,mul(v,t)),s);
}
inline Distance segmentTriangle(V from,V to,V a,V b,V c) {
    Distance best{(std::numeric_limits<double>::max)(),0,a};
    consider(best,from,closestTriangle(from,a,b,c),0);
    consider(best,to,closestTriangle(to,a,b,c),1);
    segmentEdge(best,from,to,a,b); segmentEdge(best,from,to,b,c); segmentEdge(best,from,to,c,a);
    V normal=cross(sub(b,a),sub(c,a)),direction=sub(to,from);
    double denom=dot(normal,direction);
    if(std::abs(denom)>1e-15) {
        double t=dot(normal,sub(a,from))/denom;
        if(t>=0 && t<=1) { V p=add(from,mul(direction,t));consider(best,p,closestTriangle(p,a,b,c),t); }
    }
    return best;
}

inline bool overlaps(IVP_Compact_Ledgetree_Node const* node,V from,V to,double radius) {
    double lo=0,hi=1,aa[3]={from.x,from.y,from.z},bb[3]={to.x,to.y,to.z};
    for(int axis=0;axis<3;++axis) {
        // Retail SUR quantization occasionally underbounds by a few centimetres.
        double half=node->box_sizes[axis]*node->radius*.004+radius+.1;
        double low=node->center[axis]-half,high=node->center[axis]+half,delta=bb[axis]-aa[axis];
        if(std::abs(delta)<1e-12) {if(aa[axis]<low || aa[axis]>high) return false;}
        else {double a=(low-aa[axis])/delta,b=(high-aa[axis])/delta;if(a>b)std::swap(a,b);lo=(std::max)(lo,a);hi=(std::min)(hi,b);if(lo>hi)return false;}
    }
    return true;
}

struct Query {
    V from,to;
    double radius;
    bool hit=false,exhausted=false;
    unsigned visited=0,triangles=0;
    Distance nearest{(std::numeric_limits<double>::max)(),0,{0,0,0}};
};
template<class Attached> void walk(IVP_Compact_Ledgetree_Node const* node,Query& q,Attached attached,unsigned depth=0) {
    if(++q.visited>50000 || depth>100) {q.exhausted=true;return;}
    if(!overlaps(node,q.from,q.to,q.radius)) return;
    if(node->offset_right_node) {walk(node->left_son(),q,attached,depth+1);if(!q.exhausted)walk(node->right_son(),q,attached,depth+1);return;}
    if(!node->offset_compact_ledge) return;
    auto* hull=node->get_compact_ledge();
    if((hull->SizeAndFlags&3u)!=0 || !attached(static_cast<unsigned>(hull->ClientData))) return;
    auto* faces=hull->GetFirstTriangle();
    for(int i=0;i<hull->GetNTriangles();++i) {
        ++q.triangles;
        V a=point(hull->GetPoint(&faces[i].CEdge[0])->AsArray());
        V b=point(hull->GetPoint(&faces[i].CEdge[1])->AsArray());
        V c=point(hull->GetPoint(&faces[i].CEdge[2])->AsArray());
        Distance d=segmentTriangle(q.from,q.to,a,b,c);
        if(d.squared<=q.radius*q.radius && (!q.hit || d.along<q.nearest.along-1e-9 ||
            (std::abs(d.along-q.nearest.along)<=1e-9 && d.squared<q.nearest.squared))) {
            q.hit=true;q.nearest=d;
        }
    }
}
}
