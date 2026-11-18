#pragma once
#include "port_config.h"
#include <cstring>

namespace CustomizationText
{
    // Appearance follows interface language, independently of voice-over.
    inline wchar_t const* Text(wchar_t const* russian, wchar_t const* english)
    {
        return _stricmp(PortLanguage(), "ru") == 0 ? russian : english;
    }
}
