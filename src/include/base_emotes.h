#pragma once
namespace BaseEmotes {
inline bool HoldsLastFrame(unsigned motion) { return motion == 7; }
inline bool Finished(unsigned motion, float elapsed, float duration) {
    return !HoldsLastFrame(motion) && elapsed >= duration;
}
inline char const* Name(unsigned motion) {
    static char const* const names[] = {
        "Sc_MLBODY_STND_IDLE_000LV_xa_04", "Sc_MLBODY_WLKG_000LV_XA_01",
        "Sc_MLBODY_RNNG_CYCL_000LV_XD_00", "Sc_MLBODY_STND_DANC_000LV_A_28",
        "Sc_MLBODY_STND_SALUT_RHND_000LV_A_05", "Sc_MLBODY_STND_SALR_CASL_000LV_A_02",
        "Sc_MLBODY_STND_CROSS_ARMS_000LV_A_11", "Sc_MLBODY_STND_RAISE_ARMS_000LV_XA_02"};
    return motion < 8 ? names[motion] : names[0];
}
inline float Rate(unsigned motion) { return motion == 1 ? 1.525f : motion == 2 ? .9556f : 1.f; }
}
