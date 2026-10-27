#pragma once

// Port-only class IDs, after retail (0..0x42) and adoxa engclass (0x43..0x7e).
// No changes to the retail enums, object layouts or virtual tables.
#include <cstring>

namespace EquipmentClasses
{
    enum { First = 0x7f, Levels = 10, Families = 3, End = First + Levels * Families,
           Invalid = End, CaptionBase = 0x7fef0000, DescriptionBase = CaptionBase + 32 };

    inline bool IsType(unsigned Type) { return Type >= First && Type < End; }
    inline bool IsManaged(unsigned Type) { return IsType(Type) || Type == Invalid; }
    inline int Family(unsigned Type) { return IsType(Type) ? int((Type - First) / Levels) : -1; }
    inline int Level(unsigned Type) { return IsType(Type) ? int((Type - First) % Levels) + 1 : 0; }
    inline unsigned Type(int FamilyIndex, int Class)
    {
        return FamilyIndex >= 0 && FamilyIndex < Families && Class >= 1 && Class <= Levels
            ? First + FamilyIndex * Levels + Class - 1 : Invalid;
    }
    inline int FindFamily(char const* Name)
    {
        static char const* const Names[] = { "armor", "scanner", "tractor" };
        if (Name)
            for (int I = 0; I < Families; ++I)
                if (_stricmp(Name, Names[I]) == 0) return I;
        return -1;
    }
    inline int ParseLevel(char const* Number)
    {
        if (!Number) return 0;
        if (Number[0] >= '1' && Number[0] <= '9' && Number[1] == '\0') return Number[0] - '0';
        return std::strcmp(Number, "10") == 0 ? 10 : 0;
    }
    inline unsigned Parse(char const* Name)
    {
        static char const* const Prefixes[] = {
            "hp_armor_special_", "hp_scanner_special_", "hp_tractor_special_" };
        if (!Name) return Invalid;
        for (int I = 0; I < Families; ++I)
        {
            size_t const N = std::strlen(Prefixes[I]);
            if (_strnicmp(Name, Prefixes[I], N) != 0) continue;
            char const* Number = Name + N;
            return Type(I, ParseLevel(Number));
        }
        return Invalid;
    }
}
