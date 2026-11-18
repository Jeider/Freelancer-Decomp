#include "nn_preferences.h"
#include "page_customization.h"
#include "customization_text.h"
#include "nn_text_control.h"
#include "wire_controls.h"
#include "nn_dropdown.h"
#include "common_misc.h"
#include <string>

bool NnPreferences::CreateCustomizationGroup()
{
    auto text=[&](char const* name,wchar_t const* caption,float x,float y,float width,char const* font) {
        std::wstring text=caption;
        for(auto& c:text) {
            if((c>=L'a'&&c<=L'z') || (c>=L'\u0430'&&c<=L'\u044f')) c-=32;
            else if(c==L'\u0451') c=L'\u0401';
        }
        float at[]={x,y,0};
        auto* label=static_cast<NnTextControl*>(CreateTextControl(name,font,at,nullptr,width,.03f,font[0]=='P'?1.43f:1.f,0,0,0,1));
        if(label) { label->SetText(text.c_str());label->Flags&=~kWin3DPickable;CustomizationWidgets.push_back(label); }
        return label!=nullptr;
    };
    float shift=(bInGame ? -.01f : 0.f)-.023f;
#ifdef FREELANCER_DLSS5
    shift-=.035f;
#endif
    if(!text("CustomizationGroup",CustomizationText::Text(L"\u041a\u0430\u0441\u0442\u043e\u043c\u0438\u0437\u0430\u0446\u0438\u044f", L"Customization"),-.14f,-.11f+shift,.5f,"PageHeader")) return false;
    for(int i=0;i<2;++i) {
        float const y=-.145f+shift-i*.030f;
        if(!text(i?"HelmetLabel":"CharacterLabel",i?CustomizationText::Text(L"\u0428\u043b\u0435\u043c \u0441\u0432\u044f\u0437\u0438", L"Comm helmet"):CustomizationText::Text(L"\u041f\u0435\u0440\u0441\u043e\u043d\u0430\u0436", L"Character"),-.11f,y,.27f,"ItemName")) return false;
        float at[]={.302f,y-.012f,0},half[]={.121f,.0145f,0};
        auto* button=static_cast<WireButtonControl*>(CreateWireButtonControl(i?"CustomizeHelmet":"CustomizeCharacter","ui_select_item",at,half,0,0,0,0,0xf));
        if(!button) return false;
        button->WireState&=~0x40;
        CustomizationButtons[i]=button;CustomizationWidgets.push_back(button);
        if(!text(i?"HelmetConfigure":"CharacterConfigure",CustomizationText::Text(L"\u041d\u0430\u0441\u0442\u0440\u043e\u0438\u0442\u044c", L"Customize"),.245f,y,.18f,"ItemName")) return false;
    }
    SetCustomizationHidden(true);return true;
}
void NnPreferences::SetCustomizationHidden(bool hidden)
{
    for(auto* widget:CustomizationWidgets) widget->SetProperty(1,hidden,0);
    bool const available=!bInGame || SinglePlayer();
    for(auto* button:CustomizationButtons) if(button)
        button->ButtonState=static_cast<unsigned char>((button->ButtonState&~4u)|(available?4u:0));
}
bool NnPreferences::CustomizationProperty(int msg,Win3D* source)
{
    for(int i=0;i<2;++i) if(source && source==CustomizationButtons[i]) {
        if(msg==0x26 && CurPage==1 && !bConfirmMode && !bVideoConfirm && !bFlipping) OpenCustomization(i!=0);
        return true;
    }
    return false;
}

void NnPreferences::OpenCustomization(bool portrait)
{
    if (CustomizationWindow || (bInGame && !SinglePlayer())) return;
    CloseMiscDropdown();
    if (GraphicsDropdown) GraphicsDropdown->Close();
    if (VideoModeDropdown) VideoModeDropdown->Close();
    CustomizationWindow=OpenCustomizationWindow(this,portrait);
    // Draw/update only this child while its input capture blocks the settings.
    // Keeping it under the host also works when in-game preferences own the modal tick.
}

void NnPreferences::CloseCustomization()
{
    if (!CustomizationWindow) return;
    CustomizationWindow->Destroy();
    delete CustomizationWindow;
    CustomizationWindow=nullptr;
}

void NnPreferences::Destroy()
{
    CloseCustomization();
    WinControl::Destroy();
}
