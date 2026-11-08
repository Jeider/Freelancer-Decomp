#pragma once

// Indices into Pythonlancer's SEQUENCE_MALE_STAND_RHAND_ALT2, exported as
// gestures/{vendor,player}_01..08.thn. A CONV step contains all three motions.
namespace RpgGestureRotation
{
    constexpr unsigned Count = 8;
    constexpr int ConvMinimumVoiceMs = 15000;

    inline unsigned Next(unsigned Cursor, bool Player, int VoiceMs)
    {
        unsigned Step = Cursor % Count;
        bool const Conv = Step == 0 || Step == 3;
        if (Conv && (Player || VoiceMs < ConvMinimumVoiceMs)) ++Step;
        return Step;
    }
}
