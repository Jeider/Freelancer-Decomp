#pragma once
// Port-only behavior values, transported through the existing ScriptBehavior packet.
constexpr unsigned RpgDialogOfferType = 0x525047;
constexpr unsigned RpgDialogEntryKind = 7;
constexpr unsigned RpgScriptOfferEntryKind = 8;
constexpr unsigned RpgScriptOfferId = 0x4F4D3135;
constexpr unsigned RpgScriptOfferKind = 7;
// For RPG offers only, CharacterBehaviorDescription::Field224 (wire Field228)
// carries a presentation hint; the dialogue id remains in Field220/Field224.
constexpr unsigned RpgContactIconRumor = 2;
constexpr unsigned RpgContactIconMission = 3;
inline char const* RpgContactCursor(unsigned Icon)
{
    return Icon == RpgContactIconMission ? "talk_mission" : "talk_rumor";
}
