#include "campaign_control.h"

namespace {
SRWLOCK GCampaignLock = SRWLOCK_INIT;
CampaignControl::Snapshot GCampaignStatus;
CampaignControl::Request GCampaignRequest;
bool GCampaignRequestPending = false;
HWND GCampaignWindow = nullptr;
constexpr unsigned CampaignMenu = 32840;

bool QueueCampaignStart(CampaignControl::Request const& request) {
    AcquireSRWLockExclusive(&GCampaignLock);
    bool accepted = GApp && GApp->ServerControl.bCampaignServer && GServerRunning &&
        GCampaignStatus.initialized && !GCampaignRequestPending && CampaignControl::CanRequest(GCampaignStatus.state,request);
    if (accepted) { GCampaignRequest=request;GCampaignRequestPending=true; }
    ReleaseSRWLockExclusive(&GCampaignLock);
    return accepted;
}
}

extern "C" int __cdecl FreelancerCampaignGetState(CampaignControl::Snapshot* out,unsigned size) {
    if (!out || size!=sizeof(*out)) return 0;
    AcquireSRWLockShared(&GCampaignLock);*out=GCampaignStatus;ReleaseSRWLockShared(&GCampaignLock);return 1;
}
extern "C" void __cdecl FreelancerCampaignSetState(CampaignControl::Snapshot const* value,unsigned size) {
    if (!value || size!=sizeof(*value)) return;
    AcquireSRWLockExclusive(&GCampaignLock);GCampaignStatus=*value;
    if (GCampaignRequestPending && !CampaignControl::CanRequest(value->state,GCampaignRequest)) GCampaignRequestPending=false;
    ReleaseSRWLockExclusive(&GCampaignLock);
}
extern "C" int __cdecl FreelancerCampaignTakeStart(CampaignControl::Request* out,unsigned size) {
    if (!out || size!=sizeof(*out)) return 0;
    AcquireSRWLockExclusive(&GCampaignLock);
    bool pending=GCampaignRequestPending;
    if (pending) *out=GCampaignRequest;
    GCampaignRequestPending=false;
    ReleaseSRWLockExclusive(&GCampaignLock);return pending?1:0;
}

