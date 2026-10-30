#pragma once

class Vector;
struct DamageList;

namespace FlightTelemetry {
// Client-thread API. No caller starts recording automatically. The caller must
// supply a new file path in an existing directory; existing files are never replaced.
bool Start(wchar_t const* path) noexcept;
bool Stop(char const* reason = "requested") noexcept;
bool IsRecording() noexcept;
char const* LastError() noexcept;

enum class Origin { Unknown, MappedInput, KeyboardSteering, MouseSteering, Synthetic };
class OriginScope {
public:
    explicit OriginScope(Origin origin) noexcept;
    ~OriginScope();
private:
    Origin previous;
};
// Observation hooks: never alter input, flight, weapons or saved-game state.
void BeginFrame(float dt, bool paused) noexcept;
void EndFrame(bool docking) noexcept;
void Input(unsigned command, int eventKind, bool down, bool repeat, unsigned modifiers) noexcept;
void Steering(char const* device, float x, float y, float z) noexcept;
void Command(char const* name, float x, float y = 0, float z = 0) noexcept;
void Shot(unsigned ship, unsigned short equipment, bool automatic, Vector const* aim) noexcept;
void Damage(unsigned object, DamageList const& damage) noexcept;
void Collision(unsigned a, unsigned b, unsigned short partA, unsigned short partB,
               Vector const& point, Vector const& normal, Vector const& relativeVelocity) noexcept;
}
