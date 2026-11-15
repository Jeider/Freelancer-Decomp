#pragma once
#include <cstdio>
#include <cstdint>

namespace CampaignServerConfig {
// Append to the existing version-3 file. Retail readers ignore the extension;
// old version-2/3 files and incomplete/unknown extensions mean ordinary MP.
inline bool Read(FILE* file) {
    std::uint32_t words[3] = {};
    return fread(words, sizeof(words), 1, file) == 1 &&
        words[0] == 0x504d4143u && words[1] == 1 && words[2] == 1;
}
inline bool Write(FILE* file, bool enabled) {
    std::uint32_t const words[] = {0x504d4143u, 1, enabled ? 1u : 0u};
    return fwrite(words, sizeof(words), 1, file) == 1;
}
}
