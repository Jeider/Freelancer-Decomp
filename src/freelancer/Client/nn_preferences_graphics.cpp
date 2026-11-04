#include "nn_preferences.h"
#include "nn_button_control.h"
#include "nn_text_control.h"
#include "nn_dropdown.h"
#include "wire_controls.h"
#include "nn_ui_pulse.h"
#include "ids_strings.h"
#include "hud_interface_ids.h"
#include <cstring>
#include <string>

namespace
{
    void Visible(WinControl* control, bool visible) { if (control) control->SetProperty(1,!visible,0); }
    float RowY(int row, bool inGame) { return (inGame?.2105f:.2205f)-(3+row)*.035f; }
    std::wstring IdText(unsigned id)
    {
        wchar_t text[256] = {};
        GetIdsStringWWithRawFallback(id, text, 256);
        return text;
    }
    std::wstring Label(int setting)
    {
        constexpr int ids[]={PreferenceIds::GraphicsShadows,PreferenceIds::GraphicsSurfaceRelief,PreferenceIds::GraphicsHighlights,
            PreferenceIds::GraphicsReflections,PreferenceIds::GraphicsAnisotropy,PreferenceIds::GraphicsAntialiasing,
            PreferenceIds::GraphicsNebulae,PreferenceIds::GraphicsVsync,PreferenceIds::GraphicsFpsLimit};
        return IdText(ids[setting]);
    }
    std::wstring ValueText(int setting, int value)
    {
        using namespace GraphicsSettings;
        if (Toggle(setting)) return IdText(value ? PreferenceIds::GraphicsOn : PreferenceIds::GraphicsOff);
        if (setting==Shadows || setting==Nebulae)
        {
            constexpr int ids[]={PreferenceIds::GraphicsOff,PreferenceIds::GraphicsLow,PreferenceIds::GraphicsMedium,PreferenceIds::GraphicsHigh};
            return IdText(ids[value]);
        }
        std::wstring const off=IdText(PreferenceIds::GraphicsOff);
        if (setting==Antialiasing)
        {
            if (value==2) return L"SMAA";
            if (value==1) return L"FXAA";
            return off;
        }
        if (setting==Anisotropy) return value ? std::to_wstring(1<<value)+L"x" : off;
        if (setting==FpsLimit) return std::to_wstring(Fps(value));
        return L"";
    }
}

bool NnPreferences::CreateGraphicsRows()
{
    auto text=[&](char const* name,wchar_t const* value,float x,float y,float width,int align,float scale)
    {
        float const at[3]={x,y,0};
        auto* control=static_cast<NnTextControl*>(CreateTextControl(name,"ItemName",at,nullptr,width,.027f,scale,0,align,0,1));
        if (control) { control->SetText(value);control->Flags&=~kWin3DPickable;GraphicsWidgets.push_back(control); }
        return control;
    };
    for (int i=0;i<GraphicsSettings::Count;++i)
    {
        GraphicsValues[i]=GraphicsSettings::Get(i,true);
        GraphicsOriginal[i]=GraphicsValues[i];
        auto& cell=GraphicsCells[i];
        char name[40];
        sprintf_s(name,"GraphicsLabel%d",i);
        cell.Label=text(name,Label(i).c_str(),-.11f,RowY(i,bInGame!=0),.29f,0,.9f);
        sprintf_s(name,"GraphicsValue%d",i);
        cell.Value=text(name,L"",.188f,RowY(i,bInGame!=0),.207f,1,.9f);
        float const at[3]={.302f,RowY(i,bInGame!=0)-.0145f,0},half[3]={.121f,.0145f,0};
        if (GraphicsSettings::Toggle(i))
        {
            float const toggleAt[3]={.405f,at[1],0},toggleHalf[3]={.015f,.015f,0};
            sprintf_s(name,"GraphicsToggle%d",i);
            cell.Toggle=static_cast<NnButtonControl*>(CreateToggleButtonControl(name,
                "Interface\\NeuroNet\\Inventory\\check.3db","Interface\\NeuroNet\\Inventory\\repairblackbox.3db",
                "ui_shipview_select",nullptr,toggleAt,nullptr,toggleHalf,0,0,0,0,0x65f,0x67a));
            if (!cell.Toggle) return false;
            cell.Toggle->SetProperty(0x35,1,0);
            memcpy(cell.Toggle->Colour,&G_NnPaletteArgb_679b94,4);
            GraphicsWidgets.push_back(cell.Toggle);
        }
        else
        {
            sprintf_s(name,"GraphicsChoice%d",i);
            cell.Choice=static_cast<WireButtonControl*>(CreateWireButtonControl(name,"ui_select_item",at,half,0,0,0,0,0xf));
            if (!cell.Choice) return false;
            GraphicsWidgets.push_back(cell.Choice);
        }
        if (!cell.Label || !cell.Value) return false;
    }
    GraphicsHint=text("GraphicsRestartHint",L"",-.11f,-.225f,.54f,0,.85f);
    GraphicsDropdown=CreateNnDropdownPopup(this);
    if (!GraphicsHint || !GraphicsDropdown) return false;
    SetGraphicsHidden(true);
    return true;
}

