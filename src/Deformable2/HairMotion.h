#pragma once
#include <cmath>
#include <algorithm>

// Six virtual strand joints, applied in bind space before ordinary skinning.
// No shared mesh mutation and no extra skeleton slots or draw calls.
namespace HairMotion {
inline float clamp(float v,float a,float b){return (std::max)(a,(std::min)(v,b));}
struct State {
    bool ready=false;
    double last=0;
    float rotation[9]={};
    float angle[6][2]={},velocity[6][2]={};
    void reset(double now,const float* pose){
        ready=true;last=now;
        for(int i=0;i<9;++i)rotation[i]=pose[i];
        for(int g=0;g<6;++g)for(int a=0;a<2;++a)angle[g][a]=velocity[g][a]=0;
    }
    void update(double now,const float* pose){
        if(!ready || now<last || now-last>.25){reset(now,pose);return;}
        double elapsed=now-last;
        if(elapsed<1./120.)return; // Reuse the pose for adjacent shadow/colour submissions.
        float dt=(float)elapsed;
        // Small relative rotation from orthonormal frame cross products.
        float spinX=0,spinY=0,spinZ=0,change=0;
        for(int row=0;row<3;++row){
            int k=row*3;
            spinX+=rotation[k+1]*pose[k+2]-rotation[k+2]*pose[k+1];
            spinY+=rotation[k+2]*pose[k]-rotation[k]*pose[k+2];
            spinZ+=rotation[k]*pose[k+1]-rotation[k+1]*pose[k];
            for(int j=0;j<3;++j)change+=std::fabs(rotation[k+j]-pose[k+j]);
        }
        if(change>2.5f){reset(now,pose);return;} // Teleport, cut or abrupt pose replacement.
        float impulse[2]={clamp((-spinZ-spinY*.7f)*.5f/dt,-5.f,5.f),clamp(spinX*.5f/dt,-5.f,5.f)};
        int steps=(std::max)(1,(int)std::ceil(dt*120));float h=dt/steps;
        for(int step=0;step<steps;++step){
            double time=last+(step+1)*h;
            for(int g=0;g<6;++g)for(int a=0;a<2;++a){
                // Sub-millimetre rest motion; no scrolling UVs or uniform sine wave.
                float idle=.004f*(float)std::sin(time*(1.35+.07*g)+g*1.7+a*2.1)
                          +.002f*(float)std::sin(time*2.23+g*.9-a);
                float target=idle+impulse[a]*.009f*(.8f+.08f*g);
                float acceleration=95.f*(target-angle[g][a])-18.f*velocity[g][a];
                velocity[g][a]+=acceleration*h;
                angle[g][a]+=velocity[g][a]*h;
                if(std::fabs(angle[g][a])>.04f){angle[g][a]=clamp(angle[g][a],-.04f,.04f);velocity[g][a]=0;}
            }
        }
        for(int i=0;i<9;++i)rotation[i]=pose[i];last=now;
    }
    void deform(const float* source,float weight,float* out) const {
        for(int i=0;i<6;++i)out[i]=source[i];
        if(weight<=0 || !ready)return;
        float azimuth=std::atan2(source[0],source[2])*(3.f/3.14159265359f)+3.f;
        int first=(int)std::floor(azimuth);float blend=azimuth-first;
        first=first%6;int second=(first+1)%6;
        blend=blend*blend*(3-2*blend);
        float x=angle[first][0]*(1-blend)+angle[second][0]*blend;
        float z=angle[first][1]*(1-blend)+angle[second][1]*blend;
        float length=(std::max)(0.f,source[1]-.065f);
        out[0]+=x*length*weight;out[2]+=z*length*weight;
        // Bend the normal with the strand, avoiding a stationary lighting pattern.
        out[3]=source[3]+x*source[4]*weight;
        out[4]=source[4]-(x*source[3]+z*source[5])*weight;
        out[5]=source[5]+z*source[4]*weight;
        float inv=1.f/std::sqrt((std::max)(1e-12f,out[3]*out[3]+out[4]*out[4]+out[5]*out[5]));
        for(int i=3;i<6;++i)out[i]*=inv;
    }
};
}
