#include "common.hlsli"
#ifndef VARIANT
#define VARIANT 0
#endif

float3 magneticSpace(float3 p) {
    // Magnetic axis tilted 0.53 rad from the spin axis; full 3D precession.
    return rotateX(rotateY(p,-Frame.x*.64),.53);
}
float4 PSMain(PixelIn input) : COLOR0 {
    float3 ro,rd; camera(input.uv,ro,rd);
    float hit=sphereHit(ro,rd,.46);
    float3 light=0; float tr=1;
    float start=max(0,-dot(ro,rd)-4.5);
    [loop] for(int i=0;i<144;++i) {
        float t=start+(i+.5)*.063;
        if(t>hit) break;
        float3 p=ro+rd*t,q=magneticSpace(p);
        float r=length(q),rho=length(q.xz);
        float envelope=1-smoothstep(3.25,4.1,r);
        if(r>.47 && r<4.1) {
#if VARIANT == 0
            float y=abs(q.y),width=.035+y*.075;
            float cone=exp(-rho*rho/(width*width));
            float knots=.65+.35*sin(y*12-Frame.x*6);
            float dens=cone*envelope*1.7*(.5+noise(q*12-float3(0,Frame.x,0)));
            float3 col=float3(.14,.9,3.4)*(1+knots);
            // Faint hollow sheath makes the cones read as volumes.
            float corkscrew=pow(.5+.5*cos(atan2(q.z,q.x)*3-y*9+Frame.x*2),6);
            dens+=gaussian((rho-width*1.6)/max(.02,width*.2))*envelope*corkscrew*.65;
            // An equatorial wind sheet makes this more than two plain cones.
            float wind=gaussian(q.y/.13)*gaussian((rho-1.1)/.5)*(.3+noise(q*15))*.13;
            dens+=wind;
#else
            // Dipole field lines satisfy r = L sin(theta)^2.
            // Discrete L shells and azimuth windows turn them into spatial arcs.
            float s2=max(.015,rho*rho/(r*r));
            float L=r/s2;
            float az=atan2(q.z,q.x);
            float shell=abs(frac((L-.9)*1.6+.5)-.5)/1.6*s2;
            float meridian=pow(.5+.5*cos(az*7+sin(L*1.7)*.2),14);
            float arcs=gaussian(shell/.04)*meridian*(1-smoothstep(3.2,3.5,L))*smoothstep(.65,.85,L);
            float moving=.55+.45*sin(r*14+az*3-Frame.x*3.5);
            float dens=arcs*envelope*smoothstep(.5,.7,r)*2.1;
            float3 col=lerp(float3(1.7,.08,3.8),float3(.12,2.4,3.8),moving)*(1+Event.x*2);
            // A flare heats existing loops; its expanding shell is an artistic cue.
            float shellRadius=.65+frac(Frame.x*.16)*3.2;
            float flare=Event.x*gaussian((r-shellRadius)/.09)*envelope;
            dens+=flare*.7;
#endif
            integrate(light,tr,col,dens,.063);
        }
    }
    float3 back=sky(rd);
    if(hit<1e4) {
        float3 p=ro+rd*hit,q=magneticSpace(p);
        float grain=noise(q*22+Frame.x*.1);
        float limb=pow(saturate(dot(normalize(p),-rd)),.4);
        float caps=pow(abs(q.y)/.46,12);
        back=float3(1.0,1.8,2.7)*(1.0+grain*1.1)*(.35+.65*limb)+caps*float3(2,3,5);
    }
    // Broad, restrained coronal emission. The sphere still occludes rear arcs.
    float impact=length(cross(ro,rd));
    light+=float3(.025,.15,.36)*exp(-impact*impact*1.4);
    return float4(light+tr*back,1);
}
