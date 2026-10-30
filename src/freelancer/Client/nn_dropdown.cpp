#include "nn_dropdown.h"
#include "nn_text_control.h"
#include "nn_ui_pulse.h"
#include "wire_controls.h"
#include "star_sphere.h"
#include "win3d_immediate.h"
#include "win3d_renderables.h"
#include <algorithm>
#include <cstdio>
#include <cstring>

namespace {
void BeginPanel(WinControl const* control)
{
    // Use the same immediate overlay path as native NeuroNet inventory panels.
    Win3DFlushBeforeOverlayDraw();
    Win3DBeginDraw();
    float transform[12];
    memcpy(transform, control->Orientation, 9 * sizeof(float));
    for (int i=0;i<3;++i) transform[9+i]=control->Position[i]+control->Offset[i];
    Win3DBindModelview(nullptr, transform);
    Win3DEnable(kWin3DBlend);
    Win3DSetBlendFunc(kWin3DBlendSrcAlpha, kWin3DBlendInvSrcAlpha);
}
void Quad(float left,float top,float right,float bottom)
{
    Win3DBegin(kWin3DQuads);
    Win3DVertex3f(left,top,0);Win3DVertex3f(left,bottom,0);
    Win3DVertex3f(right,bottom,0);Win3DVertex3f(right,top,0);
    Win3DEnd();
}
}

NnDropdownPopup* CreateNnDropdownPopup(WinControl* owner)
{
    auto* popup=new NnDropdownPopup;
    if (popup->Create(owner,nullptr)) return popup;
    delete popup;
    return nullptr;
}

bool NnDropdownPopup::Create(Win3D* parent,void*)
{
    Win3DReparent(this,parent);
    Win3DRegister(this);
    Flags=kWin3DActive|kWin3DVisible;
    SetPosition(parent->Position);
    float const at[3]={0,0,0}, half[3]={.115f,RowHeight*.5f,0};
    for (int i=0;i<Capacity;++i) {
        char name[40];sprintf_s(name,"DropdownChoice%d",i);
        Buttons_[i]=static_cast<WireButtonControl*>(CreateWireButtonControl(
            name,"ui_select_item",at,half,0,1,0,0,0xf));
        sprintf_s(name,"DropdownChoiceText%d",i);
        Texts_[i]=static_cast<NnTextControl*>(CreateTextControl(
            name,"ItemName",at,nullptr,.21f,.027f,.9f,0,0,0,1));
        if (!Buttons_[i] || !Texts_[i]) return false;
        Texts_[i]->Flags &= ~kWin3DPickable;
        Texts_[i]->SetProperty(0x24,1,0);
        Buttons_[i]->WireState &= ~0x40;
    }
    Close();
    return true;
}

NnDropdownPopup::~NnDropdownPopup() { Close(); }

void NnDropdownPopup::SetPosition(float const* position)
{
    // Preferences moves its controls to z=-1 through SetOffset, leaving its
    // Position at zero. A plain WinControl ignores that attachment, which put
    // both the popup and its choices on the camera plane. Anchor this container
    // at the owner's actual plane, as the native sibling wire controls do.
    // Child creation can also call SetPosition(Position); derive from the owner
    // every time so those calls do not accumulate the offset.
    auto const* owner=Parent ? Parent->AsWinControl() : nullptr;
    float placed[3];
    for (int i=0;i<3;++i)
        placed[i]=owner ? owner->Position[i]+owner->Offset[i] : position[i];
    WinControl::SetPosition(placed);
}

bool NnDropdownPopup::Open(float left,float anchorTop,float width,
                         std::vector<std::wstring> const& choices,int selected)
{
    Close();
    if (choices.empty()) return false;
    Choices_=choices;
    Left_=left;Width_=width;Count_=int(choices.size());
    Selected_=Focused_=std::clamp(selected,0,Count_-1);
    First_=0;
    Top_=anchorTop-.032f;
    // Keep a list near the bottom of the preferences panel above its field.
    int const visible=(std::min)(Count_,Capacity);
    if (Top_-visible*RowHeight<-.265f) Top_=anchorTop+.004f+visible*RowHeight;
    RefreshChoices();
    Open_=true;
    WinControl::SetProperty(1,0,0);
    CaptureMouse();
    return true;
}

void NnDropdownPopup::RefreshChoices()
{
    int const visible=(std::min)(Count_,Capacity);
    if (Focused_<First_) First_=Focused_;
    if (Focused_>=First_+visible) First_=Focused_-visible+1;
    First_=std::clamp(First_,0,Count_-visible);
    for (int i=0;i<Capacity;++i) {
        Buttons_[i]->SetProperty(1,i>=visible,0);
        Texts_[i]->SetProperty(1,i>=visible,0);
        if (i>=visible) continue;
        float const y=Top_-i*RowHeight;
        Buttons_[i]->HalfExtents[0]=Width_*.5f;
        Buttons_[i]->SetOffset(Left_+Width_*.5f,y-RowHeight*.5f,0);
        Texts_[i]->SetOffset(Left_+.009f,y-.004f,0);
        Texts_[i]->SetWidth(Width_-.024f);
        Texts_[i]->SetText(Choices_[size_t(First_+i)].c_str());
    }
}

