#include "page_customization.h"
#include "customization_text.h"
#include "type_select.h"
#include "nn_static_control.h"
#include "ui_win_deform.h"
#include "ui_text_msg_button.h"
#include "ui_page_desc.h"
#include "space_scene_obj_draw.h"
#include "common_reputation.h"
#include "player_customization.h"
#include "menu_ui_init.h"
#include "win3d_immediate.h"
#include "win3d_renderables.h"
#include "star_sphere.h"
#include <wchar.h>

namespace {
void BeginOverlay()
{
    Win3DFlushBeforeOverlayDraw(); Win3DBeginDraw();
    float matrix[]={1,0,0,0,1,0,0,0,1,0,0,-1};
    Win3DBindModelview(nullptr,matrix);
    Win3DEnable(kWin3DBlend);
    Win3DSetBlendFunc(kWin3DBlendSrcAlpha,kWin3DBlendInvSrcAlpha);
}
void Rectangle(float x,float y,float width,float height,int mode)
{
    Win3DBegin(mode);
    Win3DVertex3f(x,y,0); Win3DVertex3f(x,y-height,0);
    Win3DVertex3f(x+width,y-height,0); Win3DVertex3f(x+width,y,0);
    Win3DEnd();
}
class SquareArrow : public TextMsgButton {
    void Draw() override {
        BeginOverlay();
        bool const hover=Win3DGetHover()==this;
        Win3DColor4f(.025f,.065f,.12f,.96f);
        Rectangle(Position[0],Position[1],Width,Height,kWin3DQuads);
        Win3DColor4f(hover?1.f:.40f,hover?.8f:.72f,hover?.25f:.90f,1);
        Rectangle(Position[0],Position[1],Width,Height,kWin3DLineLoop);
        TextMsgButton::Draw();
    }
};
// Draw the native panel explicitly before the model and text, regardless of Z sorting.
class CustomizationPanel : public NnStaticControl {
public:
    void Draw() override {}
    void DrawPanel() { NnStaticControl::Draw(); }
    void CreatePanel(Win3D* parent,char const* mesh,float y) {
        Create(parent,nullptr);
        float const zero[]={0,0,0},offset[]={0,y,-1};
        // Match NnPreferences::CreateStaticControl, including compound-instance
        // updates, material tint and depth-disabled rendering of every frame part.
        Init(mesh,offset,nullptr,zero,0,0,0,1,1,0,1,0,0,0,zero);
        Flags&=~kWin3DPickable;
    }
};
class CustomizationSubwindow : public Win3D {
    bool Slot23(unsigned msg,unsigned a,unsigned b) override {
        return Parent && Parent->Slot23(msg,a,b);
    }
};
class CustomizationPage : public Win3D, public EventHandler
{
    CustomizationPanel Shade, Background;
    CustomizationSubwindow BodyWindow, PortraitWindow;
    UiWinDeform Character, Portrait;
    TextWin BodyName, HatName, HelmetName, Notice;
    SquareArrow BodyLeft, BodyRight, HatLeft, HatRight, HelmetLeft, HelmetRight;
    UiTextMsgButton OpenPortrait, BackToBody, ApplyButton, CancelButton;
    PlayerCustomization::Selection Draft;
    bool PortraitOpen = false;
    bool PreviewValid = false;

    static constexpr float ContentRise=.035f;

