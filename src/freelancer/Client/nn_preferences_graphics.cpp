#include "nn_preferences.h"
#include "nn_button_control.h"
#include "nn_text_control.h"
#include "nn_dropdown.h"
#include "wire_controls.h"
#include "nn_ui_pulse.h"
#include "ids_strings.h"
#include "hud_interface_ids.h"
#include "color_grade_preferences.h"
#include <cstring>
#include <string>
#ifdef FREELANCER_DLSS5
#include "base_neural_preferences.h"
#include "ui_scroll.h"
#endif

namespace
{
    void Visible(WinControl* control, bool visible) { if (control) control->SetProperty(1,!visible,0); }
    float RowY(int row, bool inGame)
    {
        float spacing=.0315f;
#ifdef FREELANCER_DLSS5
        spacing=.029f; // Color grade and DLSS fit above the hint/buttons.
#endif
        return (inGame?.2105f:.2205f)-3*.035f-row*spacing;
    }
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
    std::wstring GradeText(int preset)
    {
        constexpr int ids[]={PreferenceIds::GraphicsOff,PreferenceIds::ColorGradeNatural,PreferenceIds::ColorGradeWarm,PreferenceIds::ColorGradeCool};
        return IdText(ids[preset]);
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
    float hintY=-.225f;
    ColorGradeValue=ColorGradeOriginal=ColorGrade::ConfiguredPreset();
    float const gradeY=RowY(GraphicsSettings::Count,bInGame!=0);
    ColorGradeCell.Label=text("ColorGradeLabel",IdText(PreferenceIds::ColorGradeLabel).c_str(),-.11f,gradeY,.29f,0,.9f);
    ColorGradeCell.Value=text("ColorGradeValue",L"",.188f,gradeY,.207f,1,.9f);
    float const gradeAt[3]={.302f,gradeY-.0145f,0},gradeHalf[3]={.121f,.0145f,0};
    ColorGradeCell.Choice=static_cast<WireButtonControl*>(CreateWireButtonControl("ColorGradeChoice","ui_select_item",gradeAt,gradeHalf,0,0,0,0,0xf));
    if(!ColorGradeCell.Label||!ColorGradeCell.Value||!ColorGradeCell.Choice)return false;
    GraphicsWidgets.push_back(ColorGradeCell.Choice);
#ifdef FREELANCER_DLSS5
    NeuralStrength=NeuralStrengthOriginal=BaseNeural::ConfiguredStrengthPercent();
    NeuralEnabled=NeuralEnabledOriginal=BaseNeural::ConfiguredEnabled();
    float const y=RowY(GraphicsSettings::Count+1,bInGame!=0);
    auto* label=text("NeuralStrengthLabel",IdText(PreferenceIds::NeuralStrength).c_str(),-.11f,y,.24f,0,.9f);
    float const enableAt[3]={.157f,y-.0145f,0},enableHalf[3]={.015f,.015f,0};
    NeuralEnableToggle=static_cast<NnButtonControl*>(CreateToggleButtonControl("NeuralEnableToggle",
        "Interface\\NeuroNet\\Inventory\\check.3db","Interface\\NeuroNet\\Inventory\\repairblackbox.3db",
        "ui_shipview_select",nullptr,enableAt,nullptr,enableHalf,0,0,0,0,PreferenceIds::NeuralEnabled,0x67a));
    if(!NeuralEnableToggle)return false;
    NeuralEnableToggle->SetProperty(0x35,1,0);GraphicsWidgets.push_back(NeuralEnableToggle);
    NeuralStrengthValue=text("NeuralStrengthValue",L"",.368f,y,.062f,1,.85f);
    float const sliderPosition[3]={.19f,y-.007f,-1.f};
    NeuralStrengthSlider=CreateUIScroll("NeuralStrengthSlider",sliderPosition,.17f,.014f,0,100,1,1);
    if(!label||!NeuralStrengthValue||!NeuralStrengthSlider)return false;
    NeuralStrengthSlider->SetProperty(0x37,0,100);
    NeuralStrengthSlider->SetStepMode(true);NeuralStrengthSlider->SetPageField(1.f);
    GraphicsWidgets.push_back(NeuralStrengthSlider);
#endif
    GraphicsHint=text("GraphicsRestartHint",L"",-.11f,hintY,.54f,0,.85f);
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
    ColorGradeCell.Value->SetText(GradeText(ColorGradeValue).c_str());
    unsigned hint=PreferenceIds::ColorGradeHint;
#ifdef FREELANCER_DLSS5
    if(NeuralEnableToggle)NeuralEnableToggle->SetProperty(0x30,NeuralEnabled,0);
    if(NeuralStrengthSlider)NeuralStrengthSlider->SetActiveField(NeuralEnabled);
    if(NeuralStrengthSlider)NeuralStrengthSlider->SetProperty(0x38,NeuralStrength,0);
    if(NeuralStrengthValue)NeuralStrengthValue->SetText((std::to_wstring(NeuralStrength)+L"%").c_str());
#endif
    GraphicsHint->SetText(IdText(pending ? PreferenceIds::GraphicsRestartPending : hint).c_str());
    GraphicsHint->TextColour=pending?G_NnPaletteArgb_679ba4:G_NnPaletteArgb_679b94;
}
void NnPreferences::SnapshotGraphics()
{
    ColorGradeValue=ColorGradeOriginal=ColorGrade::ConfiguredPreset();ColorGrade::Cancel();
#ifdef FREELANCER_DLSS5
    NeuralEnabled=NeuralEnabledOriginal=BaseNeural::ConfiguredEnabled();
    NeuralStrength=NeuralStrengthOriginal=BaseNeural::ConfiguredStrengthPercent();
    BaseNeural::CancelStrengthPreview();
#endif
    for (int i=0;i<GraphicsSettings::Count;++i)
        GraphicsOriginal[i]=GraphicsValues[i]=GraphicsSettings::Get(i,true);
    RefreshGraphicsRows();
}
void NnPreferences::CommitGraphics()
{
    ColorGrade::Commit(ColorGradeValue);
#ifdef FREELANCER_DLSS5
    BaseNeural::CommitEnabled(NeuralEnabled);
    BaseNeural::CommitStrength(NeuralStrength);
#endif
    for (int i=0;i<GraphicsSettings::Count;++i) GraphicsSettings::Set(i,GraphicsValues[i]);
}
void NnPreferences::RevertGraphics()
{
    ColorGradeValue=ColorGradeOriginal;ColorGrade::Preview(ColorGradeValue);
#ifdef FREELANCER_DLSS5
    NeuralEnabled=NeuralEnabledOriginal;BaseNeural::PreviewEnabled(NeuralEnabled);
    NeuralStrength=NeuralStrengthOriginal;
    BaseNeural::PreviewStrength(NeuralStrength);
#endif
    for (int i=0;i<GraphicsSettings::Count;++i) GraphicsValues[i]=GraphicsOriginal[i];
    if (GraphicsDropdown) GraphicsDropdown->Close();
    GraphicsDropdownRow=-1;
    RefreshGraphicsRows();
}
bool NnPreferences::GraphicsDirty() const
{
    if(ColorGradeValue!=ColorGradeOriginal)return true;
#ifdef FREELANCER_DLSS5
    if(NeuralEnabled!=NeuralEnabledOriginal)return true;
    if(NeuralStrength!=NeuralStrengthOriginal)return true;
#endif
    for (int i=0;i<GraphicsSettings::Count;++i) if (GraphicsValues[i]!=GraphicsOriginal[i]) return true;
    return false;
}
bool NnPreferences::GraphicsProperty(int msg, Win3D* source, uintptr_t value)
{
    // The in-game dialog never runs the main-menu opening animation: Anim stays -2.
    if (CurPage!=1 || bFlipping || bConfirmMode || bVideoConfirm || (!bInGame && Anim<0)) return false;
#ifdef FREELANCER_DLSS5
    if(NeuralEnableToggle&&source==NeuralEnableToggle)
    {
        if(msg==0x30){NeuralEnabled=value==0;BaseNeural::PreviewEnabled(NeuralEnabled);RefreshGraphicsRows();UpdateDirty(-1,-1.f);}
        return true;
    }
    if(NeuralStrengthSlider&&source==NeuralStrengthSlider)
    {
        if(msg==0x3e)
        {
            NeuralStrength=value>100?100:static_cast<int>(value);
            BaseNeural::PreviewStrength(NeuralStrength);
            RefreshGraphicsRows();UpdateDirty(-1,-1.f);
        }
        return true;
    }
#endif
    if (source==GraphicsDropdown && msg==0x3e)
    {
        int const row=GraphicsDropdownRow;
        GraphicsDropdown->Close();GraphicsDropdownRow=-1;
        if(row==GraphicsSettings::Count){
            if(value<=3){ColorGradeValue=int(value);ColorGrade::Preview(ColorGradeValue);RefreshGraphicsRows();UpdateDirty(-1,-1.f);}
            return true;
        }
        if (row<0 || row>=GraphicsSettings::Count || value>unsigned(GraphicsSettings::Maximum(row))) return true;
        int const selected=int(value)+(row==GraphicsSettings::FpsLimit ? 1 : 0);
        if (selected>GraphicsSettings::Maximum(row)) return true;
        GraphicsValues[row]=selected;
        RefreshGraphicsRows();UpdateDirty(-1,-1.f);return true;
    }
    if (source==DefaultsButton && msg==0x26)
    {
        ColorGradeValue=ColorGrade::DefaultPreset();ColorGrade::Preview(ColorGradeValue);
#ifdef FREELANCER_DLSS5
        NeuralEnabled=false;BaseNeural::PreviewEnabled(false);
        NeuralStrength=BaseNeural::DefaultStrengthPercent();
        BaseNeural::PreviewStrength(NeuralStrength);
#endif
        for (int i=0;i<GraphicsSettings::Count;++i) GraphicsValues[i]=GraphicsSettings::Default(i);
        RefreshGraphicsRows(); // continue into the native defaults handler
        return false;
    }
    if(source==ColorGradeCell.Choice){
        if(msg==0x26){
            if(VideoModeDropdown)VideoModeDropdown->Close();
            GraphicsDropdown->Close();GraphicsDropdownRow=-1;
            std::vector<std::wstring> choices;for(int i=0;i<4;i++)choices.push_back(GradeText(i));
            if(GraphicsDropdown->Open(.181f,RowY(GraphicsSettings::Count,bInGame!=0),.242f,choices,ColorGradeValue))GraphicsDropdownRow=GraphicsSettings::Count;
        }
        return true;
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
    if(ColorGradeCell.Choice&&(ColorGradeCell.Choice->Flags&kWin3DVisible))DrawNnDropdownCaret(ColorGradeCell.Choice);
    for (auto const& cell:GraphicsCells)
        if (cell.Choice && (cell.Choice->Flags&kWin3DVisible)) DrawNnDropdownCaret(cell.Choice);
    if (GraphicsDropdown) GraphicsDropdown->Draw();
}
