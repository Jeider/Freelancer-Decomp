#pragma once

#ifdef FREELANCER_EQUIPMENT_SLOTS
#include "equipment_slots.h"
#include "port_config.h"
#include <string>
#include <cwchar>

// Private virtual IDS range: no dependency on the external engclass resource DLL.
inline bool EquipmentSlotText(unsigned Id, std::wstring& Text)
{
    if (!EquipmentSlots::Enabled()) return false;
    bool const Russian = _stricmp(PortLanguage(), "ru") == 0;
    static wchar_t const* const English[] = { L"Armor", L"Scanner", L"Tractor beam" };
    static wchar_t const* const Ru[] = { L"\u0411\u0440\u043e\u043d\u044f", L"\u0421\u043a\u0430\u043d\u0435\u0440", L"\u0422\u0440\u0430\u043a\u0442\u043e\u0440\u043d\u044b\u0439 \u043b\u0443\u0447" };
    if (Id >= EquipmentClasses::CaptionBase && Id < EquipmentClasses::CaptionBase + 30)
    {
        unsigned const Type = EquipmentClasses::First + Id - EquipmentClasses::CaptionBase;
        Text = Russian ? Ru[EquipmentClasses::Family(Type)] : English[EquipmentClasses::Family(Type)];
        Text += Russian ? L" \u2014 \u043a\u043b\u0430\u0441\u0441 \u0434\u043e " : L" \u2014 max class ";
        Text += std::to_wstring(EquipmentClasses::Level(Type));
        return true;
    }
    if (Id >= EquipmentClasses::DescriptionBase && Id < EquipmentClasses::DescriptionBase + 3)
    {
        unsigned const Family = Id - EquipmentClasses::DescriptionBase;
        Text = Russian ? Ru[Family] : English[Family];
        Text += Russian
            ? L". \u0412\u043d\u0443\u0442\u0440\u0435\u043d\u043d\u0438\u0439 \u0441\u043b\u043e\u0442: \u0443\u0441\u0442\u0430\u043d\u0430\u0432\u043b\u0438\u0432\u0430\u0435\u0442\u0441\u044f \u043e\u0434\u043d\u043e \u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u043e \u044d\u0442\u043e\u0433\u043e \u0441\u0435\u043c\u0435\u0439\u0441\u0442\u0432\u0430 \u043d\u0435 \u0432\u044b\u0448\u0435 \u0443\u043a\u0430\u0437\u0430\u043d\u043d\u043e\u0433\u043e \u043a\u043b\u0430\u0441\u0441\u0430."
            : L". Internal slot: fits one device of this family up to the displayed maximum class.";
        return true;
    }
    return false;
}
#endif