void NnDropdownPopup::Close()
{
    Open_=false;
    // Esc/page changes can arrive while a child still holds a mouse press.
    // Destroy() may already have deleted the children before our destructor.
    for (Win3D* child=ChildHead;child;child=child->NextSibling) {
        auto found=std::find(std::begin(Buttons_),std::end(Buttons_),child);
        if (found==std::end(Buttons_)) continue;
        auto* button=*found;
        if (button->ButtonState&1) Win3DRemoveCapture(button);
        button->ButtonState &= ~1;
        button->WireState &= ~7;
    }
    ReleaseMouse();
    WinControl::SetProperty(1,1,0);
}

void NnDropdownPopup::Choose(int index)
{
    if (!Open_ || index<0 || index>=Count_) return;
    Close();
    if (Parent && Parent->AsWinControl())
        Parent->AsWinControl()->SetProperty(0x3e,reinterpret_cast<uintptr_t>(this),index);
}

intptr_t NnDropdownPopup::SetProperty(int msg,uintptr_t a,uintptr_t b)
{
    if (msg==1 && a) {Close();return 1;}
    if (Open_) for (int i=0;i<(std::min)(Count_,Capacity);++i) if (reinterpret_cast<Win3D*>(a)==Buttons_[i]) {
        if (msg==0x26) Choose(First_+i);
        else if (msg==0x2c) Focused_=First_+i;
        return 1;
    }
    return WinControl::SetProperty(msg,a,b);
}

bool NnDropdownPopup::MouseEvent(FWin3DMouseEvent const* event)
{
    if (!Open_) return false;
    // Children get their clicks first. A click elsewhere dismisses on release,
    // consuming both halves so the control beneath cannot accidentally activate.
    if (event->Field1==1) Close();
    return true;
}

bool NnDropdownPopup::KeyEvent(unsigned key,unsigned char* modifiers)
{
    if (!Open_) return false;
    if (key==0x73 && (modifiers[0]&0x10)) return false; // Alt+F4.
    if (!(modifiers[0]&2)) return true;
    switch (key) {
    case 0x1b: case 0x09: Close();break;
    case 0x0d: case 0x20: Choose(Focused_);break;
    case 0x26: Focused_=(std::max)(0,Focused_-1);break;
    case 0x28: Focused_=(std::min)(Count_-1,Focused_+1);break;
    case 0x24: Focused_=0;break;
    case 0x23: Focused_=Count_-1;break;
    case 0x21: Focused_=(std::max)(0,Focused_-Capacity);break;
    case 0x22: Focused_=(std::min)(Count_-1,Focused_+Capacity);break;
    }
    if (Open_) RefreshChoices();
    return true;
}

bool NnDropdownPopup::Slot18(int delta)
{
    if (!Open_) return false;
    if (delta) Focused_=std::clamp(Focused_+(delta>0?-1:1),0,Count_-1);
    RefreshChoices();
    return true;
}

void NnDropdownPopup::Draw()
{
    if (!Open_) return;
    BeginPanel(this);
    int const visible=(std::min)(Count_,Capacity);
    Win3DColor4ub(15,24,38,250);
    Quad(Left_,Top_,Left_+Width_,Top_-visible*RowHeight);
    Win3DColor4ub(40,75,92,230);
    Quad(Left_,Top_-(Focused_-First_)*RowHeight,Left_+Width_,Top_-(Focused_-First_+1)*RowHeight);
    if (Count_>visible) {
        float const height=visible*RowHeight;
        Win3DColor4ub(40,75,92,230);
        Quad(Left_+Width_-.006f,Top_,Left_+Width_-.002f,Top_-height);
        Win3DColor4ub(120,190,210,255);
        float const start=Top_-height*First_/Count_;
        Quad(Left_+Width_-.006f,start,Left_+Width_-.002f,start-height*visible/Count_);
    }
    for (int i=0;i<visible;++i) {
        Texts_[i]->TextColour=First_+i==Selected_?G_NnPaletteArgb_679ba4:G_NnPaletteArgb_679bb0;
        Buttons_[i]->Draw();
        Texts_[i]->Draw();
    }
    Win3DImmedBatchFlushAll();
    UiOverlayPrepPipeline();
}

void DrawNnDropdownCaret(WireButtonControl const* button)
{
    BeginPanel(button);
    unsigned char const* color=reinterpret_cast<unsigned char const*>(&G_NnPaletteArgb_679bb0);
    Win3DColor4ubv(color);
    float const x=button->HalfExtents[0]-.013f;
    Win3DBegin(kWin3DTriangles);
    Win3DVertex3f(x-.004f,.0025f,0);
    Win3DVertex3f(x,-.0025f,0);
    Win3DVertex3f(x+.004f,.0025f,0);
    Win3DEnd();
}
