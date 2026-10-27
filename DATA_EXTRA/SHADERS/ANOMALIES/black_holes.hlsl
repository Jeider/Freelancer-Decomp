#include "common.hlsli"
#ifndef VARIANT
#define VARIANT 2
#endif

// A green solar source belongs to the *background*, never a specular BRDF.
float3 monkeySky(float3 rd) {
    float3 sunDirection=normalize(float3(-.51,.31,-1));
    float a=acos(clamp(dot(normalize(rd),sunDirection),-1,1));
    float core=1-smoothstep(.045,.058,a);
    return sky(rd)*float3(.5,1,.7)+float3(.1,1,.32)*(core*9+.004/(a*a+.004));
}
float4 PSMain(PixelIn input) : COLOR0 {
    float3 ro,rd; camera(input.uv,ro,rd);
#if VARIANT == 0
    // Artistic successor to the mod's solar-atmosphere refraction trick.
    // Radial angular remap, chromatic fringe and opaque inner silhouette.
    // No reflected environment, material highlight or reflective sphere here.
    float b=length(cross(ro,rd));
    float3 radial=normalize(ro+rd*(-dot(ro,rd))+float3(1e-5,0,0));
    float band=exp(-abs(b-1.52)*3.8);
    float ripple=sin(b*37-Frame.x*1.4)*.045*band;
    float strength=.25*band+ripple;
    float3 bent=normalize(rd-radial*strength);
    float3 col=monkeySky(bent);
    col.r=monkeySky(normalize(rd-radial*(strength*1.04))).r;
    col.b=monkeySky(normalize(rd-radial*(strength*.96))).b;
    float mask=smoothstep(1.38,1.41,b);
    col*=mask;
    col+=float3(.008,.14,.045)*gaussian((b-1.43)/.035);
    return float4(col,1);
#else
    // Bounded artistic ray bending, NOT a GR geodesic solver.
    float3 p=ro,d=rd,light=0; float tr=1,hit=0;
    [loop] for(int i=0;i<176;++i) {
        float r=length(p);
        if(r<.63) { hit=1; break; }
        if(r>View.w+2 && i>16) break;
        float ds=clamp(r*.027,.038,.20);
        float3 perpendicular=p-d*dot(p,d);
#if VARIANT == 1
        d=normalize(d-.22*perpendicular/(r*r*r)*ds);
#else
        d=normalize(d-.86*perpendicular/(r*r*r)*ds);
#endif
        p+=d*ds;
        float radial=length(p.xz),angle=atan2(p.z,p.x);
        float rotation=Frame.x*.52/pow(max(radial,.8),1.5);
        float a=angle+rotation;
        float3 q=float3(cos(a)*radial,p.y*3,sin(a)*radial);
        float n=turbulence(q*7);
        float spiral=.55+.45*sin(a*3-radial*8+n*3);
        float window=smoothstep(.93,1.16,radial)*(1-smoothstep(2.65,3.30,radial));
#if VARIANT == 1
        // Public promo vm0QkrtOF2Q at 01:24: red disk, white ring, thin blue jet.
        float height=.06+.018*radial;
        float streak=(.18+.82*pow(.5+.5*sin(radial*42+n*9+a*2),2))*(.25+pow(n*1.5,3));
        float dens=gaussian(p.y/height)*window*(.5+2*n+spiral)*5;
        float whiteRing=gaussian((radial-1.18)/.16);
        float3 color=lerp(float3(2.1,.045,.015)*streak,float3(4.5,3.8,3.3),whiteRing);
        float jet=gaussian(length(p.xz)/.028)*(1-smoothstep(2.7,3.4,abs(p.y)))*smoothstep(.65,.8,abs(p.y));
        float3 emission=color*dens+float3(.7,1.6,4)*jet*5;
        dens+=jet*2;
        // Analytic, orbiting debris clusters. They absorb and show emissive cracks.
        float sector=floor((a+PI)*3.0);
        float ca=(sector+.5)/3.0-PI;
        float orbit=2.6+.48*sin(sector*2.7);
        float3 chunkCenter=float3(cos(ca)*orbit,.28*sin(sector*5.3)+.2,sin(ca)*orbit);
        float chunkDistance=length(q-chunkCenter);
        float rock=(1-smoothstep(.105,.17,chunkDistance))*(.6+n)*15;
        float cracks=pow(saturate((noise(q*37)-.49)*6),3);
        emission+=rock*(float3(.018,.008,.004)+float3(1.7,.3,.015)*cracks);
        dens+=rock;
        color=emission/max(dens,.0001);
#else
        float height=.035+.014*radial;
        float dens=gaussian(p.y/height)*window*(.4+2*n+spiral)*9;
        float heat=saturate(1.7/radial-.35);
        float streak=.28+.72*pow(.5+.5*sin(radial*80+n*9+a*2),2);
        float3 color=lerp(float3(1.9,.23,.018),float3(3.6,2.1,.9),heat);
        float doppler=pow(clamp(1+.45*dot(normalize(float3(-p.z,0,p.x)), -d),.5,1.5),3);
        color*=doppler*(.35+.65*spiral)*streak;
#endif
        integrate(light,tr,color,dens,ds);
        if(tr<.004) break;
    }
    // Stable projected core for the intro proxy; prevents unresolved
    // high-order samples at the capture boundary from looking like a star globe.
#if VARIANT == 1
    float core=1-smoothstep(.69,.71,length(cross(ro,rd)));
    light*=1-core;
    hit=max(hit,core);
#endif
    return float4(light+tr*(1-hit)*sky(d),1);
#endif
}
