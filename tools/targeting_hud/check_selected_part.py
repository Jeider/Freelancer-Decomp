"""Exercise live world selection and cruiser/gunboat toolbar eligibility."""
import check_world_input as world

stub = world.stub + r'''
struct FSpaceCamera:ICamera {};
ICamera* AsCamera(FSpaceCamera* p){return p;}
void DrawPartWire(FSpaceCamera*,Hover const& part,WireState& cache){cache.drawn=part;}
struct HudTarget {IObjRW* ViewObject=nullptr;bool TargetingShowsAutoselect() const;};
IObjRW* WatchedObjRw(IObjRW* p){return p;}
CObject* CObjectOfObjRw(IObjRW* p){return p?p->ship:nullptr;}
bool IsClass(CObject* p,unsigned mask){return (p->ObjectClass&mask)==mask;}
'''
checks = r'''
int main(){
    Arch arch;CArchGroup group;group.Arch=&arch;CShip a,b;
    a.ArchGroups.group=b.ArchGroups.group=&group;
    IObjRW ar{&a},br{&b};test_playerShip.target=&ar;test_playerShip.selectedSub=0x8002;
    CEScanner scanner;test_playerShip.EquipManager.scanner=&scanner;
    FSpaceCamera scene;
    // Selection survives an empty cursor ray, UI hover and mouse-flight picking lock.
    for(int frame=0;frame<100;++frame){
        ui=(frame%2)==0;blocked=(frame%3)==0;
        VulnerableTargetingDraw(&scene);
        assert(selectedState.drawn.object==&a&&selectedState.drawn.subId==0x8002);
    }
    ui=blocked=false;
    nextHit.Object=&b;nextHit.Instance=42;nextHit.Point.z=100;
    VulnerableTargetingDraw(&scene);
    assert(selectedState.drawn.object==&a&&state.drawn.object==&b);
    nextHit.Object=&a;VulnerableTargetingDraw(&scene);
    assert(selectedState.drawn.object==&a&&!state.drawn.object); // Same part drawn once.
    nextHit.Object=nullptr;
    for(unsigned type:{0x80000u,0x40000u}) {
        a.TypeBits=type;contact.attitude=-1;
        VulnerableTargetingDraw(&scene);assert(selectedState.drawn.object==&a);
        for(float attitude:{0.f,1.f}) {
            contact.attitude=attitude;VulnerableTargetingDraw(&scene);assert(!selectedState.drawn.object);
            assert(test_playerShip.target==&ar&&test_playerShip.selectedSub==0x8002);
        }
        contact.attitude=-1;VulnerableTargetingDraw(&scene);assert(selectedState.drawn.object==&a);
    }
    test_playerShip.target=&br;VulnerableTargetingDraw(&scene);
    assert(selectedState.drawn.object==&b);
    test_playerShip.selectedSub=0;VulnerableTargetingDraw(&scene);assert(!selectedState.drawn.object);
    test_playerShip.selectedSub=0x8002;
    for(int kind=0;kind<9;++kind){
        group.State=1;group.HitPts=100;group.root=42;arch.bVulnerable=true;
        b.CloakPercent=0;b.center.z=100;b.centerValid=true;test_playerShip.target=&br;activePlayer=&test_player;
        switch(kind){case 0:group.State=0;break;case 1:group.HitPts=0;break;
        case 2:group.root=-1;break;case 3:arch.bVulnerable=false;break;
        case 4:b.CloakPercent=1;break;case 5:b.center.z=3000;break;
        case 6:b.centerValid=false;break;case 7:test_playerShip.target=nullptr;break;
        case 8:activePlayer=nullptr;break;}
        VulnerableTargetingDraw(&scene);assert(!selectedState.drawn.object);
    }
    activePlayer=&test_player;test_playerShip.target=&br;
    GunArchData gunArch;CEGun turret;turret.arch=&gunArch;turret.owner=&b;
    b.CEqObj::EquipManager.gun=&turret;test_playerShip.selectedSub=18;
    VulnerableTargetingDraw(&scene);assert(selectedState.drawn.turret==&turret);
    turret.destroyed=true;VulnerableTargetingDraw(&scene);assert(!selectedState.drawn.object);
    turret.destroyed=false;turret.connected=false;
    VulnerableTargetingDraw(&scene);assert(!selectedState.drawn.object);turret.connected=true;
    for(bool* gate:{&G_bNnScreenUp,&paused,&transition,&letterbox,&loading,&focus}){
        *gate=true;VulnerableTargetingDraw(&scene);assert(!selectedState.drawn.object);*gate=false;
    }
    foreground=false;VulnerableTargetingDraw(&scene);assert(!selectedState.drawn.object);foreground=true;
    hud=false;VulnerableTargetingDraw(&scene);assert(!selectedState.drawn.object);hud=true;
    SetVulnerableAutoselect(false);VulnerableTargetingDraw(&scene);assert(!selectedState.drawn.object);
    assert(test_playerShip.selectedSub==18);
    SetVulnerableAutoselect(true);VulnerableTargetingDraw(&scene);assert(selectedState.drawn.turret==&turret);
    VulnerableTargetingReset();assert(!selectedState.drawn.object&&!state.drawn.object);
    HudTarget panel;assert(!panel.TargetingShowsAutoselect());panel.ViewObject=&ar;
    for(unsigned type:{0x80000u,0x40000u}){ar.type=type;assert(panel.TargetingShowsAutoselect());}
    for(unsigned type:{0u,0x10000u,0x100000u,0x200000u}){ar.type=type;assert(!panel.TargetingShowsAutoselect());}
    ar.type=0x40000u;ar.typeResult=-1;assert(!panel.TargetingShowsAutoselect());ar.typeResult=0;
    a.ObjectClass=0x303;assert(!panel.TargetingShowsAutoselect());
    puts("PASS: persistent world selection, separate hover, mouse flight/UI, live target changes, dead/detached parts, scanner, toggle and reset");
    puts("PASS: cruiser and gunboat toolbar eligibility, invalid/non-ship targets");
}
'''
production = world.attitude_function + '\n'.join(world.function(s) for s in (
    'bool Available(', 'bool VulnerableAutoselectEnabled()', 'void SetVulnerableAutoselect(',
    'bool IsTurret(', 'bool CanAutoselect(', 'Hover ResolvePart(', 'bool InScannerRange(', 'Hover Pick(',
    'Hover SelectedPart()', 'void VulnerableTargetingDraw(', 'void VulnerableTargetingReset('))
world.source = (world.repo / 'src/freelancer/Client/hud_target_panel.cpp').read_text()
production += world.function('bool HudTarget::TargetingShowsAutoselect() const')
world.compile_check(stub + production + checks, world.repo / 'src/obj/targeting_selected_part')
