// Authored vector cursor artwork, in mouse.ini's 256-unit, top-left/Y-down space.
// No TGA/DDS decoding, atlas flips, or generated-PNG pixels are used at runtime.
// Portable on purpose: the offline preview/check executes the same rasterizer.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>

namespace CursorVectorArt {
constexpr float Pi = 3.14159265358979323846f;
struct Point { float x, y; };
inline Point operator+(Point a, Point b) { return {a.x+b.x,a.y+b.y}; }
inline Point operator-(Point a, Point b) { return {a.x-b.x,a.y-b.y}; }
inline Point operator*(Point a, float s) { return {a.x*s,a.y*s}; }
inline float Dot(Point a, Point b) { return a.x*b.x+a.y*b.y; }
inline float Length(Point a) { return std::sqrt(Dot(a,a)); }
inline float Clamp(float x,float a,float b) { return (std::max)(a,(std::min)(b,x)); }
struct Color { float r,g,b; };
constexpr Color Blue{150,218,238}, White{255,255,255};

struct Primitive {
    enum Type { Polygon, Circle, Ring, RoundBox, Segment } type = Polygon;
    std::vector<Point> points;
    Point center{}, half{};
    float radius=0, width=0, dilation=0;
    bool subtract=false;
    float Distance(Point p) const {
        if(type==Circle) return Length(p-center)-radius;
        if(type==Ring) return std::fabs(Length(p-center)-radius)-width*.5f;
        if(type==RoundBox) {
            Point q{std::fabs(p.x-center.x)-half.x+radius,
                    std::fabs(p.y-center.y)-half.y+radius};
            return Length({(std::max)(q.x,0.f),(std::max)(q.y,0.f)})+
                (std::min)((std::max)(q.x,q.y),0.f)-radius;
        }
        if(type==Segment) {
            Point d=points[1]-points[0], a=p-points[0];
            return Length(a-d*Clamp(Dot(a,d)/Dot(d,d),0,1))-width*.5f;
        }
        float dist=1e9f; bool inside=false;
        for(size_t i=0,j=points.size()-1;i<points.size();j=i++) {
            Point a=points[j],b=points[i],d=b-a;
            float dd=Dot(d,d);
            dist=(std::min)(dist,Length(p-a-d*(dd>0?Clamp(Dot(p-a,d)/dd,0,1):0)));
            if((a.y>p.y)!=(b.y>p.y) && p.x<(b.x-a.x)*(p.y-a.y)/(b.y-a.y)+a.x)
                inside=!inside;
        }
        return (inside?-dist:dist)-dilation;
    }
};
inline Primitive Poly(std::vector<Point> p) { Primitive s; s.points=std::move(p); return s; }
inline Primitive Disk(Point c,float r) { Primitive s; s.type=Primitive::Circle;s.center=c;s.radius=r;return s; }
inline Primitive Ring(Point c,float r,float w) { auto s=Disk(c,r);s.type=Primitive::Ring;s.width=w;return s; }
inline Primitive Box(Point c,Point h,float r=0) { Primitive s;s.type=Primitive::RoundBox;s.center=c;s.half=h;s.radius=r;return s; }
inline Primitive Line(Point a,Point b,float w) { Primitive s;s.type=Primitive::Segment;s.points={a,b};s.width=w;return s; }
struct Layer {
    Color color;
    std::vector<Primitive> parts;
    // Optional analytic surface shading; absent for the existing cursor artwork.
    Color (*paint)(Point,Layer const&)=nullptr;
    float Distance(Point p) const {
        float d=1e9f;
        for(auto const& s:parts) d=s.subtract?(std::max)(d,-s.Distance(p)):(std::min)(d,s.Distance(p));
        return d;
    }
};
struct Icon {
    char const* name;
    Color glow;
    float sigma=5, strength=.38f;
    std::vector<Layer> layers;
    float sampleScale=1;
    Point sampleOffset{};
    Color tint=White;
    Layer& Add(Color c) { layers.push_back({c,{}});return layers.back(); }
};
inline void Hollow(Layer& l,Primitive outer,Primitive inner) {
    l.parts.push_back(outer);inner.subtract=true;l.parts.push_back(inner);
}
inline void Outline(Layer& l,std::vector<Point> const& p,float w) {
    for(size_t i=0;i<p.size();++i) l.parts.push_back(Line(p[i],p[(i+1)%p.size()],w));
}
inline void Stroke(Layer& l,std::vector<Point> const& p,float w) {
    for(size_t i=1;i<p.size();++i)l.parts.push_back(Line(p[i-1],p[i],w));
}
struct Path {
    std::vector<Point> p;
    explicit Path(Point start):p{start} {}
    Path& To(Point q) {p.push_back(q);return *this;}
    Path& Curve(Point b,Point c,Point d,int steps=12) {
        Point a=p.back();
        for(int i=1;i<=steps;++i) {float t=i/float(steps),u=1-t;
            p.push_back(a*(u*u*u)+b*(3*u*u*t)+c*(3*u*t*t)+d*(t*t*t));}
        return *this;
    }
};
inline Point Rotate(Point p,float a) { float c=std::cos(a),s=std::sin(a);return {c*p.x-s*p.y,s*p.x+c*p.y}; }
inline std::vector<Point> Rounded(std::vector<Point> const& p,float trim) {
    std::vector<Point> out;
    for(size_t i=0;i<p.size();++i) {
        Point c=p[i],da=p[(i+p.size()-1)%p.size()]-c,db=p[(i+1)%p.size()]-c;
        Point a=c+da*((std::min)(trim/Length(da),.3f)),b=c+db*((std::min)(trim/Length(db),.3f));
        for(int k=0;k<=4;++k) {float t=k/4.f,u=1-t;out.push_back(a*(u*u)+c*(2*u*t)+b*(t*t));}
    }
    return out;
}
struct Sample { Color color;float alpha; };
inline float Halo(Icon const& icon,float distance) {
    float d=(std::max)(distance,0.f)/icon.sigma;
    return d>=3.5f?0.f:icon.strength*std::exp(-.5f*d*d);
}
inline Sample Evaluate(Icon const& icon,Point p,float pixelWidth) {
    p=p*icon.sampleScale+icon.sampleOffset;pixelWidth*=icon.sampleScale;
    float distance=1e9f, alpha=0;Color rgb{};
    for(auto const& layer:icon.layers) {
        float d=layer.Distance(p);distance=(std::min)(distance,d);
        float coverage=Clamp(.5f-d/pixelWidth,0,1);
        Color c=coverage>0 && layer.paint?layer.paint(p,layer):layer.color;
        rgb={c.r*coverage+rgb.r*(1-coverage),
             c.g*coverage+rgb.g*(1-coverage),
             c.b*coverage+rgb.b*(1-coverage)};
        alpha=coverage+alpha*(1-coverage);
    }
    // Glow behind opaque cores. Distance to the filled stroke works on BOTH
    // sides, including the holes. Never add white or inherit noisy raster glow.
    float glow=Halo(icon,distance)*(1-alpha);
    rgb={rgb.r+icon.glow.r*glow,rgb.g+icon.glow.g*glow,rgb.b+icon.glow.b*glow};
    alpha+=glow;
    Color result=alpha>0?Color{rgb.r/alpha,rgb.g/alpha,rgb.b/alpha}:icon.glow;
    result={result.r*icon.tint.r/255,result.g*icon.tint.g/255,result.b*icon.tint.b/255};
    return {result,alpha};
}
inline int TextureSize(float displayedSide) {
    int size=64;
    while(size<512 && size<displayedSide*2)size*=2;
    return size;
}
inline std::vector<uint32_t> Rasterize(Icon const& icon,int size) {
    std::vector<uint32_t> pixels(size*size);
    float step=256.f/size;
    for(int y=0;y<size;++y) for(int x=0;x<size;++x) {
        auto s=Evaluate(icon,{(x+.5f)*step,(y+.5f)*step},step);
        auto byte=[](float v)->uint32_t {return static_cast<uint32_t>(Clamp(v,0,255)+.5f);};
        pixels[y*size+x]=(byte(s.alpha*255)<<24)|(byte(s.color.r)<<16)|(byte(s.color.g)<<8)|byte(s.color.b);
    }
    return pixels;
}
} // namespace CursorVectorArt
