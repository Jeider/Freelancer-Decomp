"""Exercise the production physical-ring handler and shared snapshot manager."""
from pathlib import Path
import subprocess
import sys
import json
import hashlib

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cursors'))
from check import compiler_env,VC
OUT=ROOT/'src/obj/tradelane_server_check';OUT.mkdir(parents=True,exist_ok=True)
# Reuse the door manager's engine-boundary fixture, freshly regenerated from
# production. Physical lanes use this same tested manager and wire format.
subprocess.run([sys.executable,str(ROOT/'tools/doors/check.py')],cwd=ROOT,check=True)
fixture=(ROOT/'src/obj/doors/check/manager.cpp').read_text()
fixture=fixture[:fixture.index('int main(){')]
fixture=fixture.replace('bool automatic=true;', 'bool automatic=true, ring=false;')
fixture=fixture.replace('float get_radius(){return Radius;}', 'bool is_lane_ring(){return Archetype && Archetype->ring;} float get_radius(){return Radius;}')
fixture=fixture.replace('Vector const& get_position(){return pos;}', 'Vector const& get_position(){return pos;} Vector const& get_transform(){return pos;} int get_lane_direction(Vector const& p,bool* side){*side=p.z<0;return 0;}')
fixture+=r'''
bool SolarAnimation::GetRingConfig(Archetype::Root const* a,RingConfig& c){
 strcpy_s(c.Left,"open");strcpy_s(c.Right,"close");return a&&a->ring;
}
'''
fixture+=(ROOT/'src/Server/server_tradelane_physics.inl').read_text()
fixture+=r'''
int main(){
 StarSystem sys;world=&sys;SystemPlayerNode end{},player{};end.Next=&player;player.Next=&end;player.View.PlayerId=1;sys.PlayerListHead=&end;
 Archetype::Root arch;arch.automatic=false;arch.ring=true;CSolar raw;raw.Archetype=&arch;
 GameObject ring{&raw,101,{}},a{&raw,201,{0,0,100}},b{&raw,202,{0,0,-100}};
 Node rn{nullptr,&ring};sys.Solars.Head=&rn;objects={{101,&ring},{201,&a},{202,&b}};
 ActivatePhysicalTradeLane(&ring,true,201);assert(client.packets.size()==1);
 assert(!strcmp(client.packets.back().Animation.Name,"open"));
 ActivatePhysicalTradeLane(&ring,true,201);ActivatePhysicalTradeLane(&ring,true,202);assert(client.packets.size()==1);
 UpdateSolarAnimations(sys,1);SendSolarAnimations(sys,2);
 assert(client.packets.size()==2&&client.packets.back().Animation.Time==1&&client.packets.back().Animation.Sound==0);
 auto serial=client.packets.back().Animation.Serial;
 ActivatePhysicalTradeLane(&ring,false,201);ActivatePhysicalTradeLane(&ring,false,202);
 // Cancellation does not stop the full turn. New requests while playing do
 // not restart, and completion never starts a queued request.
 ActivatePhysicalTradeLane(&ring,true,202);assert(client.packets.size()==2);
 UpdateSolarAnimations(sys,8);ActivatePhysicalTradeLane(&ring,true,202);assert(client.packets.size()==2);
 ActivatePhysicalTradeLane(&ring,false,202);ActivatePhysicalTradeLane(&ring,true,202);
 assert(client.packets.size()==3&&!strcmp(client.packets.back().Animation.Name,"close"));
 assert(client.packets.back().Animation.Serial>serial);
 b.dead=true;UpdateSolarAnimations(sys,8);assert(Managers[&sys].Objects[101].RingUsers.empty());
 ActivatePhysicalTradeLane(&ring,true,201);assert(client.packets.size()==4);
 arch.ring=false;ActivatePhysicalTradeLane(&ring,true,201);assert(client.packets.size()==4);
 ring.dead=true;UpdateSolarAnimations(sys,.2f);assert(Managers[&sys].Objects.empty());
 ForgetSolarAnimations(sys);assert(Managers.empty());
 puts("PASS physical lanes: both directions, repeated/multiple ships, cancellation, no queue, timestamped late join, dead users, opt-in and cleanup");
}
'''
(OUT/'check.cpp').write_text(fixture)
subprocess.run([str(VC/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/EHsc','/MT','check.cpp','/Fecheck.exe'],cwd=OUT,env=compiler_env(),check=True)
subprocess.run([str(OUT/'check.exe')],check=True)
paths=[ROOT/p for p in ('src/Server/server_solar_animation.cpp','src/Server/server_tradelane_physics.inl',
    'src/Server/server_classes.cpp','src/include/server_solar_animation.h','src/include/solar_animation.h',
    'src/freelancer/Client/tradelane_ring_anim.cpp','tools/tradelane/check_server_physical.py')]
(OUT/'verified.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2))
