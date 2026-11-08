#include "color_grade_preferences.h"
#include "port_config.h"
#include "common_misc.h"
#include <windows.h>
#include <cstdlib>
namespace
{
    int ValidGrade(int value){return value>=0&&value<=3?value:0;}
    struct GradePreferences
    {
        int saved,preview;
        GradePreferences():saved(ColorGrade::DefaultPreset())
        {
            char directory[MAX_PATH]={},path[MAX_PATH]={},text[64]={};
            if(GetUserDataPath(directory))
            {
                _snprintf_s(path,sizeof(path),_TRUNCATE,"%s\\PerfOptions.ini",directory);
                GetPrivateProfileStringA("ColorGrade","preset","",text,sizeof(text),path);
                char* end=nullptr;long value=std::strtol(text,&end,10);bool digits=end!=text;
                while(*end==' '||*end=='\t')++end;
                if(digits&&(*end==0||*end==';')&&value>=0&&value<=3)saved=int(value);
            }
            preview=saved;
        }
    };
    GradePreferences& GradeState(){static GradePreferences value;return value;}
}
int ColorGrade::DefaultPreset(){return ValidGrade(PortConfigInt("ColorGrade","preset",0));}
int ColorGrade::Preset(){return GradeState().preview;}
int ColorGrade::ConfiguredPreset(){return GradeState().saved;}
void ColorGrade::Preview(int value){GradeState().preview=ValidGrade(value);}
void ColorGrade::Commit(int value){GradeState().saved=GradeState().preview=ValidGrade(value);}
void ColorGrade::Cancel(){GradeState().preview=GradeState().saved;}
void ColorGrade::WritePreferences(FILE* file){if(file)std::fprintf(file,"\n[ColorGrade]\npreset = %d\n",ConfiguredPreset());}
