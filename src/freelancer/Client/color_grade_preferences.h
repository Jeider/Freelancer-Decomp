#pragma once
#include <cstdio>
namespace ColorGrade
{
    int Preset();
    int ConfiguredPreset();
    int DefaultPreset();
    void Preview(int preset);
    void Commit(int preset);
    void Cancel();
    void WritePreferences(FILE* file);
}
