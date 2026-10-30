#pragma once

// Kept outside retail object layouts: Common.dll consumers depend on their ABI.
struct CloakSettings
{
    bool enabled = false;
    bool defaultState = false;
    float duration = -1.0f;
    float cooldown = 0.0f;
    float toggleCooldown = 0.3f;
};
