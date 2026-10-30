#pragma once
#include "wincontrol_base.h"
#include <string>
#include <vector>

class WireButtonControl;
class NnTextControl;

// A small NeuroNet choice list. The owner draws it after its other controls and
// receives 0x3e (source=this, B=chosen index) only after an explicit selection.
class NnDropdownPopup final : public WinControl
{
public:
    ~NnDropdownPopup() override;
    bool Create(Win3D* parent, void* data) override;
    void SetPosition(float const* position) override;
    bool Open(float left, float anchorTop, float width,
              std::vector<std::wstring> const& choices, int selected);
    void Close();
    bool IsOpen() const { return Open_; }
    void Draw() override;
    bool MouseEvent(FWin3DMouseEvent const* event) override;
    bool KeyEvent(unsigned key, unsigned char* modifiers) override;
    bool Slot18(int delta) override;
    intptr_t SetProperty(int msg, uintptr_t a, uintptr_t b) override;

private:
    static constexpr int Capacity = 8;
    static constexpr float RowHeight = .035f;
    WireButtonControl* Buttons_[Capacity] = {};
    NnTextControl* Texts_[Capacity] = {};
    int Count_ = 0, Selected_ = 0, Focused_ = 0;
    int First_ = 0;
    std::vector<std::wstring> Choices_;
    float Left_ = 0, Top_ = 0, Width_ = 0;
    bool Open_ = false;
    void Choose(int index);
    void RefreshChoices();
};

NnDropdownPopup* CreateNnDropdownPopup(WinControl* owner);
void DrawNnDropdownCaret(WireButtonControl const* button);