namespace {
wchar_t const* CampaignPhaseText(CampaignControl::Snapshot const& status) {
    using namespace CampaignControl;
    switch (status.notice) {
    case NoPlayers: return L"\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435 \u0438\u0433\u0440\u043e\u043a\u0430 \u043d\u0430 \u0431\u0430\u0437\u0435 \u0438\u043b\u0438 \u0432 \u043a\u043e\u0441\u043c\u043e\u0441\u0435.";
    case PlayerBusy: return L"\u041f\u0435\u0440\u0435\u0434 \u0437\u0430\u043f\u0443\u0441\u043a\u043e\u043c \u0437\u0430\u0432\u0435\u0440\u0448\u0438\u0442\u0435 \u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0435 \u0437\u0430\u0434\u0430\u043d\u0438\u044f \u0438\u0433\u0440\u043e\u043a\u043e\u0432.";
    case CreateFailed: return L"\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0441\u043e\u0437\u0434\u0430\u0442\u044c \u043c\u0438\u0441\u0441\u0438\u044e. \u041c\u043e\u0436\u043d\u043e \u043f\u043e\u0432\u0442\u043e\u0440\u0438\u0442\u044c \u0437\u0430\u043f\u0443\u0441\u043a.";
    case DiskError: return L"\u041e\u0448\u0438\u0431\u043a\u0430 \u0437\u0430\u043f\u0438\u0441\u0438 campaign_progress.bin. \u041a\u0430\u043c\u043f\u0430\u043d\u0438\u044f \u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u0430.";
    case CorruptSave: return L"\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043f\u0440\u043e\u0447\u0438\u0442\u0430\u0442\u044c campaign_progress.bin. \u041f\u0440\u043e\u0433\u0440\u0435\u0441\u0441 \u043d\u0435 \u0441\u0431\u0440\u043e\u0448\u0435\u043d.";
    case OwnerAbsent: return L"\u0412\u0435\u0434\u0443\u0449\u0438\u0439 \u043e\u0442\u043a\u043b\u044e\u0447\u0438\u043b\u0441\u044f \u0438\u043b\u0438 \u0441\u043c\u0435\u043d\u0438\u043b \u043f\u0435\u0440\u0441\u043e\u043d\u0430\u0436\u0430. \u041c\u0438\u0441\u0441\u0438\u044f \u043f\u0440\u0438\u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u0430.";
    }
    switch (status.state.phase) {
    case First: return L"\u041f\u0435\u0440\u0432\u0430\u044f \u043c\u0438\u0441\u0441\u0438\u044f \u0437\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u0441\u044f \u0430\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u043f\u0440\u0438 \u0432\u0445\u043e\u0434\u0435 \u0438\u0433\u0440\u043e\u043a\u0430.";
    case Running: return L"\u0421\u044e\u0436\u0435\u0442\u043d\u0430\u044f \u043c\u0438\u0441\u0441\u0438\u044f \u0432\u044b\u043f\u043e\u043b\u043d\u044f\u0435\u0442\u0441\u044f.";
    case Freeflight: return L"\u0421\u0432\u043e\u0431\u043e\u0434\u043d\u0430\u044f \u0438\u0433\u0440\u0430. \u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0443\u044e \u043c\u0438\u0441\u0441\u0438\u044e \u0437\u0430\u043f\u0443\u0441\u043a\u0430\u0435\u0442 \u0445\u043e\u0437\u044f\u0438\u043d \u0441\u0435\u0440\u0432\u0435\u0440\u0430.";
    case Automatic: return L"\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435 \u0430\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u043e\u0433\u043e \u043f\u0440\u043e\u0434\u043e\u043b\u0436\u0435\u043d\u0438\u044f \u0441\u044e\u0436\u0435\u0442\u043d\u043e\u0439 \u0446\u0435\u043f\u043e\u0447\u043a\u0438.";
    case Interrupted: return L"\u041c\u0438\u0441\u0441\u0438\u044f \u043f\u0440\u0435\u0440\u0432\u0430\u043d\u0430. \u0414\u043e\u0441\u0442\u0443\u043f\u0435\u043d \u043f\u043e\u0432\u0442\u043e\u0440\u043d\u044b\u0439 \u0437\u0430\u043f\u0443\u0441\u043a \u0441 \u043d\u0430\u0447\u0430\u043b\u0430.";
    case Complete: return L"\u041a\u0430\u043c\u043f\u0430\u043d\u0438\u044f \u043f\u0440\u043e\u0439\u0434\u0435\u043d\u0430. \u0421\u0432\u043e\u0431\u043e\u0434\u043d\u0430\u044f \u0438\u0433\u0440\u0430.";
    default: return L"\u041a\u0430\u043c\u043f\u0430\u043d\u0438\u044f \u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u0430.";
    }
}
void RefreshCampaignWindow(HWND window) {
    using namespace CampaignControl;
    Snapshot snapshot;FreelancerCampaignGetState(&snapshot,sizeof(snapshot));
    HWND list=GetDlgItem(window,1);
    int selected=int(SendMessageW(list,LB_GETCURSEL,0,0));
    SendMessageW(list,WM_SETREDRAW,FALSE,0);SendMessageW(list,LB_RESETCONTENT,0,0);
    for (unsigned i=0;i<MissionCount;++i) {
        wchar_t const* state=L"\u0417\u0430\u043a\u0440\u044b\u0442\u0430";
        if (i<snapshot.state.completed) state=L"\u041f\u0440\u043e\u0439\u0434\u0435\u043d\u0430";
        else if (i==snapshot.state.completed) {
            if (snapshot.state.phase==Running) state=L"\u0412\u044b\u043f\u043e\u043b\u043d\u044f\u0435\u0442\u0441\u044f";
            else if (snapshot.state.phase==Interrupted) state=L"\u041f\u0440\u0435\u0440\u0432\u0430\u043d\u0430";
            else if (snapshot.state.phase==First || snapshot.state.phase==Automatic) state=L"\u0410\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0439 \u0437\u0430\u043f\u0443\u0441\u043a";
            else if (snapshot.state.phase==Freeflight) state=L"\u0414\u043e\u0441\u0442\u0443\u043f\u043d\u0430";
        }
        wchar_t line[128];swprintf_s(line,L"%hs\t%s",Missions()[i].name,state);
        SendMessageW(list,LB_ADDSTRING,0,reinterpret_cast<LPARAM>(line));
    }
    if (selected<0) selected=int(snapshot.state.completed<MissionCount?snapshot.state.completed:MissionCount-1);
    SendMessageW(list,LB_SETCURSEL,selected,0);SendMessageW(list,WM_SETREDRAW,TRUE,0);InvalidateRect(list,nullptr,TRUE);
    wchar_t title[256];swprintf_s(title,L"\u0423\u0440\u043e\u0432\u0435\u043d\u044c \u043a\u0430\u043c\u043f\u0430\u043d\u0438\u0438: %u\r\n%s",snapshot.state.rank,CampaignPhaseText(snapshot));
    SetWindowTextW(GetDlgItem(window,2),title);
    bool pending;
    AcquireSRWLockShared(&GCampaignLock);pending=GCampaignRequestPending;ReleaseSRWLockShared(&GCampaignLock);
    Request request{unsigned(selected),snapshot.state.revision};
    EnableWindow(GetDlgItem(window,3),GServerRunning && snapshot.initialized && !pending && CanRequest(snapshot.state,request));
    SetWindowTextW(GetDlgItem(window,3),snapshot.state.phase==Interrupted?L"\u0417\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u044c \u0437\u0430\u043d\u043e\u0432\u043e":L"\u0417\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u044c \u043c\u0438\u0441\u0441\u0438\u044e");
}
LRESULT CALLBACK CampaignWindowProc(HWND window,UINT message,WPARAM wparam,LPARAM lparam) {
    switch (message) {
    case WM_CREATE: {
        auto instance=GetModuleHandleW(nullptr);
        auto child=[&](wchar_t const* kind,wchar_t const* text,DWORD style,int x,int y,int w,int h,int id) {
            HWND control=CreateWindowExW(0,kind,text,WS_CHILD|WS_VISIBLE|style,x,y,w,h,window,reinterpret_cast<HMENU>(id),instance,nullptr);
            SendMessageW(control,WM_SETFONT,reinterpret_cast<WPARAM>(GetStockObject(DEFAULT_GUI_FONT)),TRUE);
            return control;
        };
        child(L"STATIC",L"",0,16,12,580,54,2);
        HWND list=child(L"LISTBOX",L"",WS_BORDER|WS_VSCROLL|WS_TABSTOP|LBS_NOTIFY|LBS_USETABSTOPS,16,72,580,270,1);
        int tab=135;SendMessageW(list,LB_SETTABSTOPS,1,reinterpret_cast<LPARAM>(&tab));
        child(L"BUTTON",L"\u0417\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u044c \u043c\u0438\u0441\u0441\u0438\u044e",WS_TABSTOP,16,356,225,30,3);
        child(L"BUTTON",L"\u0417\u0430\u043a\u0440\u044b\u0442\u044c",WS_TABSTOP,486,356,110,30,4);
        SetTimer(window,1,500,nullptr);RefreshCampaignWindow(window);return 0;
    }
    case WM_TIMER: RefreshCampaignWindow(window);return 0;
    case WM_COMMAND:
        if (LOWORD(wparam)==4) { DestroyWindow(window);return 0; }
        if (LOWORD(wparam)==1 && HIWORD(wparam)==LBN_SELCHANGE) { RefreshCampaignWindow(window);return 0; }
        if (LOWORD(wparam)==3) {
            CampaignControl::Snapshot snapshot;FreelancerCampaignGetState(&snapshot,sizeof(snapshot));
            int selected=int(SendMessageW(GetDlgItem(window,1),LB_GETCURSEL,0,0));
            if (snapshot.state.phase==CampaignControl::Interrupted &&
                MessageBoxW(window,L"\u041c\u0438\u0441\u0441\u0438\u044f \u043d\u0430\u0447\u043d\u0451\u0442\u0441\u044f \u0437\u0430\u043d\u043e\u0432\u043e. \u041f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u0435 \u043c\u0438\u0440\u0430 \u0432\u043d\u0443\u0442\u0440\u0438 \u043f\u0440\u0435\u0440\u0432\u0430\u043d\u043d\u043e\u0439 \u043c\u0438\u0441\u0441\u0438\u0438 \u043d\u0435 \u0432\u043e\u0441\u0441\u0442\u0430\u043d\u0430\u0432\u043b\u0438\u0432\u0430\u0435\u0442\u0441\u044f, \u0441\u044e\u0436\u0435\u0442\u043d\u044b\u0435 \u0432\u044b\u0434\u0430\u0447\u0438 \u043c\u043e\u0433\u0443\u0442 \u043f\u043e\u0432\u0442\u043e\u0440\u0438\u0442\u044c\u0441\u044f. \u041f\u0440\u043e\u0434\u043e\u043b\u0436\u0438\u0442\u044c?",
                            L"\u041f\u043e\u0432\u0442\u043e\u0440 \u043c\u0438\u0441\u0441\u0438\u0438",MB_YESNO|MB_ICONQUESTION)!=IDYES) return 0;
            QueueCampaignStart({unsigned(selected),snapshot.state.revision});
            RefreshCampaignWindow(window);return 0;
        }
        break;
    case WM_CLOSE: DestroyWindow(window);return 0;
    case WM_DESTROY: KillTimer(window,1);GCampaignWindow=nullptr;return 0;
    }
    return DefWindowProcW(window,message,wparam,lparam);
}
}