    static void PositionAt(Win3D& widget, float x, float y) {
        float position[] = {x,y+ContentRise,-1.0f}; widget.SetPosition(position);
    }
    void Label(TextWin& label, Win3D* parent, wchar_t const* text, float x, float y, float width) {
        label.Create(parent,nullptr); label.Width=width; label.Height=.045f;
        label.SetFont("ButtonText",1.0f); label.SetText(text); PositionAt(label,x,y);
    }
    void Button(UiTextMsgButton& button, Win3D* parent, wchar_t const* text, int command,
                float x, float y, float width=.08f) {
        FUiPayloadTextMsgButton payload={width,.055f,const_cast<wchar_t*>(text),command,0,
                                         const_cast<char*>("<default>")};
        button.Create(parent,&payload); PositionAt(button,x,y);
    }
    void Button(SquareArrow& button,Win3D* parent,wchar_t const* text,int command,
                float x,float y,float width=.035f) {
        button.Init(parent,text,.035f,.035f,command);
        button.FieldE8=1;button.SetFlagsE4E5(1,1);PositionAt(button,x,y);
    }
    void PreviewPosition(UiWinDeform& preview, bool portrait) {
        preview.Width = .34f;
        preview.Height = portrait ? .40f : .48f;
        float matrix[] = {1,0,0,0,1,0,0,0,1,-.41f,.22f+ContentRise,-1};
        preview.SetTransform(matrix);
        SpaceCameraSetHalfFovX(&preview.Camera,12.0f);
        SpaceCameraSetNearFar(&preview.Camera,.1f,100.0f);
    }
    void Rebuild() {
        using namespace PlayerCustomization;
        BodyName.SetText(CustomizationText::Text(Bodies[Draft.Body].Label, Bodies[Draft.Body].EnglishLabel));
        HatName.SetText(CustomizationText::Text(Hats[Draft.Hat].Label, Hats[Draft.Hat].EnglishLabel));
        HelmetName.SetText(CustomizationText::Text(Helmets[Draft.Helmet].Label, Helmets[Draft.Helmet].EnglishLabel));
        Costume base = {}, comm = {};
        auto const* descriptions = GetCostumeDescriptions();
        PreviewValid = false;
        if (descriptions && descriptions->find_costume("trent")) {
            descriptions->get_costume("trent",base);
            comm = base;
            // Comm is a head-and-shoulders view with its own helmet, never the base hat.
            comm.AccessoryCount = 0;
            Apply(base,comm,Draft);
            for (int i=1;i<4;++i) comm.PartIds[i]=base.PartIds[i];
            bool const bodyOk=Character.SetCostume(base), portraitOk=Portrait.SetCostume(comm);
            PreviewValid=bodyOk && portraitOk;
            if (bodyOk) {
                Character.Body.PlayAnimation("Sc_MLBODY_STND_000LV_A_31",0,0,1,2);
                Character.Body.Advance(.1f);
            }
            if (portraitOk) {
                Portrait.Body.PlayAnimation("Sc_MLBODY_STND_000LV_A_31",0,0,1,2);
                Portrait.Body.Advance(.1f);
            }
        }
        ApplyButton.bInteractive=PreviewValid ? 1 : 0;
        Notice.SetText(PreviewValid ? CustomizationText::Text(L"\u041e\u0431\u0440\u0430\u0437 \u043f\u0440\u0438\u043c\u0435\u043d\u044f\u0435\u0442\u0441\u044f \u043f\u0440\u0438 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0435 \u0441\u044e\u0436\u0435\u0442\u043d\u043e\u0439 \u0438\u0433\u0440\u044b", L"Applied when you load a story game") :
                                     CustomizationText::Text(L"\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0437\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u043c\u043e\u0434\u0435\u043b\u044c. \u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0440\u0443\u0433\u043e\u0439 \u0432\u0430\u0440\u0438\u0430\u043d\u0442.", L"Could not load the model. Choose another option."));
    }
    void ShowPortrait(bool show) {
        PortraitOpen=show;
        BodyWindow.Flags=(BodyWindow.Flags & ~3) | (show ? 0 : 3);
        PortraitWindow.Flags=(PortraitWindow.Flags & ~3) | (show ? 3 : 0);
    }
public:
    bool Closed = false;
    // A subwindow forwards button commands but retains its own visibility subtree.
    bool Slot23(unsigned msg,unsigned a,unsigned b) override {
        if (msg!=0x3004 || Closed) return false;
        using namespace PlayerCustomization;
        PlayOrRewindUiSoundSlot(0);
        switch(a) {
        case 1: Draft.Body=(Draft.Body+_countof(Bodies)-1)%_countof(Bodies); break;
        case 2: Draft.Body=(Draft.Body+1)%_countof(Bodies); break;
        case 3: Draft.Hat=(Draft.Hat+_countof(Hats)-1)%_countof(Hats); break;
        case 4: Draft.Hat=(Draft.Hat+1)%_countof(Hats); break;
        case 5: Draft.Helmet=(Draft.Helmet+_countof(Helmets)-1)%_countof(Helmets); break;
        case 6: Draft.Helmet=(Draft.Helmet+1)%_countof(Helmets); break;
        case 7: ShowPortrait(true); return true;
        case 8: ShowPortrait(false); return true;
        case 9:
            if (PreviewValid && Save(Draft)) Closed=true;
            else Notice.SetText(CustomizationText::Text(L"\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0441\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c \u043e\u0431\u0440\u0430\u0437. \u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u043d\u0435 \u043f\u0440\u0438\u043c\u0435\u043d\u0435\u043d\u044b.", L"Could not save appearance. Settings were not applied."));
            return true;
        case 10: Closed=true; return true;
        default: return false;
        }
        Rebuild(); return true;
    }
    bool OnEvent(unsigned msg) override {
        if (msg!=0xf) return false;
        Closed=true;
        return true;
    }
    bool KeyEvent(unsigned key,unsigned char* modifiers) override {
        if (key==VK_ESCAPE && modifiers && (modifiers[0]&2)) { Closed=true; return true; }
        return false;
    }
    bool Create(Win3D* parent,void* data) override {
        Win3D::Create(parent,data);
        Closed=false; Draft=PlayerCustomization::Load();
        // Use the complete in-game settings frame at its native size and position.
        Shade.CreatePanel(this,"Interface\\NeuroNet\\MISC_bigblackplane.3db",0);
        Background.CreatePanel(this,
            "Interface\\NeuroNet\\Inventory\\FRONT_options_box2.cmp",-.075f);
        BodyWindow.Create(this,nullptr); PortraitWindow.Create(this,nullptr);
        Character.Create(&BodyWindow,nullptr); Portrait.Create(&PortraitWindow,nullptr);
        Character.PoseZ=-3.8f; Character.PoseHeight=-.9f;
        Portrait.PoseZ=-1.8f; Portrait.PoseHeight=-1.5f;
        PreviewPosition(Character,false); PreviewPosition(Portrait,true);
        Label(HatName,&BodyWindow,L"",.07f,.145f,.31f);
        Label(BodyName,&BodyWindow,L"",.07f,-.02f,.31f);
        Label(HelmetName,&PortraitWindow,L"",.07f,.085f,.31f);
        Label(Notice,this,L"",-.40f,-.235f,.85f);
        Button(HatLeft,&BodyWindow,L"<",3,.015f,.15f);
        Button(HatRight,&BodyWindow,L">",4,.395f,.15f);
        Button(BodyLeft,&BodyWindow,L"<",1,.015f,-.015f);
        Button(BodyRight,&BodyWindow,L">",2,.395f,-.015f);
        Button(HelmetLeft,&PortraitWindow,L"<",5,.015f,.09f);
        Button(HelmetRight,&PortraitWindow,L">",6,.395f,.09f);
        Button(OpenPortrait,&BodyWindow,CustomizationText::Text(L"\u041f\u043e\u0440\u0442\u0440\u0435\u0442 \u0441\u0432\u044f\u0437\u0438", L"Comm portrait"),7,.07f,-.17f,.28f);
        Button(BackToBody,&PortraitWindow,CustomizationText::Text(L"\u041a \u043f\u0435\u0440\u0441\u043e\u043d\u0430\u0436\u0443", L"Back to character"),8,.07f,-.17f,.28f);
        Button(ApplyButton,this,CustomizationText::Text(L"\u041f\u0440\u0438\u043c\u0435\u043d\u0438\u0442\u044c", L"Apply"),9,-.37f,-.285f,.28f);
        Button(CancelButton,this,CustomizationText::Text(L"\u041e\u0442\u043c\u0435\u043d\u0430", L"Cancel"),10,.05f,-.285f,.28f);
        Notice.SetFont("ButtonText",.8f);
        ShowPortrait(data && *static_cast<bool*>(data)); Rebuild();
        RegisterEvent(0xf); Win3DPushCapture(this); return true;
    }
    void Update() override {
        PreviewPosition(Character,false); PreviewPosition(Portrait,true);
        Win3D::Update();
    }
    void Draw() override {
        Win3DFlushBeforeOverlayDraw();
        Shade.DrawPanel();
        Win3DFlushBeforeOverlayDraw();
        Background.DrawPanel();
        Win3DFlushBeforeOverlayDraw();
        Win3D::Draw();
    }
    void Destroy() override {
        Win3DRemoveCapture(this);
        UnregisterAllEvents();
        Character.Body.Reset(); Portrait.Body.Reset();
        // Destroy unregisters and unlinks children; do not advance a detached sibling.
        while (BodyWindow.ChildHead) BodyWindow.ChildHead->Destroy();
        while (PortraitWindow.ChildHead) PortraitWindow.ChildHead->Destroy();
        while (ChildHead) ChildHead->Destroy();
        Win3D::Destroy();
    }
};
}
Win3D* OpenCustomizationWindow(Win3D* parent, bool portrait) {
    auto* page=new CustomizationPage();
    page->Create(parent,&portrait); return page;
}
bool CustomizationWindowClosed(Win3D* window) {
    return !window || static_cast<CustomizationPage*>(window)->Closed;
}
