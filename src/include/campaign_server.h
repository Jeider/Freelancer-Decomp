#pragma once
#include <windows.h>

namespace CampaignServer {
// The dedicated host owns this immutable startup setting. A client executable
// (including SP/rpclocal) never exports it. No environment variable or save can
// accidentally enable campaign execution in the single-player process.
inline bool Enabled() {
    using Query = int (__cdecl*)();
    auto query = reinterpret_cast<Query>(GetProcAddress(GetModuleHandleW(nullptr),
                                                       "FreelancerCampaignServerEnabled"));
    return query && query() == 1;
}
}
