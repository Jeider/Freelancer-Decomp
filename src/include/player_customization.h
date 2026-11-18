#pragma once
#include "graphics_settings.h"

// Keys intentionally match both Launchers' [Costume] preferences.
namespace PlayerCustomization
{
    struct Choice { char const* Key; wchar_t const* Label; wchar_t const* EnglishLabel; };
    static Choice const Bodies[] = {
        {"default", L"\u0421\u0442\u0430\u043d\u0434\u0430\u0440\u0442\u043d\u0430\u044f \u043e\u0434\u0435\u0436\u0434\u0430", L"Default suit"}, {"li_elite", L"\u042d\u043b\u0438\u0442\u0430 \u041b\u0438\u0431\u0435\u0440\u0442\u0438", L"Liberty elite"},
        {"li_guard", L"\u041e\u0444\u0438\u0446\u0435\u0440 \u041b\u0438\u0431\u0435\u0440\u0442\u0438", L"Liberty guard"}, {"br_elite", L"\u042d\u043b\u0438\u0442\u0430 \u0411\u0440\u0435\u0442\u043e\u043d\u0438\u0438", L"Bretonia elite"},
        {"br_guard", L"\u041e\u0444\u0438\u0446\u0435\u0440 \u0411\u0440\u0435\u0442\u043e\u043d\u0438\u0438", L"Bretonia guard"}, {"rh_elite", L"\u042d\u043b\u0438\u0442\u0430 \u0420\u0435\u0439\u043d\u043b\u0430\u043d\u0434\u0430", L"Rheinland elite"},
        {"rh_guard", L"\u041e\u0444\u0438\u0446\u0435\u0440 \u0420\u0435\u0439\u043d\u043b\u0430\u043d\u0434\u0430", L"Rheinland guard"}, {"ku_elite", L"\u042d\u043b\u0438\u0442\u0430 \u041a\u0443\u0441\u0430\u0440\u0438", L"Kusari elite"},
        {"ku_guard", L"\u041e\u0444\u0438\u0446\u0435\u0440 \u041a\u0443\u0441\u0430\u0440\u0438", L"Kusari guard"}, {"order", L"\u041e\u0434\u0435\u0436\u0434\u0430 \u041e\u0440\u0434\u0435\u043d\u0430", L"Order suit"},
        {"classic", L"\u041a\u043b\u0430\u0441\u0441\u0438\u0447\u0435\u0441\u043a\u0438\u0439 \u0422\u0440\u0435\u043d\u0442", L"Classic Trent"}
    };
    static Choice const Hats[] = {
        {"default", L"\u0411\u0435\u0437 \u0433\u043e\u043b\u043e\u0432\u043d\u043e\u0433\u043e \u0443\u0431\u043e\u0440\u0430", L"No headwear"}, {"rh_elite", L"\u0420\u0435\u0439\u043d\u043b\u0430\u043d\u0434", L"Rheinland"},
        {"li_elite", L"\u041b\u0438\u0431\u0435\u0440\u0442\u0438", L"Liberty"}, {"br_elite", L"\u0411\u0440\u0435\u0442\u043e\u043d\u0438\u044f", L"Bretonia"}, {"ku_elite", L"\u041a\u0443\u0441\u0430\u0440\u0438", L"Kusari"}
    };
    static Choice const Helmets[] = {
        {"default", L"\u0421\u0442\u0430\u043d\u0434\u0430\u0440\u0442\u043d\u044b\u0439", L"Default"}, {"ge_generic1", L"\u0413\u0440\u0430\u0436\u0434\u0430\u043d\u0441\u043a\u0438\u0439", L"Civilian"},
        {"pl_player", L"\u0422\u0440\u0435\u043d\u0442", L"Trent"}, {"br_brighton", L"\u0411\u0440\u0430\u0439\u0442\u043e\u043d", L"Brighton"},
        {"br_darcy", L"\u0414\u0430\u0440\u0441\u0438", L"Darcy"}, {"br_kaitlyn", L"\u041a\u0435\u0439\u0442\u043b\u0438\u043d", L"Caitlyn"},
        {"ku_kym", L"\u041a\u0438\u043c", L"Kym"}, {"li_hatcher", L"\u0425\u044d\u0442\u0447\u0435\u0440", L"Hatcher"},
        {"pi_pirate", L"\u041f\u0438\u0440\u0430\u0442", L"Pirate"}, {"rh_alaric", L"\u0410\u043b\u0430\u0440\u0438\u043a", L"Alaric"},
        {"rh_reichman", L"\u0420\u0430\u0439\u0445\u043c\u0430\u043d", L"Reichman"}, {"rh_wilham", L"\u0412\u0438\u043b\u044c\u0445\u0430\u043c", L"Wilham"},
        {"br_elite", L"\u042d\u043b\u0438\u0442\u0430 \u0411\u0440\u0435\u0442\u043e\u043d\u0438\u0438", L"Bretonia elite"}, {"rh_elite", L"\u042d\u043b\u0438\u0442\u0430 \u0420\u0435\u0439\u043d\u043b\u0430\u043d\u0434\u0430", L"Rheinland elite"},
        {"li_elite", L"\u042d\u043b\u0438\u0442\u0430 \u041b\u0438\u0431\u0435\u0440\u0442\u0438", L"Liberty elite"}, {"ku_elite", L"\u042d\u043b\u0438\u0442\u0430 \u041a\u0443\u0441\u0430\u0440\u0438", L"Kusari elite"}
    };
    struct Selection { int Body = 0; int Hat = 0; int Helmet = 0; };
    COMMON_API Selection __cdecl Load();
    COMMON_API bool __cdecl Save(Selection const& value);
    COMMON_API void __cdecl Apply(Costume& base, Costume& comm, Selection const& value);
}