void NnPreferences::SetGraphicsHidden(bool hidden)
{
    if (GraphicsDropdown) GraphicsDropdown->Close();
    GraphicsDropdownRow=-1;
    for (auto* control:GraphicsWidgets) Visible(control,!hidden);
    if (!hidden) RefreshGraphicsRows();
}
void NnPreferences::RefreshGraphicsRows()
{
    if (!GraphicsHint) return;
    bool pending=false;
    for (int i=0;i<GraphicsSettings::Count;++i)
    {
        auto& cell=GraphicsCells[i];
        cell.Value->SetText(ValueText(i,GraphicsValues[i]).c_str());
        if (cell.Toggle) cell.Toggle->SetProperty(0x30,GraphicsValues[i]!=0,0);
        pending|=GraphicsValues[i]!=GraphicsSettings::Get(i);
    }
    GraphicsHint->SetText(IdText(pending ? PreferenceIds::GraphicsRestartPending : PreferenceIds::GraphicsRestartHint).c_str());
    GraphicsHint->TextColour=pending?G_NnPaletteArgb_679ba4:G_NnPaletteArgb_679b94;
}
void NnPreferences::SnapshotGraphics()
{
    for (int i=0;i<GraphicsSettings::Count;++i)
        GraphicsOriginal[i]=GraphicsValues[i]=GraphicsSettings::Get(i,true);
    RefreshGraphicsRows();
}
void NnPreferences::CommitGraphics()
{
    for (int i=0;i<GraphicsSettings::Count;++i) GraphicsSettings::Set(i,GraphicsValues[i]);
}
void NnPreferences::RevertGraphics()
{
    for (int i=0;i<GraphicsSettings::Count;++i) GraphicsValues[i]=GraphicsOriginal[i];
    if (GraphicsDropdown) GraphicsDropdown->Close();
    GraphicsDropdownRow=-1;
    RefreshGraphicsRows();
}
bool NnPreferences::GraphicsDirty() const
{
    for (int i=0;i<GraphicsSettings::Count;++i) if (GraphicsValues[i]!=GraphicsOriginal[i]) return true;
    return false;
}
bool NnPreferences::GraphicsProperty(int msg, Win3D* source, uintptr_t value)
{
    if (CurPage!=1 || bFlipping || bConfirmMode || bVideoConfirm || Anim<0) return false;
    if (source==GraphicsDropdown && msg==0x3e)
    {
        int const row=GraphicsDropdownRow;
        GraphicsDropdown->Close();GraphicsDropdownRow=-1;
        if (row<0 || row>=GraphicsSettings::Count || value>unsigned(GraphicsSettings::Maximum(row))) return true;
        int const selected=int(value)+(row==GraphicsSettings::FpsLimit ? 1 : 0);
        if (selected>GraphicsSettings::Maximum(row)) return true;
        GraphicsValues[row]=selected;
        RefreshGraphicsRows();UpdateDirty(-1,-1.f);return true;
    }
    if (source==DefaultsButton && msg==0x26)
    {
        for (int i=0;i<GraphicsSettings::Count;++i) GraphicsValues[i]=GraphicsSettings::Default(i);
        RefreshGraphicsRows(); // continue into the native defaults handler
        return false;
    }
    for (int i=0;i<GraphicsSettings::Count;++i)
    {
        auto const& cell=GraphicsCells[i];
        if (cell.Toggle && source==cell.Toggle)
        {
            if (msg==0x30) {GraphicsValues[i]=value==0?1:0;RefreshGraphicsRows();UpdateDirty(-1,-1.f);}
            return true;
        }
        if (cell.Choice && source==cell.Choice)
        {
            if (msg!=0x26) return true;
            if (VideoModeDropdown) VideoModeDropdown->Close();
            GraphicsDropdown->Close();GraphicsDropdownRow=-1;
            std::vector<std::wstring> choices;
            int const first=i==GraphicsSettings::FpsLimit ? 1 : 0;
            for (int valueIndex=first;valueIndex<=GraphicsSettings::Maximum(i);++valueIndex) choices.push_back(ValueText(i,valueIndex));
            if (GraphicsDropdown->Open(.181f,RowY(i,bInGame!=0),.242f,choices,GraphicsValues[i]-first)) GraphicsDropdownRow=i;
            return true;
        }
    }
    return false;
}
void NnPreferences::DrawGraphicsDropdown()
{
    if (CurPage!=1 || bConfirmMode || bVideoConfirm || bFlipping) return;
    for (auto const& cell:GraphicsCells)
        if (cell.Choice && (cell.Choice->Flags&kWin3DVisible)) DrawNnDropdownCaret(cell.Choice);
    if (GraphicsDropdown) GraphicsDropdown->Draw();
}
