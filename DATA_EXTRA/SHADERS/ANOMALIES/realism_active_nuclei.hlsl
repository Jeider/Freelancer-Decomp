#include "realism_common.hlsli"
#ifndef VARIANT
#define VARIANT 0
#endif
float nuclearDust(float3 p) {
    float radius=length(p.xz),a=atan2(p.z,p.x);
    float clumps=fbm5(p*2.4+float3(3,8,1));
    float lanes=noise(p*10);
    float torus=gaussian((radius-2.7)/1.0)*gaussian(p.y/(.32+.12*radius));
    torus*=smoothstep(1.25,1.85,radius)*(1-smoothstep(4.2,5.4,radius));
    float arcs=.65+.35*sin(a*3-radius*2.5+clumps*4);
    return torus*pow(saturate(clumps*1.5-.24),2)*(.4+lanes)*arcs*4.5;
}
float nuclearShadow(float3 p) {
    float step=length(p)/10,tau=0;
    [loop] for(int k=0;k<8;++k) tau+=nuclearDust(p*(.16+.10*k))*step;
    return exp(-tau*1.7);
}
float4 PSMain(PixelIn input) : COLOR0 {
    float3 ro,rd;camera(input.uv,ro,rd);
    float nucleusRadius=VARIANT==0?.065:.14;
    float coreHit=sphereHit(ro,rd,nucleusRadius),stop=coreHit;
    float3 companion=float3(3.4,.10,0);
    float donorHit=1e5;
#if VARIANT == 1
    donorHit=sphereHit(ro-companion,rd,.72);
    stop=min(stop,donorHit);
#endif
    float2 interval=volumeInterval(ro,rd,VARIANT==0?14.0:7.0);
    interval.y=min(interval.y,stop);
    if(interval.y<=interval.x) return float4(quietSky(rd)*.22,1);
    float ds=(interval.y-interval.x)/(VOLUME_PASSES*128);
    float3 radiance=0,transmission=1;
    [loop] for(int batch=0;batch<VOLUME_PASSES;++batch) {
        [loop] for(int k=0;k<128;++k) {
            float3 p=ro+rd*(interval.x+(batch*128+k+.5)*ds);
            float radial=length(p.xz),r=length(p),height=abs(p.y);
            float angle=atan2(p.z,p.x),flow=height*.7-Frame.x*.18;
            // Collimated spine, broad intermittent sheath, nonperiodic shocks.
            float width=.035+height*(VARIANT==0?.036:.045);
            float2 centre=float2(sin(height*.38),cos(height*.31))*(.003*height);
            float radius=length(p.xz-centre);
            float spine=gaussian(radius/width),sheath=gaussian((radius-width*1.65)/(width*.5));
            float knots=pow(noise(float3(2,flow,9)*3.2),3)*3+.2;
            float filament=fbm5(float3(p.x*24,flow*2,p.z*24));
            float jet=(spine+sheath*.22)*knots*(.4+filament)*smoothstep(.18,.38,height);
            jet*=1-smoothstep(VARIANT==0?10.0:4.8,VARIANT==0?13.5:6.7,height);
            float observerCos=dot(-rd,float3(0,p.y<0?-1:1,0));
            float beta=VARIANT==0?.94:.78;
            float doppler=sqrt(1-beta*beta)/max(1-beta*observerCos,.04);
            float3 emission=float3(.70,.79,1)*jet*pow(doppler,3)*26;
            float3 extinction=jet*.012;
#if VARIANT == 0
            float dust=nuclearDust(p);
            if(dust>.0001) {
                float shadow=nuclearShadow(p);
                float scatter=henyeyGreenstein(dot(normalize(p),-rd),.45);
                float irradiance=36/max(r*r,.2);
                emission+=float3(.48,.32,.19)*dust*irradiance*shadow*(.12+.35*scatter);
                // Hot inner dust rim is primarily IR. Optional sensor response
                // reveals it without pretending visible 1200 K dust is white-hot.
                float rim=gaussian((radial-1.85)/.24)*dust;
                emission+=thermalRGB(1400)*rim*18+float3(.30,.11,.035)*rim*Event.y;
                extinction+=dust*float3(1.25,1.65,2.25);
            }
#else
            // A compact resolved disk + a narrow, curved mass-transfer stream.
            float disk=gaussian(p.y/.035)*smoothstep(.18,.28,radial)*(1-smoothstep(1.1,1.45,radial));
            float a=angle+Frame.x*.28/pow(max(radial,.22),1.5);
            float grain=fbm5(float3(cos(a)*radial*12,p.y,sin(a)*radial*12));
            float temperature=11000*pow(.3/max(radial,.3),.68);
            emission+=thermalRGB(temperature)*disk*(.3+grain)*9;
            extinction+=disk*3;
            float along=saturate((p.x-.8)/2.6);
            float3 delta=float3(0,p.y-.10,p.z-.48*sin(along*PI));
            float stream=gaussian(length(delta)/.045)*smoothstep(.75,1.0,p.x)*(1-smoothstep(3.0,3.4,p.x));
            emission+=thermalRGB(7000)*stream*1.6;
            extinction+=stream*.7;
#endif
            transport(radiance,transmission,emission,extinction,ds);
        }
        if(max(transmission.x,max(transmission.y,transmission.z))<.0001) break;
    }
    float3 background=quietSky(rd)*.22;
    if(coreHit<1e4 && coreHit<donorHit) background=thermalRGB(22000)*(VARIANT==0?18:4);
#if VARIANT == 1
    if(donorHit<1e4 && donorHit<coreHit) {
        float3 n=normalize(ro+rd*donorHit-companion);
        float facing=saturate(dot(n,-rd));
        float irradiated=saturate(dot(n,-normalize(companion)));
        background=thermalRGB(6500+irradiated*2300)*(.35+.65*facing)*(.95+.05*fbm5(n*16));
    }
#endif
    return float4(min(radiance+transmission*background,32000),1);
}
