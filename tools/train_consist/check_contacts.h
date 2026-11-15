#pragma once
#include "../../src/Common/train_contact_math.h"
static void checkSoftContacts() {
    using namespace TrainJoint;
    Body b[5];for(auto& x:b){x.inverseMass=1.0/250;x.inverseInertia={1e-5,1e-5,1e-5};}
    std::vector<Contact> contacts;
    for(int i=1;i<5;++i)b[i].position={0,0,25.37+(i-1)*43.44};
    trainContacts(b,4,1./16,true,contacts);need(contacts.empty(),"straight train has no side repulsion");
    // Nearby neighbours are left to the couplings, not forced apart by envelopes.
    b[0].position={1000,0,0};b[1].position={0,0,0};b[2].position={5,0,0};
    trainContacts(b,2,1./16,true,contacts);need(contacts.empty(),"neighbouring wagons may articulate");
    b[3].position={10,0,0};
    trainContacts(b,3,1./16,true,contacts);need(!contacts.empty(),"folded non-neighbouring wagons contact");
    for(auto& c:contacts) {need(c.a==1 && c.b==3,"only the crossing non-neighbour pair contacts");solveContact(b,c);}
    need(b[1].velocity.x<0 && b[3].velocity.x>0,"side contact pushes both wagons apart");
    need((b[1].velocity+b[3].velocity).length()<1e-8,"side contact conserves linear momentum");
    for(double dt:{1./16,1./60,1./144}) {
        Body pair[2];for(auto& x:pair){x.inverseMass=1.0/250;x.inverseInertia={};}
        pair[1].position={10,0,0};
        for(int step=0;step<int(4/dt);++step) {
            contacts.clear();
            addContact(pair,0,1,{{0,0,0},{0,0,20},8},{{0,0,0},{0,0,20},8},dt,contacts);
            for(auto& c:contacts)solveContact(pair,c);
            for(auto& x:pair){need(x.velocity.length()<1.1,"pre-existing overlap separates without launch");x.position=x.position+x.velocity*dt;}
        }
        need((pair[1].position-pair[0].position).length()>15,"overlap recovers at different frame rates");
    }
    for(int side:{-1,1}) {
        Body pair[2];for(auto& x:pair){x.inverseMass=1.0/250;x.inverseInertia={1e-5,1e-5,1e-5};}
        pair[1].position={side*28.,-17.05,-40};
        trainContacts(pair,1,1./16,true,contacts);
        need(!contacts.empty(),"engine nacelle has a separation zone on each side");
        for(auto& c:contacts)solveContact(pair,c);
        need(pair[1].velocity.x*side>0,"engine zone pushes wagon away from the nacelle");
    }
    // A positive gap may brake an approaching wagon but cannot pull it in.
    Body pair[2];for(auto& x:pair){x.inverseMass=1.0/250;x.inverseInertia={};}
    pair[1].position={18,0,0};pair[1].velocity={-60,0,0};contacts.clear();
    addContact(pair,0,1,{{0,0,0},{0,0,20},8},{{0,0,0},{0,0,20},8},1./16,contacts);
    need(!contacts.empty(),"fast closing motion gets speculative contact");
    for(auto& c:contacts)solveContact(pair,c);
    need((pair[1].velocity-pair[0].velocity).x>=-32.001,"contact brakes before penetration");
    // Two overlapping loops, with couplings active: separation must coexist
    // with the joint solver rather than tearing the consist apart.
    Body folded[13];Joint links[12];
    for(int i=0;i<13;++i) {
        auto& x=folded[i];x.inverseMass=1.0/(i?250:500);x.inverseInertia={1e-5,1e-5,1e-5};
        double angle=i*.7853981633974483;
        x.rotation.axes[0]={std::cos(angle),0,-std::sin(angle)};
        x.rotation.axes[2]={std::sin(angle),0,std::cos(angle)};x.inertiaAxes=x.rotation;
        if(i) {
            auto& j=links[i-1];j.a=i-1;j.b=i;j.anchorA={-.1,1.696,i==1?25.1456:43.21455};j.anchorB={-.1,1.696,-.22488};
            x.position=worldPoint(folded[i-1],j.anchorA)-x.rotation.mul(j.anchorB);
        }
    }
    double maxGap=0,maxSpeed=0;int active=0;
    for(int step=0;step<16*6;++step) {
        trainContacts(folded,12,1./16,true,contacts);active+=(int)contacts.size();
        solve(folded,links,12,1./16,true,contacts.data(),(int)contacts.size());
        for(auto& x:folded) {
            maxSpeed=(std::max)(maxSpeed,x.velocity.length());
            x.position=x.position+x.velocity*(1./16);
            const double w=x.omega.length();
            if(w>1e-8){V axis=x.omega*(1/w);double angle=w/16;
                for(auto& v:x.rotation.axes)v=v*std::cos(angle)+axis.cross(v)*std::sin(angle)+axis*(axis.dot(v)*(1-std::cos(angle)));}
            x.inertiaAxes=x.rotation;
            x.velocity=x.velocity*.98;x.omega=x.omega*.98;
        }
        for(auto& j:links)maxGap=(std::max)(maxGap,(worldPoint(folded[j.a],j.anchorA)-worldPoint(folded[j.b],j.anchorB)).length());
    }
    printf("Folded contact/joint solve: contacts %d, max speed %.3f, max pin gap %.3f\n",active,maxSpeed,maxGap);
    need(active>0 && maxSpeed<30 && maxGap<1,"folded recovery keeps bounded speeds and connected pins");
    puts("PASS soft sides: straight/adjacent exclusions, folded wagons, engines, bounded recovery and swept approach");
}
