// Production character-clock and teardown routines with a fake mixer boundary.
#include <cassert>
#include <cstdio>
#define FREELANCER_RPG_WORLD
#define DACOM_API
using GENRESULT = int;
constexpr int GR_OK = 0;
struct Script { bool RpgFragment = false; unsigned char Field_0x55 = 0; };
struct Character {
    struct { int Instance = 1; } Lod;
    int ActiveMotions = 3, LightGroup = 1, Layer = 1, RenderMode = 1, Resets = 0;
    double Time = 0;
    void Update(double dt) { Time += dt; }
    void RemoveMotionHandle(int h) { if (h != -1) --ActiveMotions; }
    void ResetScriptState(unsigned char) { ++Resets; }
};
namespace DALib {
    struct Deformer {
        int Destroyed = 0, AimsStopped = 0;
        void DestroyHandle(int, int) { ++Destroyed; }
        void StopAim(int, void*) { ++AimsStopped; }
    } Fake;
    auto* Deform = &Fake;
}
struct CharacterDb { int Releases = 0; void ReleaseScript(unsigned) { ++Releases; } } Db;
CharacterDb* GetCharacterInfoDb() { return &Db; }
void malloc_strfree(char** p) { *p = nullptr; }
struct FThornDeformable {
    static constexpr int kMotionSlots = 2, kAimSlots = 2;
    struct FMotionSlot { int Handle = -1; unsigned ScriptId = 0; int EventId = -1; bool bActive = false; } Motions[2];
    struct FAimSlot { void* Handle = nullptr; bool bStarted = false, bActive = false; } Aims[2];
    ::Script* Owner;
    ::Character* Character;
    char* ActorName = nullptr;
    GENRESULT AdvanceTime(int);
    void Stop();
};
#include "deformable.inc"
int main() {
    Script session, overlay; overlay.RpgFragment = true;
    Character actor;
    FThornDeformable persistent{ {}, {}, &session, &actor };
    FThornDeformable speech{ {}, {}, &overlay, &actor };
    FThornDeformable gestures{ {}, {}, &overlay, &actor };
    persistent.AdvanceTime(100); speech.AdvanceTime(100); gestures.AdvanceTime(100);
    assert(actor.Time == .1); // Three tracks, one mixer tick.
    speech.Motions[0] = { 10, 11, 12, true };
    speech.Stop();
    assert(actor.ActiveMotions == 2 && actor.Resets == 0 && actor.LightGroup == 1);
    assert(DALib::Fake.Destroyed == 1 && Db.Releases == 1);
    speech.Stop();
    assert(actor.ActiveMotions == 2 && DALib::Fake.Destroyed == 1);
    persistent.Stop();
    assert(actor.Resets == 1 && actor.LightGroup == 0);
    puts("PASS: parallel RPG tracks advance character once; fragment teardown balances handles and preserves session state");
}
