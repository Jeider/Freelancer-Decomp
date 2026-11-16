#include "nn_preferences.h"
#include "nn_button_control.h"
#include "nn_text_control.h"
#include "nn_dropdown.h"
#include "wire_controls.h"
#include "nn_ui_pulse.h"
#include "ids_strings.h"
#include "hud_interface_ids.h"
#include "color_grade_preferences.h"
#include "native_subtitles.h"
#include "ui_scroll.h"
#include <cstring>
#include <string>
#ifdef FREELANCER_DLSS5
#include "base_neural_preferences.h"
#endif

namespace
{
    void Visible(WinControl* control, bool visible) { if (control) control->SetProperty(1,!visible,0); }
    float DetailRowY(int row, bool inGame)
    {
        // Keep the first row below the tabs, including its full text/button height.
        // Spread the eleven advanced rows down to the restart hint, leaving room
        // for the last control's height and the preset buttons below it.
        return (inGame ? .1553125f : .165078125f) - row * .0351f;
    }
    float MainRowY(int row, bool inGame)
    {
        // Continue Monitor immediately after resolution and gamma.
        return (inGame ? .195f : .205f) - (row + 3) * .035f;
    }
    bool MainSetting(int setting)
    { return setting==GraphicsSettings::VSync || setting==GraphicsSettings::FpsLimit; }
    constexpr float GraphicsColumnShift=.03f;
    float ColumnShift(int setting) { return MainSetting(setting)?0.f:GraphicsColumnShift; }
    constexpr int GraphicsVisibleRows=11;
    constexpr int GraphicsOrder[]={GraphicsSettings::Shadows,GraphicsSettings::Relief,GraphicsSettings::Highlights,
        GraphicsSettings::Reflections,GraphicsSettings::Anisotropy,GraphicsSettings::Antialiasing,
        GraphicsSettings::Nebulae,GraphicsSettings::WeaponLights,GraphicsSettings::Anomalies,
        GraphicsSettings::TradeLane,GraphicsSettings::Hyperspace,-1,GraphicsSettings::Interiors,GraphicsSettings::Hair};
    // The separator occupies its own scroll row, leaving space on both sides.
    constexpr int GraphicsSeparatorRow=11;
    constexpr int GraphicsRowCount=sizeof(GraphicsOrder)/sizeof(GraphicsOrder[0]);
    int GraphicsRow(int setting)
    {
        for(int row=0;row<GraphicsRowCount;++row)if(GraphicsOrder[row]==setting)return row;
        return -1;
    }
    float SettingRowY(int setting, bool inGame, int first=0)
    {
        if(MainSetting(setting)) return MainRowY(setting==GraphicsSettings::VSync?0:1,inGame)+.0135f;
        return DetailRowY(GraphicsRow(setting)-first,inGame);
    }
    bool SettingOnPage(int setting,int page,int tab)
    { return MainSetting(setting) ? page==1 : page==2 && tab==0; }
    std::wstring IdText(unsigned id)
    {
        wchar_t text[256] = {};
        GetIdsStringWWithRawFallback(id, text, 256);
        for(auto& c:text) {
            if((c>=L'a'&&c<=L'z') || (c>=L'\u0430'&&c<=L'\u044f')) c-=32;
            else if(c==L'\u0451') c=L'\u0401';
        }
        return text;
    }
    std::wstring Label(int setting)
    {
        if(setting==GraphicsSettings::Hair)return L"\u0412\u041e\u041b\u041e\u0421\u042b \u041f\u0415\u0420\u0421\u041e\u041d\u0410\u0416\u0415\u0419";
        if(setting==GraphicsSettings::TradeLane)return IdText(PreferenceIds::GraphicsTradeLane);
        if(setting==GraphicsSettings::Hyperspace)return IdText(PreferenceIds::GraphicsHyperspace);
        constexpr int ids[]={PreferenceIds::GraphicsShadows,PreferenceIds::GraphicsSurfaceRelief,PreferenceIds::GraphicsHighlights,
            PreferenceIds::GraphicsReflections,PreferenceIds::GraphicsAnisotropy,PreferenceIds::GraphicsAntialiasing,
            PreferenceIds::GraphicsNebulae,PreferenceIds::GraphicsVsync,PreferenceIds::GraphicsFpsLimit,
            PreferenceIds::GraphicsWeaponLights,PreferenceIds::GraphicsAnomalies,PreferenceIds::GraphicsInteriors};
        return IdText(ids[setting]);
    }
    std::wstring ValueText(int setting, int value)
    {
        using namespace GraphicsSettings;
        if (((setting==Interiors || setting==Relief || setting==Highlights || setting==TradeLane || setting==Hyperspace) && value==0) || (setting==Anomalies && value==1))
            return IdText(PreferenceIds::GraphicsStandard);
        if (Toggle(setting)) return IdText(value ? PreferenceIds::GraphicsOn : PreferenceIds::GraphicsOff);
        if (setting==Shadows || setting==Nebulae || setting==Anomalies || setting==Interiors || setting==Relief || setting==Highlights || setting==Hair || setting==TradeLane || setting==Hyperspace)
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
        std::wstring text=value;
        for(auto& c:text) {
            if((c>=L'a'&&c<=L'z') || (c>=L'\u0430'&&c<=L'\u044f')) c-=32;
            else if(c==L'\u0451') c=L'\u0401';
        }
        float const at[3]={x,y,0};
        auto* control=static_cast<NnTextControl*>(CreateTextControl(name,"ItemName",at,nullptr,width,.027f,scale,0,align,0,1));
        if (control) { control->SetText(text.c_str());control->Flags&=~kWin3DPickable;GraphicsWidgets.push_back(control); }
        return control;
    };
    for (int i=0;i<GraphicsSettings::Count;++i)
    {
        GraphicsValues[i]=GraphicsSettings::Get(i,true);
        GraphicsOriginal[i]=GraphicsValues[i];
        auto& cell=GraphicsCells[i];
        char name[40];
        sprintf_s(name,"GraphicsLabel%d",i);
        float const shift=ColumnShift(i);
        cell.Label=text(name,Label(i).c_str(),-.11f,SettingRowY(i,bInGame!=0),.29f-shift,0,.9f);
        sprintf_s(name,"GraphicsValue%d",i);
        cell.Value=text(name,L"",.188f-shift,SettingRowY(i,bInGame!=0),.207f,1,.9f);
        float const at[3]={.302f-shift,SettingRowY(i,bInGame!=0)-.0145f,0},half[3]={.121f,.0145f,0};
        if (GraphicsSettings::Toggle(i))
        {
            float const toggleAt[3]={.405f-shift,at[1],0},toggleHalf[3]={.015f,.015f,0};
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
    float const separatorAt[3]={.1565f-GraphicsColumnShift*.5f,0,0};
    float const separatorHalf[3]={.2665f-GraphicsColumnShift*.5f,0,0};
    GraphicsInteriorSeparator=CreateWireStaticControl("GraphicsInteriorSeparator",separatorAt,separatorHalf,0,0,0,1);
    if(!GraphicsInteriorSeparator)return false;
    GraphicsInteriorSeparator->Flags&=~kWin3DPickable;
    GraphicsWidgets.push_back(GraphicsInteriorSeparator);
    float const scrollAt[3]={.438f-GraphicsColumnShift,DetailRowY(0,bInGame!=0),-1.f};
    GraphicsScroll=CreateUIScroll("GraphicsScroll",scrollAt,.015f,.386f,0,GraphicsRowCount,GraphicsVisibleRows,0);
    if(!GraphicsScroll)return false;
    GraphicsScroll->SetProperty(0x37,0,GraphicsRowCount-1);
    // A list needs a proportional thumb. Step mode is for sliders and forces
    // its length to zero on the next Relayout (e.g. the first wheel event).
    GraphicsScroll->SetStepMode(false);
    GraphicsWidgets.push_back(GraphicsScroll);
    SubtitlesValue=SubtitlesOriginal=NativeSubtitles::CutsceneEnabled();
    for(int i=0;i<2;++i) {
        auto& cell=SubtitleCells[i];
        float const y=MainRowY(3+i,bInGame!=0)+.0135f;
        cell.Label=text(i?"SpaceSubtitlesLabel":"CutsceneSubtitlesLabel",
            i?L"\u0421\u0443\u0431\u0442\u0438\u0442\u0440\u044b \u0432 \u043a\u043e\u0441\u043c\u043e\u0441\u0435":L"\u0421\u0443\u0431\u0442\u0438\u0442\u0440\u044b \u0432 \u043a\u0430\u0442\u0441\u0446\u0435\u043d\u0430\u0445",-.11f,y,.39f,0,.9f);
        float const at[]={.405f,y-.0145f,0},half[]={.015f,.015f,0};
        cell.Toggle=static_cast<NnButtonControl*>(CreateToggleButtonControl(i?"SpaceSubtitlesToggle":"CutsceneSubtitlesToggle",
            "Interface\\NeuroNet\\Inventory\\check.3db","Interface\\NeuroNet\\Inventory\\repairblackbox.3db",
            "ui_shipview_select",nullptr,at,nullptr,half,0,0,0,0,0x65f,0x67a));
        if(!cell.Label||!cell.Toggle)return false;
        cell.Toggle->SetProperty(0x35,1,0);
        memcpy(cell.Toggle->Colour,&G_NnPaletteArgb_679b94,4);
        GraphicsWidgets.push_back(cell.Toggle);
        if(i) {
            cell.Label->TextColour=G_NnPaletteArgb_679b94;
            cell.Toggle->ButtonBits2&=~2u;
            cell.Toggle->Flags&=~kWin3DPickable;
        }
    }
    float hintY=-.23f;
    ColorGradeValue=ColorGradeOriginal=ColorGrade::ConfiguredPreset();
    float const gradeY=MainRowY(2,bInGame!=0);
    float const gradeLabelAt[3]={0.f,gradeY,0};
    ColorGradeCell.Label=static_cast<NnTextControl*>(CreateTextControl("ColorGradeLabel","SubHeader",gradeLabelAt,nullptr,.215f,.03f,1.f,0,0,0,0));
    if(ColorGradeCell.Label){ColorGradeCell.Label->SetText(IdText(PreferenceIds::ColorGradeLabel).c_str());ColorGradeCell.Label->SetProperty(0x24,1,0);ColorGradeCell.Label->Flags&=~kWin3DPickable;GraphicsWidgets.push_back(ColorGradeCell.Label);}
    ColorGradeCell.Value=text("ColorGradeValue",L"",.188f,gradeY+.0135f,.207f,1,.9f);
    float const gradeAt[3]={.302f,gradeY-.001f,0},gradeHalf[3]={.121f,.0145f,0};
    ColorGradeCell.Choice=static_cast<WireButtonControl*>(CreateWireButtonControl("ColorGradeChoice","ui_select_item",gradeAt,gradeHalf,0,0,0,0,0xf));
    if(!ColorGradeCell.Label||!ColorGradeCell.Value||!ColorGradeCell.Choice)return false;
    GraphicsWidgets.push_back(ColorGradeCell.Choice);
#ifdef FREELANCER_DLSS5
    NeuralStrength=NeuralStrengthOriginal=BaseNeural::ConfiguredStrengthPercent();
    NeuralEnabled=NeuralEnabledOriginal=BaseNeural::ConfiguredEnabled();
    float const y=MainRowY(5,bInGame!=0);
    float const neuralLabelAt[3]={0.f,y,0};
    NeuralStrengthLabel=static_cast<NnTextControl*>(CreateTextControl("NeuralStrengthLabel","SubHeader",neuralLabelAt,nullptr,.215f,.03f,1.f,0,0,0,0));
    if(NeuralStrengthLabel){NeuralStrengthLabel->SetText(IdText(PreferenceIds::NeuralStrength).c_str());NeuralStrengthLabel->SetProperty(0x24,1,0);NeuralStrengthLabel->Flags&=~kWin3DPickable;GraphicsWidgets.push_back(NeuralStrengthLabel);}
    float const enableAt[3]={.405f,y-.001f,0},enableHalf[3]={.015f,.015f,0};
    NeuralEnableToggle=static_cast<NnButtonControl*>(CreateToggleButtonControl("NeuralEnableToggle",
        "Interface\\NeuroNet\\Inventory\\check.3db","Interface\\NeuroNet\\Inventory\\repairblackbox.3db",
        "ui_shipview_select",nullptr,enableAt,nullptr,enableHalf,0,0,0,0,PreferenceIds::NeuralEnabled,0x67a));
    if(!NeuralEnableToggle)return false;
    NeuralEnableToggle->SetProperty(0x35,1,0);GraphicsWidgets.push_back(NeuralEnableToggle);
    NeuralStrengthValue=text("NeuralStrengthValue",L"",.12f,y+.0135f,.06f,2,.8f);
    float const sliderPosition[3]={.19f,y+.007f,-1.f};
    NeuralStrengthSlider=CreateUIScroll("NeuralStrengthSlider",sliderPosition,.18f,.014f,0,100,1,1);
    if(!NeuralStrengthLabel||!NeuralStrengthValue||!NeuralStrengthSlider)return false;
    NeuralStrengthSlider->SetProperty(0x37,0,100);
    NeuralStrengthSlider->SetStepMode(true);NeuralStrengthSlider->SetPageField(1.f);
    GraphicsWidgets.push_back(NeuralStrengthSlider);
#endif
    GraphicsHint=text("GraphicsRestartHint",L"",-.11f,hintY,.54f,0,.85f);
    GraphicsDropdown=CreateNnDropdownPopup(this);
    if (!GraphicsHint || !GraphicsDropdown) return false;
    for (int tab=0;tab<2;++tab)
    {
        char name[40];
        sprintf_s(name,"GraphicsTab%d",tab);
        float const at[3]={-.02f+tab*.28f,.205f,0},half[3]={.12f,.014f,0};
        GraphicsTabButtons[tab]=static_cast<WireButtonControl*>(CreateWireButtonControl(name,"ui_select_item",at,half,0,0,0,0,0xf));
        sprintf_s(name,"GraphicsTabText%d",tab);
        unsigned const id=tab?PreferenceIds::GraphicsDisplayTab:PreferenceIds::GraphicsImageTab;
        GraphicsTabTexts[tab]=text(name,IdText(id).c_str(),at[0]-.12f,.218f,.24f,1,.75f);
        if (!GraphicsTabButtons[tab] || !GraphicsTabTexts[tab]) return false;
        GraphicsWidgets.push_back(GraphicsTabButtons[tab]);
    }
    constexpr int presetIds[]={PreferenceIds::GraphicsAllOff,PreferenceIds::GraphicsLow,
        PreferenceIds::GraphicsMedium,PreferenceIds::GraphicsHigh};
    for(int preset=0;preset<4;++preset) {
        char name[40];sprintf_s(name,"GraphicsPreset%d",preset);
        float const left=-.14f+preset*.143f;
        float const at[3]={left+.067f,-.295f,0},half[3]={.067f,.015f,0};
        GraphicsPresetButtons[preset]=static_cast<WireButtonControl*>(CreateWireButtonControl(name,"ui_select_item",at,half,0,0,0,0,0xf));
        sprintf_s(name,"GraphicsPresetText%d",preset);
        GraphicsPresetTexts[preset]=text(name,IdText(presetIds[preset]).c_str(),left,-.2815f,.134f,1,.85f);
        if(!GraphicsPresetButtons[preset] || !GraphicsPresetTexts[preset]) return false;
        GraphicsWidgets.push_back(GraphicsPresetButtons[preset]);
    }
    SetGraphicsHidden(true);
    return true;
}

void NnPreferences::SetGraphicsHidden(bool hidden)
{
    if (GraphicsDropdown) GraphicsDropdown->Close();
    GraphicsDropdownRow=-1;
    if (hidden)
    {
        for (auto* control:GraphicsWidgets) Visible(control,false);
        return;
    }
    ApplyGraphicsTab();
}
void NnPreferences::ApplyGraphicsTab()
{
    bool const main=CurPage==1;
    bool const detail=CurPage==2;
    bool const image=detail && GraphicsTab==0;
    for (int i=0;i<GraphicsSettings::Count;++i)
    {
        auto& cell=GraphicsCells[i];
        int const row=GraphicsRow(i);
        bool const show=SettingOnPage(i,CurPage,GraphicsTab) &&
            (MainSetting(i)||(row>=GraphicsFirstRow&&row<GraphicsFirstRow+GraphicsVisibleRows));
        float const y=SettingRowY(i,bInGame!=0,GraphicsFirstRow);
        // Creation coordinates are local Offset, not SetPosition's parent anchor.
        // Updating the anchor with x/y would add the same coordinates twice in
        // retail text, wire and toggle controls (including the two Main rows).
        auto moveCell=[&](WinControl* control,float x,float cy){if(control)control->SetOffset(x,cy,control->Offset[2]);};
        float const shift=ColumnShift(i);
        moveCell(cell.Label,-.11f,y);moveCell(cell.Value,.188f-shift,y);
        moveCell(cell.Toggle,.405f-shift,y-.0145f);moveCell(cell.Choice,.302f-shift,y-.0145f);
        Visible(cell.Label,show);
        Visible(cell.Value,show);
        Visible(cell.Toggle,show);
        Visible(cell.Choice,show);
    }
    Visible(GraphicsScroll,image && GraphicsRowCount>GraphicsVisibleRows);
    int const separatorRow=GraphicsSeparatorRow-GraphicsFirstRow;
    if(GraphicsInteriorSeparator)GraphicsInteriorSeparator->SetOffset(.1565f-GraphicsColumnShift*.5f,
        DetailRowY(separatorRow,bInGame!=0)-.0145f,GraphicsInteriorSeparator->Offset[2]);
    Visible(GraphicsInteriorSeparator,image && separatorRow>=0 && separatorRow<GraphicsVisibleRows);
    for(auto& cell:SubtitleCells) { Visible(cell.Label,main);Visible(cell.Toggle,main); }
    Visible(ColorGradeCell.Label,main);
    Visible(ColorGradeCell.Value,main);
    Visible(ColorGradeCell.Choice,main);
#ifdef FREELANCER_DLSS5
    bool const neural=main;
    Visible(NeuralStrengthLabel,neural);
    Visible(NeuralEnableToggle,neural);
    Visible(NeuralStrengthSlider,neural);
    Visible(NeuralStrengthValue,neural);
#endif
    for (int tab=0;tab<2;++tab)
    {
        Visible(GraphicsTabButtons[tab],detail);
        Visible(GraphicsTabTexts[tab],detail);
        if (GraphicsTabTexts[tab]) GraphicsTabTexts[tab]->TextColour=tab==GraphicsTab?G_NnPaletteArgb_679ba4:G_NnPaletteArgb_679bb0;
    }
    Visible(DefaultsButton,!image);Visible(DefaultsText,!image);
    Visible(CancelButton,!image);Visible(CancelText,!image);
    for(int preset=0;preset<4;++preset) {
        Visible(GraphicsPresetButtons[preset],image);
        Visible(GraphicsPresetTexts[preset],image);
    }
    Visible(GraphicsHint,image); // Main controls apply live; reserve the footer for customization.
    if (detail) SetOptionRowsHidden(image);
    RefreshGraphicsRows();
}
void NnPreferences::RefreshGraphicsRows()
{
    if (!GraphicsHint) return;
    for(int preset=0;preset<4;++preset) {
        bool selected=true;
        for(int i=0;i<GraphicsSettings::Count;++i) {
            int const expected=GraphicsSettings::PresetValue(i,preset);
            if(expected>=0 && GraphicsValues[i]!=expected) selected=false;
        }
        if(GraphicsPresetTexts[preset]) GraphicsPresetTexts[preset]->TextColour=selected?G_NnPaletteArgb_679ba4:G_NnPaletteArgb_679bb0;
    }
    bool pending=false;
    for (int i=0;i<GraphicsSettings::Count;++i)
    {
        auto& cell=GraphicsCells[i];
        cell.Value->SetText(ValueText(i,GraphicsValues[i]).c_str());
        if (cell.Toggle) cell.Toggle->SetProperty(0x30,GraphicsValues[i]!=0,0);
        pending|=GraphicsValues[i]!=GraphicsSettings::Get(i);
    }
    SubtitleCells[0].Toggle->SetProperty(0x30,SubtitlesValue,0);
    SubtitleCells[1].Toggle->SetProperty(0x30,0,0);
    ColorGradeCell.Value->SetText(GradeText(ColorGradeValue).c_str());
    unsigned hint=PreferenceIds::GraphicsRestartHint;
#ifdef FREELANCER_DLSS5
    if(NeuralEnableToggle)NeuralEnableToggle->SetProperty(0x30,NeuralEnabled,0);
    if(NeuralStrengthSlider)NeuralStrengthSlider->SetActiveField(NeuralEnabled);
    if(NeuralStrengthSlider)NeuralStrengthSlider->SetProperty(0x38,NeuralStrength,0);
    if(NeuralStrengthValue)NeuralStrengthValue->SetText((NeuralEnabled ? std::to_wstring(NeuralStrength)+L"%" : IdText(PreferenceIds::GraphicsOff)).c_str());
#endif
    GraphicsHint->SetText(IdText(pending ? PreferenceIds::GraphicsRestartPending : hint).c_str());
    GraphicsHint->TextColour=pending?G_NnPaletteArgb_679ba4:G_NnPaletteArgb_679b94;
}
void NnPreferences::SnapshotGraphics()
{
    SubtitlesValue=SubtitlesOriginal=NativeSubtitles::CutsceneEnabled();
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
    NativeSubtitles::SetCutsceneEnabled(SubtitlesValue);
    ColorGrade::Commit(ColorGradeValue);
#ifdef FREELANCER_DLSS5
    BaseNeural::CommitEnabled(NeuralEnabled);
    BaseNeural::CommitStrength(NeuralStrength);
#endif
    for (int i=0;i<GraphicsSettings::Count;++i) GraphicsSettings::Set(i,GraphicsValues[i]);
}
void NnPreferences::RevertGraphics()
{
    SubtitlesValue=SubtitlesOriginal;
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
    if(SubtitlesValue!=SubtitlesOriginal)return true;
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
    if ((CurPage!=1 && CurPage!=2) || bFlipping || bConfirmMode || bVideoConfirm || (!bInGame && Anim<0)) return false;
    if(source==GraphicsScroll && CurPage==2 && GraphicsTab==0){
        if(msg==0x3e){
            GraphicsFirstRow=int(value);
            if(GraphicsFirstRow<0)GraphicsFirstRow=0;
            if(GraphicsFirstRow>GraphicsRowCount-GraphicsVisibleRows)GraphicsFirstRow=GraphicsRowCount-GraphicsVisibleRows;
            GraphicsScroll->SetProperty(0x38,GraphicsFirstRow,0);
            if(GraphicsDropdown)GraphicsDropdown->Close();
            GraphicsDropdownRow=-1;ApplyGraphicsTab();
        }
        return true;
    }
#ifdef FREELANCER_DLSS5
    if(CurPage==1 && NeuralEnableToggle&&source==NeuralEnableToggle)
    {
        if(msg==0x30) {
            NeuralEnabled=value==0;BaseNeural::PreviewEnabled(NeuralEnabled);
            RefreshGraphicsRows();UpdateDirty(-1,-1.f);
        }
        return true;
    }
    if(CurPage==1 && NeuralStrengthSlider&&source==NeuralStrengthSlider)
    {
        if(msg==0x3e && NeuralEnabled)
        {
            NeuralStrength=value>100?100:static_cast<int>(value);
            BaseNeural::PreviewStrength(NeuralStrength);
            RefreshGraphicsRows();UpdateDirty(-1,-1.f);
        }
        return true;
    }
#endif
    if(CurPage==1 && source==SubtitleCells[0].Toggle) {
        if(msg==0x30) { SubtitlesValue=value==0;RefreshGraphicsRows();UpdateDirty(-1,-1.f); }
        return true;
    }
    if(source==SubtitleCells[1].Toggle) return true;
    for (int tab=0;tab<2;++tab) if (CurPage==2 && msg==0x26 && source==GraphicsTabButtons[tab])
    {
        if (GraphicsDropdown) GraphicsDropdown->Close();
        GraphicsDropdownRow=-1;
        GraphicsTab=tab;
        ApplyGraphicsTab();
        return true;
    }
    for(int preset=0;preset<4;++preset) if(CurPage==2 && GraphicsTab==0 && source==GraphicsPresetButtons[preset]) {
        if(msg==0x26) {
            if(GraphicsDropdown) GraphicsDropdown->Close();
            GraphicsDropdownRow=-1;
            for(int i=0;i<GraphicsSettings::Count;++i) {
                int const setting=GraphicsSettings::PresetValue(i,preset);
                if(setting>=0) GraphicsValues[i]=setting;
            }
            RefreshGraphicsRows();UpdateDirty(-1,-1.f);
        }
        return true;
    }
    if(CurPage==2 && GraphicsTab==0 && (source==DefaultsButton || source==CancelButton)) return true;
    if (source==GraphicsDropdown && msg==0x3e)
    {
        int const row=GraphicsDropdownRow;
        GraphicsDropdown->Close();GraphicsDropdownRow=-1;
        if(CurPage==1 && row==GraphicsSettings::Count){
            if(value<=3){ColorGradeValue=int(value);ColorGrade::Preview(ColorGradeValue);RefreshGraphicsRows();UpdateDirty(-1,-1.f);}
            return true;
        }
        if (row<0 || row>=GraphicsSettings::Count || !SettingOnPage(row,CurPage,GraphicsTab) || value>unsigned(GraphicsSettings::Maximum(row))) return true;
        int const selected=int(value)+GraphicsSettings::Minimum(row);
        if (selected>GraphicsSettings::Maximum(row)) return true;
        GraphicsValues[row]=selected;
        RefreshGraphicsRows();UpdateDirty(-1,-1.f);return true;
    }
    if (source==DefaultsButton && msg==0x26)
    {
        if(CurPage==1) SubtitlesValue=true;
        ColorGradeValue=ColorGrade::DefaultPreset();ColorGrade::Preview(ColorGradeValue);
#ifdef FREELANCER_DLSS5
        if(NeuralEnabled)
        {
            NeuralStrength=BaseNeural::DefaultStrengthPercent();
            BaseNeural::PreviewStrength(NeuralStrength);
        }
#endif
        for (int i=0;i<GraphicsSettings::Count;++i) if(MainSetting(i)==(CurPage==1)) GraphicsValues[i]=GraphicsSettings::Default(i);
        RefreshGraphicsRows(); // continue into the native defaults handler
        return false;
    }
    if(CurPage==1 && source==ColorGradeCell.Choice){
        if(msg==0x26){
            if(VideoModeDropdown)VideoModeDropdown->Close();
            GraphicsDropdown->Close();GraphicsDropdownRow=-1;
            std::vector<std::wstring> choices;for(int i=0;i<4;i++)choices.push_back(GradeText(i));
            if(GraphicsDropdown->Open(.181f,MainRowY(2,bInGame!=0)+.0135f,.242f,choices,ColorGradeValue))GraphicsDropdownRow=GraphicsSettings::Count;
        }
        return true;
    }
    for (int i=0;i<GraphicsSettings::Count;++i)
    {
        auto const& cell=GraphicsCells[i];
        if (SettingOnPage(i,CurPage,GraphicsTab) && cell.Toggle && source==cell.Toggle)
        {
            if (msg==0x30) {GraphicsValues[i]=value==0?1:0;RefreshGraphicsRows();UpdateDirty(-1,-1.f);}
            return true;
        }
        if (SettingOnPage(i,CurPage,GraphicsTab) && cell.Choice && source==cell.Choice)
        {
            if (msg!=0x26) return true;
            if (VideoModeDropdown) VideoModeDropdown->Close();
            GraphicsDropdown->Close();GraphicsDropdownRow=-1;
            std::vector<std::wstring> choices;
            int const first=GraphicsSettings::Minimum(i);
            for (int valueIndex=first;valueIndex<=GraphicsSettings::Maximum(i);++valueIndex) choices.push_back(ValueText(i,valueIndex));
            if (GraphicsDropdown->Open(.181f-ColumnShift(i),SettingRowY(i,bInGame!=0,GraphicsFirstRow),.242f,choices,GraphicsValues[i]-first)) GraphicsDropdownRow=i;
            return true;
        }
    }
    return false;
}
void NnPreferences::DrawGraphicsDropdown()
{
    if ((CurPage!=1 && CurPage!=2) || bConfirmMode || bVideoConfirm || bFlipping) return;
    if(ColorGradeCell.Choice&&(ColorGradeCell.Choice->Flags&kWin3DVisible))DrawNnDropdownCaret(ColorGradeCell.Choice);
    for (auto const& cell:GraphicsCells)
        if (cell.Choice && (cell.Choice->Flags&kWin3DVisible)) DrawNnDropdownCaret(cell.Choice);
    if (GraphicsDropdown) GraphicsDropdown->Draw();
}
