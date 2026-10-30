"""Exercise production gravity equipment definitions, registries and fixed-step forces."""
import os
from pathlib import Path
import subprocess
from check_gravity import ROOT, STUB, function

OUT=ROOT/'src/obj/gravity_devices_check'
CHECK=r'''
bool near(double a,double b){return std::fabs(a-b)<.0001;}
void Read(Archetype::Equipment& arch,std::initializer_list<std::pair<std::string,std::string>> values){
    INI_Reader reader;reader.lines=values;
    while(reader.read_value())assert(CmnGravity::ReadEquipmentValue(arch,reader));
}
void Mount(CEquip& eq,CEqObj& owner,Archetype::Equipment& arch,unsigned short id=1){
    eq.owner=&owner;eq.arch=&arch;eq.id=id;CmnGravity::RegisterEquipment(&eq);
}
int main(){
    SYSTEM system;IObjDB db{&system},clientDb{&system};int environment=1;
    IVP_Core core;core.Environment=&environment;core.MWorldFCore.vv.k[0]=5000;
    Body body{&core};CShip target;target.Id=2;target.ObjectDb=&clientDb;target.BodyPtr=&body;
    IVP_Core* array[]={&core};IVP_U_Vector<IVP_Core> cores;cores.elems=array;cores.n_elems=1;
    IVP_Event_Sim event;event.environment=&environment;
    auto sample=[&]{core.SpeedChange={};CmnGravity::Apply(target,&event,&cores);return core.SpeedChange.x;};
    Archetype::Equipment generator,repeller,compensator,compensator2,suppressor,child,unrelated;
    Read(generator,{{"gravity","true"},{"gravity_mode","attract"}});
    Read(repeller,{{"gravity","true"},{"gravity_mode","repel"}});
    Read(compensator,{{"gravity_compensation","0.7"}});
    Read(compensator2,{{"gravity_compensation","0.5"}});
    Read(suppressor,{{"gravity","true"},{"gravity_mode","suppress"},{"gravity_suppression","0.5"},{"gravity_radius","10000"}});
    INI_Reader unknown;unknown.lines={{"volume","1"}};unknown.read_value();
    assert(!CmnGravity::ReadEquipmentValue(unrelated,unknown)&&!Definitions().count(&unrelated));
    CmnGravity::CopyDefinition(child,generator);assert(Definitions().at(&child).source.enabled);
    Read(child,{{"gravity_mode","repel"}});assert(Definitions().at(&generator).source.field.mode==GravityField::Mode::Attract);
    CmnGravity::CopyDefinition(child,unrelated);assert(!Definitions().count(&child));
    CShip emitter;emitter.Id=1;emitter.ObjectDb=&db;
    CEquip source;Mount(source,emitter,generator);assert(source.active&&Devices().size()==1);
    assert(near(sample(),-1.5));
    source.active=false;assert(sample()==0);source.active=true;
    source.disabled=true;assert(sample()==0);source.disabled=false;
    source.destroyed=true;assert(sample()==0);source.destroyed=false;
    emitter.health=0;assert(sample()==0);emitter.health=1;
    emitter.WorldPosition.x=10000;assert(near(sample(),1.5));emitter.WorldPosition.x=0;
    // A moving authoritative source uses physics position, not render interpolation.
    IVP_Core emitterCore;Body emitterBody{&emitterCore};emitter.BodyPtr=&emitterBody;
    emitterCore.MWorldFCore.vv.k[0]=10000;assert(near(sample(),1.5));
    emitterCore.MWorldFCore.vv.k[0]=0;assert(near(sample(),-1.5));
    source.owner=&target;assert(sample()==0);source.owner=&emitter;
    target.PhysicsSystemId=2;assert(sample()==0);target.PhysicsSystemId=1;
    CmnGravity::UnregisterEquipment(&source);Mount(source,emitter,repeller);assert(near(sample(),1.5));
    // Installed compensators use the strongest device, not summed immunity.
    CEquip shield,shield2;Mount(shield,target,compensator,2);Mount(shield2,target,compensator2,3);
    assert(near(sample(),.45));shield.active=false;assert(near(sample(),.75));shield.active=true;
    CmnGravity::UnregisterEquipment(&shield);CmnGravity::UnregisterEquipment(&shield2);
    // Cargo never grants protection or creates a field, including a loaded save.
    CEquip cargo;cargo.type=EquipTypeCargo;Mount(cargo,target,compensator,4);assert(Devices().size()==1&&near(sample(),1.5));
    // Cargo emitters, repulsors and suppressors are inert even if explicitly activated.
    for(auto* arch:{&generator,&repeller,&suppressor,&compensator}){
        cargo.active=true;Mount(cargo,target,*arch,4);
        assert(Devices().size()==1&&near(sample(),1.5));
    }
    CEquip transition;Mount(transition,target,compensator,6);assert(near(sample(),.45));
    transition.type=EquipTypeCargo;Mount(transition,target,compensator,6);
    assert(Devices().size()==1&&near(sample(),1.5));
    // Duplicate SP server/client emitter copies do not double the force.
    CShip remote;remote.Id=emitter.Id;remote.ObjectDb=&clientDb;
    IVP_Core remoteCore;remoteCore.Flags=0x300;Body remoteBody{&remoteCore};remote.BodyPtr=&remoteBody;
    CEquip remoteSource;Mount(remoteSource,remote,repeller);assert(near(sample(),1.5));
    CmnGravity::UnregisterEquipment(&source);assert(near(sample(),1.5)); // remote-only MP representation
    CmnGravity::UnregisterEquipment(&remoteSource);assert(sample()==0);
    // Mission solars use the same mounted-loadout route, with no system Object entry.
    CSolar solar;solar.Id=10;solar.ObjectDb=&db;Mount(source,solar,generator);assert(near(sample(),-1.5));
    CEquip bubble;Mount(bubble,target,suppressor,5);assert(near(sample(),-.75));
    Mount(shield,target,compensator,2);assert(near(sample(),-.225));
    CmnGravity::UnregisterEquipment(&shield);
    // Suppression fades smoothly and also affects configured static sources.
    bubble.owner=&emitter;core.MWorldFCore.vv.k[0]=9000;
    double withBubble=sample();bubble.active=false;double withoutBubble=sample();
    assert(near(withBubble,withoutBubble*.75));bubble.active=true;
    core.MWorldFCore.vv.k[0]=10000;withBubble=sample();bubble.active=false;assert(near(withBubble,sample()));
    CmnGravity::UnregisterEquipment(&bubble);CmnGravity::UnregisterEquipment(&source);
    core.MWorldFCore.vv.k[0]=5000;
    system.GravityObjects[11]=GravityField::Settings{};solar.Nickname.Id=11;
    CmnGravity::RegisterSolar(&solar);assert(near(sample(),-1.5));
    Read(compensator,{{"gravity_compensation","1"}});Mount(shield,target,compensator,2);assert(sample()==0);
    // Simulate unload/reload of ordinary mounted equipment descriptors.
    CmnGravity::UnregisterEquipment(&shield);assert(near(sample(),-1.5));
    Mount(shield,target,compensator,2);Mount(shield,target,compensator,2);assert(Devices().size()==1&&sample()==0);
    CmnGravity::UnregisterEquipment(&shield);CmnGravity::UnregisterSolar(&solar);
    Read(child,{{"gravity_compensation","nan"},{"gravity","true"},{"gravity_mode","repel"},{"gravity_suppression","2"}});
    assert(Definitions().at(&child).compensation==0&&Definitions().at(&child).source.field.suppression==1);
    CmnGravity::ForgetDefinition(&child);assert(!Definitions().count(&child));
    puts("PASS: installed/cargo distinction, autoactivation, disable/death/unmount/reload, moving NPC and mission solar sources, repel, personal compensation, suppression, SP duplicates, remote emitters, INI inheritance and limits");
}
'''
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    production=(ROOT/'src/Common/common_gravity.cpp').read_text()
    production='\n'.join(line for line in production.splitlines() if not line.startswith('#include'))
    (OUT/'check.cpp').write_text(STUB+production+CHECK)
    vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
    sdk=Path('C:/Program Files (x86)/Windows Kits/10');v='10.0.26100.0'
    env=dict(os.environ)
    env['INCLUDE']=';'.join(map(str,[vc/'include',ROOT/'src/Common']+[sdk/'Include'/v/x for x in ('ucrt','shared','um')]))
    env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/v/x/'x86' for x in ('ucrt','um')]))
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc','/MT','check.cpp','/Fecheck.exe'],cwd=OUT,env=env,check=True)
    subprocess.run([str(OUT/'check.exe')],cwd=OUT,check=True)
if __name__=='__main__':main()
