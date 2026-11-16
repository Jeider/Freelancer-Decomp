#pragma once
#include "campaign_control.h"
#include <cstdio>
#include <io.h>
#include <string>

namespace CampaignControl {
inline bool Valid(State const& s) {
    if (s.phase > Complete || s.completed > MissionCount || !s.revision ||
        s.chapter > 42 || s.rank != RankForChapter(s.chapter)) return false;
    if (s.phase == First) return s.completed == 0 && s.chapter == 0;
    if (s.phase == Complete) return s.completed == MissionCount && s.chapter == 42;
    if (s.completed >= MissionCount) return false;
    auto const& m = Missions()[s.completed];
    if (s.phase == Running || s.phase == Interrupted)
        return s.attempt && s.chapter >= m.start && s.chapter <= m.finish;
    return s.completed > 0 && s.chapter == Missions()[s.completed-1].after &&
        (s.phase == Automatic) == Missions()[s.completed-1].automaticNext;
}
inline unsigned Checksum(unsigned const* words, unsigned count) {
    unsigned result = 2166136261u;
    for (unsigned i=0; i<count; ++i) result = (result ^ words[i]) * 16777619u;
    return result;
}
// Server-owned checkpoint; never read a player's StoryInfo. Atomic replacement
// keeps the previous checkpoint intact on failed writes. No game DATA writes.
class ProgressFile {
    std::wstring path;
public:
    explicit ProgressFile(std::wstring filename) : path(std::move(filename)) {}
    static std::wstring ServerPath() {
        wchar_t filename[MAX_PATH] = {};
        if (!GetModuleFileNameW(nullptr, filename, MAX_PATH)) return {};
        std::wstring result(filename);
        auto slash = result.find_last_of(L"\\/");
        return slash == std::wstring::npos ? std::wstring() : result.substr(0,slash+1) + L"campaign_progress.bin";
    }
    // 1 loaded, 0 no prior campaign, -1 unreadable/corrupt (never silently reset).
    int Load(State& out) const {
        if (path.empty()) return -1;
        FILE* file = nullptr;
        if (_wfopen_s(&file,path.c_str(),L"rb") != 0)
            return GetFileAttributesW(path.c_str()) == INVALID_FILE_ATTRIBUTES && GetLastError() == ERROR_FILE_NOT_FOUND ? 0 : -1;
        unsigned w[11] = {};
        bool good = fread(w,sizeof(w),1,file) == 1 && fgetc(file) == EOF && !ferror(file);
        fclose(file);
        if (!good || w[0] != 0x43504d46u || w[1] != 1 || w[10] != Checksum(w,10)) return -1;
        State state; state.phase=w[2];state.completed=w[3];state.chapter=w[4];state.rank=w[5];
        state.attempt=(std::uint64_t(w[7])<<32)|w[6];state.revision=w[8];
        if (w[9] || !Valid(state)) return -1;
        out=state;return 1;
    }
    bool Save(State const& state) const {
        if (path.empty() || !Valid(state)) return false;
        unsigned w[] = {0x43504d46u,1,state.phase,state.completed,state.chapter,state.rank,
            unsigned(state.attempt),unsigned(state.attempt>>32),state.revision,0,0};
        w[10]=Checksum(w,10);
        std::wstring temp=path+L".tmp";
        FILE* file=nullptr;
        if (_wfopen_s(&file,temp.c_str(),L"wb") != 0) return false;
        bool good=fwrite(w,sizeof(w),1,file)==1 && fflush(file)==0 && _commit(_fileno(file))==0;
        if (fclose(file)!=0) good=false;
        if (good) good=MoveFileExW(temp.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=0;
        if (!good) DeleteFileW(temp.c_str());
        return good;
    }
};
}