void CFLServerApp::OnCampaign() {
    if (!ServerControl.bCampaignServer) return;
    if (!GCampaignWindow) {
        WNDCLASSW cls={};cls.lpfnWndProc=CampaignWindowProc;cls.hInstance=GetModuleHandleW(nullptr);
        cls.hCursor=::LoadCursor(nullptr,IDC_ARROW);cls.hbrBackground=reinterpret_cast<HBRUSH>(COLOR_BTNFACE+1);
        cls.lpszClassName=L"FreelancerCampaignControl";RegisterClassW(&cls);
        GCampaignWindow=CreateWindowExW(WS_EX_CONTROLPARENT,cls.lpszClassName,L"\u041a\u0430\u043c\u043f\u0430\u043d\u0438\u044f \u2014 \u0441\u043f\u0438\u0441\u043e\u043a \u043c\u0438\u0441\u0441\u0438\u0439",
            WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU,CW_USEDEFAULT,CW_USEDEFAULT,630,435,
            m_pMainWnd->m_hWnd,nullptr,cls.hInstance,nullptr);
    }
    ShowWindow(GCampaignWindow,SW_SHOW);SetForegroundWindow(GCampaignWindow);
}
void CFLServerApp::OnUpdateCampaign(CCmdUI* ui) {
    ui->Enable(ServerControl.bCampaignServer && GServerRunning && !IsShuttingDown());
}
