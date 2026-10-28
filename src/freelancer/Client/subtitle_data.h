#pragma once
#include <string>
#include <unordered_map>
#include <vector>

namespace NativeSubtitles
{
    struct Part { double start = 0, end = 0; std::wstring text; };
    struct Entry
    {
        std::wstring area;
        std::wstring text;
        std::vector<Part> parts;
        std::wstring At(double seconds) const;
    };
    using Database = std::unordered_map<std::wstring, Entry>;
    struct Playback
    {
        Entry const* entry;
        double time = 0;
        bool started = false;
        unsigned long long order = 0;
        void Sync(double seconds, bool active, bool paused, float dt);
    };
    std::wstring AudioKey(std::wstring path);
    bool ReadXml(wchar_t const* path, Database& result, std::wstring& error);
}
