#pragma once
#include <cstdio>

namespace BaseNeural
{
    bool Enabled();
    bool ConfiguredEnabled();
    void PreviewEnabled(bool enabled);
    void CommitEnabled(bool enabled);
    int StrengthPercent();
    int ConfiguredStrengthPercent();
    int DefaultStrengthPercent();
    void PreviewStrength(int percent);
    void CommitStrength(int percent);
    void CancelStrengthPreview();
    void WritePreferences(FILE* file);
}
