// Schwarzschild null geodesics, r_s = 1. Source equations and limitations in
// docs/space_anomalies/realistic.md. Numerical RK4, not a radial screen warp.
float2 geodesicRhs(float2 uw) {return float2(uw.y,-uw.x+1.5*uw.x*uw.x);}
float2 geodesicStep(float2 uw,float step) {
    float2 a=geodesicRhs(uw),b=geodesicRhs(uw+a*(step*.5));
    float2 c=geodesicRhs(uw+b*(step*.5)),d=geodesicRhs(uw+c*step);
    return uw+(a+2*b+2*c+d)*(step/6);
}
float3 orbitalRadial(float3 radial,float3 tangent,float phi) {
    float s,c;sincos(phi,s,c);return radial*c+tangent*s;
}
float3 diskRadiance(float3 p,float lambda,float observerRadius,int style) {
    float r=max(length(p.xz),3.001),angle=atan2(p.z,p.x);
    float omega=sqrt(.5/(r*r*r));
    float advected=angle+Frame.x*omega*.65;
    float3 orbit=float3(cos(advected)*r,p.y,sin(advected)*r);
    float coarse=fbm5(orbit*.35);
    float fine=noise(orbit*4+float3(7,0,11));
    // Nonuniform sheared filaments instead of a stack of regular neon rings.
    float filament=pow(saturate(.5+.5*sin(r*18+advected*3+coarse*18)),5);
    float temperatureProfile=pow(abs(3/r),.75)*pow(max(1-sqrt(3/r),.000001),.25)/.488;
    float peak=style==1?5250:14500;
    float shift=sqrt(max(1-1.5/r,.001))/
        (sqrt(max(1-1/observerRadius,.001))*max(1-omega*lambda,.08));
    float temperature=peak*temperatureProfile*shift*(.94+.12*coarse);
    float outer=1-smoothstep(style==1?8.0:9.0,style==1?10.0:11.0,r);
    return thermalRGB(temperature)*outer*(.12+1.5*coarse*coarse+.7*filament+.08*fine);
}
float3 traceSchwarzschild(float3 ro,float3 rd,int style) {
    float observerRadius=length(ro);
    float3 radial=ro/observerRadius;
    float cosine=dot(rd,radial);
    float3 tangent=rd-radial*cosine;
    float sine=length(tangent);
    if(sine<1e-6) return cosine<0?float3(0,0,0):quietSky(rd);
    tangent/=sine;
    float impact=observerRadius*sine/sqrt(max(1-1/observerRadius,.0001));
    // Reverse-traced momentum has the opposite sign to the emitted photon.
    float lambda=-impact*cross(radial,tangent).y;
    float2 uw=float2(1/observerRadius,-cosine/impact);
    float phi=0;
    float3 position=ro,escapedDirection=rd,photosphere=0;
    // Float state avoids legacy fxc boolean/break lowering through nested loops.
    // 0=integrating, 1=escaped, 2=captured, 3=opaque photosphere.
    float state=0;
    [loop] for(int batch=0;batch<GR_PASSES && state==0;++batch) {
        [loop] for(int iteration=0;iteration<128 && state==0;++iteration) {
            float2 next=geodesicStep(uw,GR_STEP);
            if(next.x<=.00001) {
                float fraction=saturate(uw.x/max(uw.x-next.x,.000001));
                escapedDirection=orbitalRadial(radial,tangent,phi+GR_STEP*fraction);
                state=1;
            }
            else if(next.x>=1) {state=2;}
            else {
            float nextPhi=phi+GR_STEP;
            float3 nextPosition=orbitalRadial(radial,tangent,nextPhi)/next.x;
            if(style!=0) {
                // Optically thick, geometrically thin photosphere. Defer its
                // expensive radiance evaluation until after geodesic integration:
                // keeping noise/Planck temporaries live here exceeds SM3 registers.
                // Higher-order disk images still follow from the same geodesics.
                float directionY=nextPosition.y-position.y;
                {
                    float crossing=-position.y/(abs(directionY)<1e-7?1e-7:directionY);
                    if(crossing>=0 && crossing<1 && abs(directionY)>1e-7) {
                        float3 hitPoint=lerp(position,nextPosition,crossing);
                        float r=length(hitPoint.xz);
                        if(r>3.001 && r<11) {
                            photosphere=hitPoint;state=3;
                        }
                    }
                }
            }
            position=nextPosition;uw=next;phi=nextPhi;
            }
        }
    }
    // Unresolved near-critical rays end dark; they never fabricate an escape.
    if(style!=0 && state>2.5) return diskRadiance(photosphere,lambda,observerRadius,style);
    return (state>.5 && state<1.5)?quietSky(escapedDirection):0;
}
