#define main ExistingTrainCheck
#include "../train_consist/check.cpp"
#undef main

int main(int argc,char** argv) {
    setvbuf(stdout,nullptr,_IONBF,0);SetUnhandledExceptionFilter(fault);
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    need(argc==2,"boarding model directory");
    need(DALib::Startup(nullptr,"check_dacom.ini"),"DALib startup");DALib::OpenData(argv[1]);
    PhySys::Startup(1);
    auto* arch=new Archetype::Solar;arch->DaArchetype.Value="train_boarding.cmp";
    arch->Mass=10000;arch->bPhantomPhysics=false;
    Archetype::EqObj::DockingSphere sphere;
    sphere.HardpointName="hpdockmounta";sphere.Radius=5;sphere.Type=0;
    arch->DockingSpheres.push_back(sphere);
    auto* solar=static_cast<CSolar*>(CObject::Alloc(CObject::ClassSolar));
    solar->CObject::open(arch);solar->Id=123;
    need(arch->is_loaded() && arch->create_instance(solar)!=-1,"real boarding CMP loads");
    // CEqObj inspect uses the same native HP loader for ships and solars.
    DockHandle inspect;inspect.Object=solar;
    Transform mount,inner,outer;
    need(inspect.get_dock_hardpoints(0,nullptr,&mount,&inner,&outer,nullptr)==0,"native docking lookup resolves all three HPs");
    need(outer.Translation.y>inner.Translation.y && inner.Translation.y>mount.Translation.y && mount.Translation.y>25,"approach descends to a mount above the locomotive");
    for(auto const* hp:{&mount,&inner,&outer}) {
        need(std::abs(hp->Translation.x)<.001 && std::abs(hp->Translation.z)<.001,"vertical approach is centered");
        for(int row=0;row<3;++row)for(int col=0;col<3;++col)
            need(std::abs(hp->Rotation.E[row][col]-(row==col?1.f:0.f))<.001,"miner berth keeps the ship horizontal");
    }
    need(std::abs(inner.Translation.y-mount.Translation.y-13)<.001 &&
         std::abs(outer.Translation.y-mount.Translation.y-58)<.001,"same approach lengths as Roid_Miner2");
    auto cam=anchor(solar,"HpDockCamA");
    need(std::abs(cam.x-45)<.001 && std::abs(cam.y-mount.Translation.y-78)<.001 &&
         std::abs(cam.z+75)<.001,"native camera hardpoint matches translated miner rig");
    // Headless test has no system database; supply the stationary solar's IVP
    // parameters directly instead of CSolar::init_physics reading ObjectDb.
    PhySys::CreateParms parms={};parms.Mass=10000;parms.CollisionGroupId=1;
    parms.Type=1;parms.bFlag1c=1;parms.bEnableCollisions=1;
    strcpy_s(parms.Name,"board");
    PhySys::BuildIVP_Real(solar,parms);
    need(solar->BodyPtr && solar->BodyPtr->core,"real CSolar creates a solid SUR body");
    PhySys::RayHit hits[8];
    need(PhySys::FindRayIntersect(solar,{-100,0,0},{100,0,0},hits,8)>0,"boarding locomotive hull blocks a ray");
    solar->Release();
    std::puts("PASS: real CSolar hull collision, native docking lookup, horizontal miner approach and camera");
}
