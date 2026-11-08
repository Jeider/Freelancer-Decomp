"""Check production order text arguments and both localized description templates."""
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree
from check_orders import function
from order_texts import summary

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env

out = ROOT / 'out/train_courier/brief_check'
out.mkdir(parents=True, exist_ok=True)
code = r'''
#include <cassert>
#include <cstdio>
#include <map>
#include <string>
#include <vector>
struct FmtStr {
    unsigned Id=0;std::vector<unsigned> Strings,Ints,Nested;
    void begin_mad_lib(unsigned id){Id=id;}
    void append_string(unsigned id){Strings.push_back(id);}
    void append_int(unsigned value){Ints.push_back(value);}
    void append_fmt_str(FmtStr const& text){Nested=text.Strings;}
    void end_mad_lib(){}
};
namespace Universe {
    struct System {unsigned Name;unsigned GetStridName()const{return Name;}};
    System First{9001},Second{9002};
    System const* get_system(unsigned id){return id==100?&First:id==200?&Second:nullptr;}
}
struct Mission {
    struct {unsigned description=238288;std::map<std::string,unsigned> commodityNames{{"goods",10}};} config;
    struct {unsigned name,systemId;} source{11,100},destination{12,200};
    struct {unsigned wagons=2,distance=3,reward=400,unlockedWagons=5;} state;
    std::string commodity="goods";
    unsigned proseIds=238500,quotedReward=500,lossCharge=100,lostPods=1;
    float expectedSeconds=600;
    FmtStr Field_0x68;
'''
source = (ROOT / 'src/Content/TrainCourier.cpp').read_text()
code += function(source, 'void describeOrder()')
code += r'''
};
int main(){
    Mission m;m.describeOrder();
    assert((m.Field_0x68.Strings==std::vector<unsigned>{10,11,12,9002}));
    assert((m.Field_0x68.Nested==std::vector<unsigned>{12}));
    assert((m.Field_0x68.Ints==std::vector<unsigned>{2,200,3,500,100,1,400,10,5,500}));
    m.destination.systemId=100;m.describeOrder();
    assert(m.Field_0x68.Strings.size()==4 && m.Field_0x68.Strings[3]==9001);
    puts("PASS: production brief uses destination system IDS; refresh replaces it and preserves all existing arguments");
}
'''
(out / 'check.cpp').write_text(code)
compiler, env = compiler_env()
subprocess.run([str(compiler / 'cl.exe'), '/nologo', '/std:c++17', '/EHsc', '/MT',
                str(out / 'check.cpp'), '/Fe:' + str(out / 'check.exe'),
                '/Fo:' + str(out / 'check.obj')], cwd=out, env=env, check=True)
subprocess.run([str(out / 'check.exe')], cwd=out, check=True)
for language in ('ru', 'en'):
    for capacity in (False, True):
        text = ''.join(ElementTree.fromstring(summary(language, capacity)).itertext())
        assert ('Целевая система: %s3' if language == 'ru' else 'Destination system: %s3') in text
        assert text.count('%s3') == 1
print('PASS: RU/EN mission log and offer templates contain destination system')
