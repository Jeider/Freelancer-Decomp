#pragma once
#include "graphics_settings.h"

// Keys intentionally match both Launchers' [Costume] preferences.
namespace PlayerCustomization
{
    struct Choice { char const* Key; wchar_t const* Label; };
    static Choice const Bodies[] = {
        {"default", L"\u0421\u0442\u0430\u043d\u0434\u0430\u0440\u0442\u043d\u0430\u044f \u043e\u0434\u0435\u0436\u0434\u0430"}, {"li_elite", L"\u042d\u043b\u0438\u0442\u0430 \u041b\u0438\u0431\u0435\u0440\u0442\u0438"},
        {"li_guard", L"\u041e\u0444\u0438\u0446\u0435\u0440 \u041b\u0438\u0431\u0435\u0440\u0442\u0438"}, {"br_elite", L"\u042d\u043b\u0438\u0442\u0430 \u0411\u0440\u0435\u0442\u043e\u043d\u0438\u0438"},
        {"br_guard", L"\u041e\u0444\u0438\u0446\u0435\u0440 \u0411\u0440\u0435\u0442\u043e\u043d\u0438\u0438"}, {"rh_elite", L"\u042d\u043b\u0438\u0442\u0430 \u0420\u0435\u0439\u043d\u043b\u0430\u043d\u0434\u0430"},
        {"rh_guard", L"\u041e\u0444\u0438\u0446\u0435\u0440 \u0420\u0435\u0439\u043d\u043b\u0430\u043d\u0434\u0430"}, {"ku_elite", L"\u042d\u043b\u0438\u0442\u0430 \u041a\u0443\u0441\u0430\u0440\u0438"},
        {"ku_guard", L"\u041e\u0444\u0438\u0446\u0435\u0440 \u041a\u0443\u0441\u0430\u0440\u0438"}, {"order", L"\u041e\u0434\u0435\u0436\u0434\u0430 \u041e\u0440\u0434\u0435\u043d\u0430"},
        {"classic", L"\u041a\u043b\u0430\u0441\u0441\u0438\u0447\u0435\u0441\u043a\u0438\u0439 \u0422\u0440\u0435\u043d\u0442"}
    };
    static Choice const Hats[] = {
        {"default", L"\u0411\u0435\u0437 \u0433\u043e\u043b\u043e\u0432\u043d\u043e\u0433\u043e \u0443\u0431\u043e\u0440\u0430"}, {"rh_elite", L"\u0420\u0435\u0439\u043d\u043b\u0430\u043d\u0434"},
        {"li_elite", L"\u041b\u0438\u0431\u0435\u0440\u0442\u0438"}, {"br_elite", L"\u0411\u0440\u0435\u0442\u043e\u043d\u0438\u044f"}, {"ku_elite", L"\u041a\u0443\u0441\u0430\u0440\u0438"}
    };
    static Choice const Helmets[] = {
        {"default", L"\u0421\u0442\u0430\u043d\u0434\u0430\u0440\u0442\u043d\u044b\u0439"}, {"ge_generic1", L"\u0413\u0440\u0430\u0436\u0434\u0430\u043d\u0441\u043a\u0438\u0439"},
        {"pl_player", L"\u0422\u0440\u0435\u043d\u0442"}, {"br_brighton", L"\u0411\u0440\u0430\u0439\u0442\u043e\u043d"},
        {"br_darcy", L"\u0414\u0430\u0440\u0441\u0438"}, {"br_kaitlyn", L"\u041a\u0435\u0439\u0442\u043b\u0438\u043d"},
        {"ku_kym", L"\u041a\u0438\u043c"}, {"li_hatcher", L"\u0425\u044d\u0442\u0447\u0435\u0440"},
        {"pi_pirate", L"\u041f\u0438\u0440\u0430\u0442"}, {"rh_alaric", L"\u0410\u043b\u0430\u0440\u0438\u043a"},
        {"rh_reichman", L"\u0420\u0430\u0439\u0445\u043c\u0430\u043d"}, {"rh_wilham", L"\u0412\u0438\u043b\u044c\u0445\u0430\u043c"},
        {"br_elite", L"\u042d\u043b\u0438\u0442\u0430 \u0411\u0440\u0435\u0442\u043e\u043d\u0438\u0438"}, {"rh_elite", L"\u042d\u043b\u0438\u0442\u0430 \u0420\u0435\u0439\u043d\u043b\u0430\u043d\u0434\u0430"},
        {"li_elite", L"\u042d\u043b\u0438\u0442\u0430 \u041b\u0438\u0431\u0435\u0440\u0442\u0438"}, {"ku_elite", L"\u042d\u043b\u0438\u0442\u0430 \u041a\u0443\u0441\u0430\u0440\u0438"}
    };
    struct Selection { int Body = 0; int Hat = 0; int Helmet = 0; };
    COMMON_API Selection __cdecl Load();
    COMMON_API bool __cdecl Save(Selection const& value);
    COMMON_API void __cdecl Apply(Costume& base, Costume& comm, Selection const& value);
}
