#pragma once
#include "RP9StartupAnimation.h"
#include <cstdio>
#include <cstring>

namespace Rp9Startup {
class Window {
    HWND Handle=nullptr, Label=nullptr;
    HFONT Font=nullptr;
    bool Cancelled=false, Russian=false, Demo=false, MovieLayout=false;
    unsigned Done=0, Total=0;
    ULONGLONG Started=GetTickCount64(), LastTitle=~0ULL;
    Animation Movie;
    RECT MovieRect={40,106,520,586};
    RECT BarRect={24,86,536,92};
    void Layout() {
        MovieLayout=Movie.Available();
        const int Height=MovieLayout ? 602 : 116;
        RECT Outer={0,0,560,Height};
        AdjustWindowRectEx(&Outer,WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU,FALSE,WS_EX_TOPMOST|WS_EX_NOACTIVATE);
        SetWindowPos(Handle,nullptr,0,0,Outer.right-Outer.left,Outer.bottom-Outer.top,SWP_NOMOVE|SWP_NOZORDER|SWP_NOACTIVATE);
        SetWindowPos(Label,nullptr,24,20,512,60,SWP_NOZORDER|SWP_NOACTIVATE);
        InvalidateRect(Handle,nullptr,TRUE);
    }
    void Paint(HDC Dc,const RECT& Invalid) {
        const int Saved=SaveDC(Dc);
        if(MovieLayout) ExcludeClipRect(Dc,MovieRect.left,MovieRect.top,MovieRect.right,MovieRect.bottom);
        FillRect(Dc,&Invalid,(HBRUSH)GetStockObject(WHITE_BRUSH));
        RestoreDC(Dc,Saved);
        RECT Visible;
        if(MovieLayout && IntersectRect(&Visible,&Invalid,&MovieRect) && !Movie.Paint(Dc,MovieRect)) {
            // A drawing failure is also nonfatal: collapse to the normal progress UI.
            Movie.Close();PostMessageW(Handle,WM_APP+1,0,0);
        }
        HBRUSH Track=CreateSolidBrush(RGB(230,234,238));
        FillRect(Dc,&BarRect,Track);DeleteObject(Track);
        RECT Fill=BarRect;
        Fill.right=Fill.left+(Total ? int((ULONGLONG)(BarRect.right-BarRect.left)*Done/Total) : 0);
        HBRUSH Color=CreateSolidBrush(RGB(47,100,150));
        FillRect(Dc,&Fill,Color);DeleteObject(Color);
    }
    static LRESULT CALLBACK Proc(HWND H,UINT M,WPARAM W,LPARAM L) {
        auto* Self=reinterpret_cast<Window*>(GetWindowLongPtrW(H,GWLP_USERDATA));
        if(M==WM_NCCREATE) {
            Self=static_cast<Window*>(reinterpret_cast<CREATESTRUCTW*>(L)->lpCreateParams);
            SetWindowLongPtrW(H,GWLP_USERDATA,reinterpret_cast<LONG_PTR>(Self));
        }
        if(M==WM_MOUSEACTIVATE) return MA_NOACTIVATE;
        if(Self) {
            if(M==WM_CLOSE) {
                Self->Cancelled=true;
                SetWindowTextW(Self->Label,Self->Russian ? L"\u041e\u0442\u043c\u0435\u043d\u0430. \u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435 \u043a\u043e\u043c\u043f\u0438\u043b\u044f\u0442\u043e\u0440\u043e\u0432..." : L"Cancelling. Waiting for active shader compilers...");
                return 0;
            }
            if(M==WM_ERASEBKGND) return 1;
            if(M==WM_PAINT) {
                PAINTSTRUCT P;HDC Dc=BeginPaint(H,&P);Self->Paint(Dc,P.rcPaint);EndPaint(H,&P);return 0;
            }
            if(M==WM_CTLCOLORSTATIC) {
                SetTextColor((HDC)W,RGB(23,76,126));SetBkColor((HDC)W,RGB(255,255,255));
                return (LRESULT)GetStockObject(WHITE_BRUSH);
            }
            if(M==WM_TIMER && W==1) {
                if(Self->Movie.Advance(GetTickCount64()-Self->Started)) {
                    if(!Self->Movie.Available()) {KillTimer(H,1);Self->Layout();}
                    else InvalidateRect(H,&Self->MovieRect,FALSE);
                }
                return 0;
            }
            if(M==WM_APP+1) {KillTimer(H,1);Self->Layout();return 0;}
        }
        return DefWindowProcW(H,M,W,L);
    }
public:
    // The demo uses the exact production window, with an explicitly labelled simulated progress.
    explicit Window(bool Show=true,bool IsDemo=false,bool EnableAnimation=true):Demo(IsDemo) {
        char Path[MAX_PATH]={},Language[16]={};
        DWORD Length=GetModuleFileNameA(nullptr,Path,MAX_PATH);
        if(char* Slash=Length && Length<MAX_PATH ? strrchr(Path,'\\') : nullptr) {
            strcpy(Slash+1,"port.ini");
            GetPrivateProfileStringA("Language","language","",Language,sizeof(Language),Path);
        }
        if(const char* Switch=strstr(GetCommandLineA(),"-lang"))
            strncpy(Language,Switch[5]?Switch+6:"",2);
        Russian=Demo || _strnicmp(Language,"ru",2)==0;
        if(EnableAnimation) Movie.OpenResource();
        WNDCLASSW C={};C.lpfnWndProc=Proc;C.hInstance=GetModuleHandleW(nullptr);
        C.hCursor=LoadCursor(nullptr,IDC_ARROW);C.hbrBackground=(HBRUSH)GetStockObject(WHITE_BRUSH);
        C.lpszClassName=L"FreelancerShaderStartup";RegisterClassW(&C);
        Handle=CreateWindowExW(WS_EX_TOPMOST|WS_EX_NOACTIVATE,C.lpszClassName,L"Freelancer",
            WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_CLIPCHILDREN,CW_USEDEFAULT,CW_USEDEFAULT,560,140,
            nullptr,nullptr,C.hInstance,this);
        if(!Handle) return;
        Label=CreateWindowW(L"STATIC",Russian ? L"\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0448\u0435\u0439\u0434\u0435\u0440\u043e\u0432 \u0438 \u043a\u044d\u0448\u0430..." : L"Checking required shaders and persistent cache...",
            WS_CHILD|WS_VISIBLE,24,25,512,64,Handle,nullptr,C.hInstance,nullptr);
        Font=CreateFontW(-18,0,0,0,FW_SEMIBOLD,FALSE,FALSE,FALSE,DEFAULT_CHARSET,
            OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,CLEARTYPE_QUALITY,DEFAULT_PITCH,L"Segoe UI");
        if(Font) SendMessageW(Label,WM_SETFONT,(WPARAM)Font,TRUE);
        Layout();
        Started=GetTickCount64();
        if(Movie.Available()) SetTimer(Handle,1,16,nullptr);
        Update(0,0);
        if(Show) {ShowWindow(Handle,SW_SHOWNOACTIVATE);UpdateWindow(Handle);}
    }
    ~Window() {if(Handle) {KillTimer(Handle,1);DestroyWindow(Handle);}if(Font) DeleteObject(Font);}
    bool Update(unsigned Completed,unsigned Required) {
        if(!Handle || !Label) return false;
        if(!Cancelled && (Done!=Completed || Total!=Required || !Required)) {
            Done=Completed>Required ? Required : Completed;Total=Required;
            wchar_t Text[256];
            swprintf_s(Text,Russian ? L"\u041f\u043e\u0434\u0433\u043e\u0442\u043e\u0432\u043a\u0430 \u0448\u0435\u0439\u0434\u0435\u0440\u043e\u0432: %u / %u\n%s" : L"Preparing shaders: %u / %u\n%s",Done,Total,
                Demo ? L"\u0414\u0435\u043c\u043e\u043d\u0441\u0442\u0440\u0430\u0446\u0438\u044f \u043e\u043a\u043d\u0430. \u041f\u0440\u043e\u0433\u0440\u0435\u0441\u0441 \u043f\u043e\u0432\u0442\u043e\u0440\u044f\u0435\u0442\u0441\u044f \u043f\u043e \u043a\u0440\u0443\u0433\u0443." : Russian ?
                L"\u0418\u0433\u0440\u0430 \u0437\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u0441\u044f \u043f\u043e\u0441\u043b\u0435 \u043f\u043e\u0434\u0433\u043e\u0442\u043e\u0432\u043a\u0438." : L"The game starts after preparation.");
            SetWindowTextW(Label,Text);InvalidateRect(Handle,&BarRect,FALSE);
        }
        const ULONGLONG Seconds=(GetTickCount64()-Started)/1000;
        if(!Cancelled && Seconds!=LastTitle) {
            LastTitle=Seconds;wchar_t Title[128];
            swprintf_s(Title,Russian ? L"Freelancer \u2014 \u041f\u043e\u0434\u0433\u043e\u0442\u043e\u0432\u043a\u0430 \u0448\u0435\u0439\u0434\u0435\u0440\u043e\u0432 (%llu \u0441)%s" : L"Freelancer - Preparing shaders (%llu s)%s",
                Seconds,Demo ? L" \u2014 \u0414\u0415\u041c\u041e" : L"");
            SetWindowTextW(Handle,Title);
        }
        MSG M;
        // Keep game activation/device-reset messages outside the startup gate.
        while(PeekMessageW(&M,Handle,0,0,PM_REMOVE)) {
            if(M.message==WM_QUIT) {Cancelled=true;PostQuitMessage((int)M.wParam);break;}
            TranslateMessage(&M);DispatchMessageW(&M);
        }
        return !Cancelled;
    }
    HWND Get() const {return Handle;}
    bool HasAnimation() const {return Movie.Available();}
};
}
