struct Point {double x,y,z;};
struct Sphere {
 Point centre;double radius;
 bool InZone(Point const&p,float margin)const{
  return std::pow(p.x-centre.x,2)+std::pow(p.y-centre.y,2)+std::pow(p.z-centre.z,2)<std::pow(radius+margin,2);
 }
};
struct Exclusion {Sphere const* ZonePtr;bool bExcludeDynamicAsteroids,bExcludeBillboards;};
std::ifstream input(getenv("FREELANCER_ASTEROID_EXCLUSION_FIXTURE"));
Require(input.good(),"live Omega-15 exclusion fixture");
std::vector<Sphere> zones;Sphere zone;while(input>>zone.centre.x>>zone.centre.y>>zone.centre.z>>zone.radius)zones.push_back(zone);
Require(zones.size()==8,"all eight authored dynamic exclusions");
std::vector<Exclusion> entries;for(auto const&zone:zones)entries.push_back({&zone,true,true});
std::vector<Exclusion const*> exclusions;for(auto const&entry:entries)exclusions.push_back(&entry);
unsigned excluded=0,accepted=0;
for(auto const&zone:zones)for(double offset:{0.0,zone.radius,zone.radius+1000}){
 int sampleCell[]={NebulaAsteroidMesh::Cell(zone.centre.x+offset),NebulaAsteroidMesh::Cell(zone.centre.y),NebulaAsteroidMesh::Cell(zone.centre.z)};
 NebulaAsteroidMesh::Generate(sampleCell,3,[&](auto const&r){
  Point point{r.position[0],r.position[1],r.position[2]};float radius=56; // conservative maximum native mesh
  bool blocked=NebulaAsteroidMesh::IsExcluded(exclusions.begin(),exclusions.end(),point,radius);
  if(blocked){++excluded;return;}++accepted;
  for(auto const&z:zones){double distance=std::sqrt(std::pow(point.x-z.centre.x,2)+std::pow(point.y-z.centre.y,2)+std::pow(point.z-z.centre.z,2));
   Require(distance-radius>=z.radius-.001,"entire accepted mesh is outside every exclusion");}
 });
}
Require(excluded>1000&&accepted>1000,"actual boundaries reject rocks without emptying surrounding field");
Sphere fixture{{0,0,0},2500};Exclusion dynamic{&fixture,true,false},billboard{&fixture,false,true},inactive{&fixture,false,false};
exclusions.assign(20,&inactive);exclusions[18]=&dynamic;
Require(NebulaAsteroidMesh::IsExcluded(exclusions.begin(),exclusions.end(),Point{2530,0,0},56),"dynamic-only zone after index sixteen, whole-rock margin");
Require(!NebulaAsteroidMesh::IsExcluded(exclusions.begin(),exclusions.end(),Point{2600,0,0},56),"margin does not remove distant outside rocks");
exclusions[18]=&billboard;Require(NebulaAsteroidMesh::IsExcluded(exclusions.begin(),exclusions.end(),Point{0,0,0},56),"billboard-only exclusion");
exclusions[18]=nullptr;Require(!NebulaAsteroidMesh::IsExcluded(exclusions.begin(),exclusions.end(),Point{0,0,0},56),"disabled/null zones do not exclude");
printf("PASS all eight live Omega-15 exclusions: %u accepted, %u rejected; flag and >16-zone cases\n",accepted,excluded);
