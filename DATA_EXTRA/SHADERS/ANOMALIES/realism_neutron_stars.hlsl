#include "realism_common.hlsli"
#ifndef VARIANT
#define VARIANT 0
#endif
float3 magneticFrame(float3 p) {return rotateX(rotateY(p,-Frame.x*.38),.48);}
float magnetarLoop(float3 q,float L,float azimuth) {
    float r=max(length(q),.001),rho=length(q.xz);
    float shell=r-L*rho*rho/(r*r);
    float meridian=dot(q.xz/max(rho,.0001),float2(cos(azimuth),sin(azimuth)));
    shell+=.007*sin(q.y*27+Frame.x*.4)*sin(q.x*19);
    return gaussian(shell/(.012+.009*r))*pow(saturate(meridian),96)*
        smoothstep(.58,.72,r)*(1-smoothstep(L*.92,L,r));
}
float4 PSMain(PixelIn input) : COLOR0 {
    float3 ro,rd;camera(input.uv,ro,rd);
    float surfaceRadius=VARIANT==0?.24:.48;
    float apparentRadius=surfaceRadius/sqrt(1-.35);
    float hit=sphereHit(ro,rd,apparentRadius);
    float extent=VARIANT==0?7.0:4.5;
    float2 interval=volumeInterval(ro,rd,extent);
    interval.y=min(interval.y,hit);
    if(interval.y<=interval.x) return float4(quietSky(rd),1);
    float ds=max(interval.y-interval.x,0)/(VOLUME_PASSES*128);
    float3 radiance=0,transmission=1;
    [loop] for(int batch=0;batch<VOLUME_PASSES;++batch) {
        [loop] for(int k=0;k<128;++k) {
            float t=interval.x+(batch*128+k+.5)*ds;
            float3 p=ro+rd*t,q=magneticFrame(p);
            float r=length(q),rho=length(q.xz),height=abs(q.y);
            float envelope=1-smoothstep(extent*.76,extent,r);
            float density=0;float3 colour=float3(.7,.82,1);
#if VARIANT == 0
            float width=.028+height*.068;
            float spine=gaussian(rho/max(width,.001));
            float edge=gaussian((rho-width*1.65)/max(width*.32,.012));
            float3 flow=q*float3(8,1.6,8)-float3(0,Frame.x*.6,0);
            float eddies=fbm5(flow);
            float shocks=.3+1.4*pow(noise(float3(height*1.3-Frame.x*.3,4,8)),3);
            density=(spine*.42+edge*.16)*(.3+eddies)*shocks*envelope*smoothstep(.28,.48,height);
            // Brightness is angle dependent; emission beams are a documented
            // sensor composite when Event.y=1, not visible radio light in vacuum.
            float toward=dot(normalize(magneticFrame(-rd)),float3(0,q.y<0?-1:1,0));
            float beaming=clamp(pow(.65/max(1-.72*toward,.15),3),.1,14);
            colour*=lerp(.075,38.0,saturate(Event.y))*beaming;
            density+=gaussian(q.y/.09)*gaussian((rho-1.0)/.25)*.018*Event.y;
#else
            float loops=magnetarLoop(q,1.55,.35)+magnetarLoop(q,2.25,2.8)*.65+
                magnetarLoop(q,1.85,-1.6)*.4;
            float moving=.2+1.3*pow(noise(q*6-float3(0,Frame.x*.5,0)),2);
            density=loops*moving*envelope*lerp(.035,.5,saturate(Event.y));
            colour=thermalRGB(15000)*(.12+Event.x*.9)*lerp(1,24,saturate(Event.y));
            float3 eruptionAxis=normalize(float3(.3,.85,-.42));
            float forward=dot(q,eruptionAxis);
            float cone=gaussian(length(q-eruptionAxis*forward)/max(.06+forward*.12,.03));
            float ejecta=cone*smoothstep(.5,.8,forward)*envelope*Event.x*fbm5(q*8-Frame.x*.8);
            density+=ejecta*.7;
#endif
            transport(radiance,transmission,colour*density,density*.07,ds);
        }
    }
    float3 background=quietSky(rd);
    if(hit<1e4) {
        float3 n=normalize(ro+rd*hit),view=normalize(ro);
        float mu=saturate(dot(n,view));
        // Approximate compact-star light bending exposes some far-side caps.
        float emittingCosine=clamp((mu-.35)/.65,-1,1);
        float3 along=n-view*dot(n,view);
        along/=max(length(along),.0001);
        float3 emittingNormal=view*emittingCosine+along*sqrt(max(0,1-emittingCosine*emittingCosine));
        float3 magnetic=magneticFrame(emittingNormal);
        float caps=pow(saturate(abs(magnetic.y)),24);
        float mottling=.94+.06*fbm5(magnetic*18);
        background=thermalRGB(18000)*mottling*(.35+.65*mu)*(1+caps*2.2);
        background*=1+Event.x*6;
    }
    return float4(min(radiance+transmission*background,32000),1);
}
