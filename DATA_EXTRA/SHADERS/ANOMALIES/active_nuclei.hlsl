#include "common.hlsli"
#ifndef VARIANT
#define VARIANT 0
#endif
float4 PSMain(PixelIn input) : COLOR0 {
    float3 ro,rd; camera(input.uv,ro,rd);
    float3 light=0; float tr=1;
    float start=max(0,-dot(ro,rd)-4.8);
    float companionHit=1e5;
#if VARIANT == 1
    float3 companion=float3(2.6,.15,0);
    companionHit=sphereHit(ro-companion,rd,.52);
#endif
    [loop] for(int i=0;i<164;++i) {
        float t=start+(i+.5)*.06;
        if(t>companionHit) break;
        float3 p=ro+rd*t;
        float r=length(p),radial=length(p.xz),y=abs(p.y);
        float env=1-smoothstep(3.8,4.65,r);
        float a=atan2(p.z,p.x)+Frame.x*.6/pow(max(radial,.4),1.5);
        float3 q=float3(cos(a)*radial,p.y,sin(a)*radial);
        float n=turbulence(q*7);
        float disc=gaussian(p.y/.09)*smoothstep(.18,.4,radial)*(1-smoothstep(1.1,1.7,radial));
        float bands=.28+.72*pow(.5+.5*sin(radial*65+a*3+n*8),2);
        float3 col=float3(1.65,.55,.10)*(.5+n)*bands;
        float dens=disc*(1+n*2)*4;
        // Ionized bipolar jet: slow precession + moving internal shocks.
        float2 center=float2(sin(y*2-Frame.x*.6),cos(y*2-Frame.x*.6))*.055*y;
        float jetRadius=length(p.xz-center);
        float width=.055+y*.055;
        float twist=atan2(p.z-center.y,p.x-center.x)*3-y*7+Frame.x*1.8;
        float filament=pow(.5+.5*cos(twist),8)*gaussian((jetRadius-width*1.9)/(width*.27));
        float jet=(exp(-jetRadius*jetRadius/(width*width))+filament*.4)*smoothstep(.15,.4,y)*env;
        float shock=.7+.3*sin(y*15-Frame.x*5);
        float jetDens=jet*(.5+shock)*(.3+noise(p*16-float3(0,Frame.x,0)))*2;
        float3 emission=col*dens+float3(.12,.65,2.2)*jetDens*2;
        dens+=jetDens;
        // Unresolved brilliant nucleus; intentional compressed spatial scale.
        float nucleus=gaussian(r/.19)*9;
        emission+=float3(5,4,3)*nucleus; dens+=nucleus;
#if VARIANT == 0
        // Dust torus absorbs the far jet/disk and scatters warm light.
        float torus=gaussian((radial-1.9)/.68)*gaussian(p.y/.42)*(n*.8+.2)*2.8;
        emission+=float3(.15,.045,.012)*torus*(.15+pow(n*1.4,3));
        dens+=torus;
        // Decorative circumnuclear spiral, deliberately visible in optical light.
        float arms=pow(.5+.5*sin(a*3-radial*4+n*4),4);
        float galaxy=gaussian(p.y/.20)*smoothstep(1.8,2.5,radial)*(1-smoothstep(3.3,4.2,radial));
        galaxy*=arms*(.15+n)*.48;
        emission+=lerp(float3(.22,.10,.75),float3(.5,.65,1.4),n)*galaxy;
        dens+=galaxy;
#else
        // Roche stream, an artistic curved bridge from the companion to disk.
        float streamZ=.42*sin(saturate((p.x-.65)/1.95)*PI);
        float stream=gaussian(length(float2(p.y-.1,p.z-streamZ))/.065);
        stream*=smoothstep(.65,.9,p.x)*(1-smoothstep(2.2,2.65,p.x));
        emission+=float3(3,.65,.15)*stream*3; dens+=stream*1.4;
#endif
        integrate(light,tr,emission/max(dens,.0001),dens,.06);
        if(tr<.003) break;
    }
    float3 back=sky(rd);
#if VARIANT == 1
    if(companionHit<1e4) {
        float3 n=normalize(ro+rd*companionHit-companion);
        back=float3(2.7,.75,.15)*(1+.45*noise(n*14+Frame.x*.1))*(.4+.6*saturate(dot(n,-rd)));
    }
#endif
    return float4(light+tr*back,1);
}
