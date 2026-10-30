#pragma once
struct Win3D;
namespace HudTilt
{
    constexpr float MaxAngleDegrees = 50.f;
    constexpr float AngleStepDegrees = 2.f;
    float Angle();
    // User preference in PerfOptions.ini [HUD]. Console overrides stay temporary.
    float ConfiguredAngle();
    void SetConfiguredAngle(float degrees);
    void SetAngle(float degrees);
    void Shutdown();
    bool InputActive();
    void MapCursor(int& x, int& y);
    void ProjectTooltip(float* worldPosition);
    class InputScope
    {
        int Previous;
    public:
        explicit InputScope(Win3D const* object);
        ~InputScope();
        InputScope(InputScope const&) = delete;
        InputScope& operator=(InputScope const&) = delete;
    };
    class DrawScope
    {
        bool Owner = false;
        bool PreviousFlat = false;
        InputScope Input;
    public:
        explicit DrawScope(Win3D const* object);
        ~DrawScope();
        DrawScope(DrawScope const&) = delete;
        DrawScope& operator=(DrawScope const&) = delete;
    };
}
