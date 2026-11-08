#include "rpg_dialog.h"
#ifdef FREELANCER_RPG_WORLD
#include "rpg_dialog_model.h"
#include "rpg_gesture_rotation.h"
#include "player_spawn.h"
#include <windows.h>
#include "gf_script_object.h"
#include "rich_text_win.h"
#include "wincontrol_base.h"
#include "ids_rdl.h"
#include "ids_strings.h"
#include "common_text.h"
#include "input_manager.h"
#include "ship_parking.h"
#include "common_universe.h"
#include <string>
#include "space_letterbox.h"
#include "common_goods.h"
#include "common_misc.h"
#include "port_config.h"
#include "gf_script.h"
#include "room_control.h"
#include "character_info.h"
#include "gf_thorn_component.h"
#include <windows.h>

namespace
{
    bool WantOffer = false;
    bool PendingAccept = false;
    FGfScriptSequence* Owner = nullptr;
    bool EscapeHeld = false;

    class FDialog : public WinControl
    {
    public:
        FRpgDialogModel Model;
        WinControl* Buttons[4] = {};
        RichTextWin* Labels[4] = {};
        RichTextWin* Reply = nullptr;
        bool Offer = false;
        bool Tree = false;
        unsigned DialogId = 0;
        unsigned NodeId = 0;
        std::string SceneGroup;
        std::string GestureGroup;
        FGfScriptEntry* Speech = nullptr;
        int PendingChoice = -1;
        bool Speaking = false;
        int FallbackMs = 0;
        unsigned GestureStep[2] = {};
        FGfScriptEntry* Gestures[2] = {};

        void ChoiceCamera() {
            if (SceneGroup.empty()) return;
            auto* Camera = G_GfScriptManager.FindCreatedEntity(3, "RpgCamera_player");
            auto* Monitor = G_GfScriptManager.FindCreatedEntity(4, "RpgMonitor");
            if (!Camera || !Monitor) return;
            float Transform[12] = {}, Fov = 30, Near = .1f, Far = 10000;
            Camera->GetTransform(Transform); Camera->GetFov(&Fov);
            Camera->GetNear(&Near); Camera->GetFar(&Far);
            Monitor->SetTransform(Transform); Monitor->SetFov(&Fov);
            Monitor->SetNear(&Near); Monitor->SetFar(&Far);
        }

        static void StopEntry(FGfScriptEntry*& Entry) {
            if (Entry) {
                Entry->Script->Teardown();
                GfScriptTouchEntities(Entry->Engine, false);
                GfScriptCharacterAnimations(Entry->Engine, false);
                delete Entry; Entry = nullptr;
            }
        }
        void StopSpeech() {
            StopEntry(Speech);
            Speaking = false; FallbackMs = 0;
        }
        ~FDialog() { StopSpeech(); for (auto*& Entry : Gestures) StopEntry(Entry); }
        void StartGesture(unsigned Role, int VoiceMs) {
            // One whole authored step survives speech changes and speech-only Esc.
            if (Gestures[Role]) return;
            unsigned const Step = RpgGestureRotation::Next(GestureStep[Role], Role != 0, VoiceMs);
            char Name[32];
            sprintf_s(Name, "%s_%02u.thn", Role ? "player" : "vendor", Step + 1);
            std::string const File = "SCRIPTS\\RPG\\" + GestureGroup + "\\gestures\\" + Name;
            std::string const Full = std::string(PortExeDirectory()) + "..\\DATA\\" + File;
            if (GetFileAttributesA(Full.c_str()) == INVALID_FILE_ATTRIBUTES) return;
            auto* Entry = new FGfScriptEntry;
            malloc_strcpy(&Entry->ScriptFile, File.c_str());
            Entry->Engine = ThornScriptLoad(Entry->ScriptFile);
            if (!Entry->Engine) { delete Entry; return; }
            Entry->Frame = Owner->Entries[Owner->Current].Frame;
            Entry->Create(Owner->Room, Owner);
            Entry->Script->Mirror = &Owner->Mirror;
            Entry->Script->RpgBoundActors = Entry->Script->RpgFragment = true;
            GfScriptCharacterAnimations(Entry->Engine, true);
            GfScriptTouchEntities(Entry->Engine, true);
            GetCharacterInfoDb()->FlushQueuedScripts();
            Gestures[Role] = Entry;
            GestureStep[Role] = (Step + 1) % RpgGestureRotation::Count;
            Entry->Script->Start(Entry->Engine, Entry->ScriptFile, 2, 0, 0, 0,
                                 Owner->Priority + 1, 0, Owner->Name, 0, 0);
        }
        void UpdateGestures(int Ms) {
            for (auto*& Entry : Gestures)
                if (Entry && Entry->Script->Update(Ms)) StopEntry(Entry);
        }
        void ShowChoices(bool Show) {
            if (Show) { Refresh(); ChoiceCamera(); }
            else for (int I=0; I<4; ++I) { Buttons[I]->Flags &= ~3; Labels[I]->Flags &= ~3; }
        }
        bool StartLine(int ChoiceIndex) {
            if (SceneGroup.empty() || !Owner) return false;
            using FragmentFn = char const* (__cdecl*)(unsigned, unsigned, int, unsigned);
            auto Fragment = reinterpret_cast<FragmentFn>(GetProcAddress(Content(), "RpgDialogFragment"));
            std::string Id = Fragment ? Fragment(DialogId, NodeId, ChoiceIndex, GetPlayerConnectionId()) : "";
            if (Id.empty()) return false;
            std::string Language = _stricmp(PortVoice(), "ru") == 0 ? "ru" : "en";
            std::string File = "SCRIPTS\\RPG\\" + SceneGroup + "\\" + Language + "\\" + Id + ".thn";
            std::string Full = std::string(PortExeDirectory()) + "..\\DATA\\" + File;
            auto AudioExists = [&](char const* Lang) {
                std::string const Audio = std::string(PortExeDirectory()) + "..\\DATA\\AUDIO\\" +
                    (!strcmp(Lang, "ru") ? "MOD" : "MOD_ENG") + "\\RPG\\" + SceneGroup + "\\" + Id +
                    (ChoiceIndex < 0 ? "_l001_vendor.wav" : "_l001_player.wav");
                return GetFileAttributesA(Audio.c_str()) != INVALID_FILE_ATTRIBUTES;
            };
            if ((GetFileAttributesA(Full.c_str()) == INVALID_FILE_ATTRIBUTES || !AudioExists(Language.c_str())) && Language != "en") {
                Language = "en";
                File = "SCRIPTS\\RPG\\" + SceneGroup + "\\en\\" + Id + ".thn";
                Full = std::string(PortExeDirectory()) + "..\\DATA\\" + File;
            }
            if (GetFileAttributesA(Full.c_str()) == INVALID_FILE_ATTRIBUTES || !AudioExists(Language.c_str())) return false;
            unsigned const Role = ChoiceIndex < 0 ? 0 : 1;
            if (!RoomControlPlayerCharacter(Owner->Room) ||
                !Owner->Mirror.First() ||
                !G_GfScriptManager.FindCreatedEntity(3, "RpgCamera_vendor") ||
                !G_GfScriptManager.FindCreatedEntity(3, "RpgCamera_player")) return false;
            auto* Entry = new FGfScriptEntry;
            malloc_strcpy(&Entry->ScriptFile, File.c_str());
            Entry->Engine = ThornScriptLoad(Entry->ScriptFile);
            if (!Entry->Engine) { delete Entry; return false; }
            Entry->Frame = Owner->Entries[Owner->Current].Frame;
            Entry->Create(Owner->Room, Owner);
            Entry->Script->Mirror = &Owner->Mirror;
            Entry->Script->RpgBoundActors = Entry->Script->RpgFragment = true;
            GfScriptCharacterAnimations(Entry->Engine, true);
            GfScriptTouchEntities(Entry->Engine, true);
            GetCharacterInfoDb()->FlushQueuedScripts();
            Speech = Entry; Speaking = true;
            Entry->Script->Start(Entry->Engine, Entry->ScriptFile, 2, 0, 0, 0,
                                 Owner->Priority + 1, 0, Owner->Name, 0, 0);
            // START_SOUND carries the measured WAV duration of the selected language.
            // Scene duration also includes facial tails and must not qualify a short voice.
            auto const& Sounds = Entry->Script->SoundEvents;
            int const VoiceMs = Sounds.size() == 1 ? Sounds.front().EndMs - Sounds.front().StartMs : 0;
            StartGesture(Role, VoiceMs);
            ShowChoices(false);
            auto Render = reinterpret_cast<RenderFn>(GetProcAddress(Content(), "RpgDialogRenderText"));
            if (Render) Text(Reply, Render(DialogId, NodeId, ChoiceIndex, GetPlayerConnectionId()));
            return true;
        }
        void PlayNode() {
            Refresh();
            if (StartLine(-1)) return;
            auto Count = reinterpret_cast<CountFn>(GetProcAddress(Content(), "RpgDialogChoiceCount"));
            if (!SceneGroup.empty() && Count && Count(DialogId, NodeId) == 0) { Speaking = true; FallbackMs = 2500; ShowChoices(false); }
            else ChoiceCamera();
        }
        void FinishSpeech() {
            if (!Speaking) return;
            StopSpeech();
            int const Choice = PendingChoice; PendingChoice = -1;
            if (Choice >= 0) { ApplyChoice(Choice); return; }
            auto Count = reinterpret_cast<CountFn>(GetProcAddress(Content(), "RpgDialogChoiceCount"));
            if (!Count || Count(DialogId, NodeId) == 0) Model.Done = true;
            else ShowChoices(true);
        }

        void Text(RichTextWin* Target, wchar_t const* Caption)
        {
            std::wstring Expanded = Caption ? Caption : L"";
            size_t const BaseToken = Expanded.find(L"{base}");
            if (BaseToken != std::wstring::npos) {
                auto StatusFn = reinterpret_cast<ShipParkingStatusFn>(GetProcAddress(GetModuleHandleA("Server.dll"), "PlayerShipParking_Status"));
                ShipParkingStatus Status;
                wchar_t Name[256] = {};
                if (StatusFn && StatusFn(GetPlayerConnectionId(), &Status) == ParkingOk)
                    if (auto const* Base = Universe::get_base(Status.BaseId)) GetIdsStringW(Base->GetStridName(), Name, 256);
                Expanded.replace(BaseToken, 6, Name);
            }
            RenderDisplayList Rdl;
            StyleNode Style(0x9ca4);
            RdlAppendNode(Rdl, Style.Clone());
            TextNode Words(Expanded.c_str(), -1);
            RdlAppendNode(Rdl, Words.Clone());
            Target->ClearContent();
            Target->AppendContent(Rdl);
        }
        typedef unsigned (__cdecl* StartFn)(unsigned);
        typedef unsigned (__cdecl* BeginFn)(unsigned, unsigned);
        typedef wchar_t const* (__cdecl* RenderFn)(unsigned, unsigned, int, unsigned);
        typedef int (__cdecl* CountFn)(unsigned, unsigned);
        typedef wchar_t const* (__cdecl* TextFn)(unsigned, unsigned);
        typedef wchar_t const* (__cdecl* ChoiceFn)(unsigned, unsigned, int);
        typedef unsigned (__cdecl* ChooseFn)(unsigned, unsigned, int, unsigned);
        typedef unsigned (__cdecl* NodeIdsFn)(unsigned, unsigned);
        typedef unsigned (__cdecl* ChoiceIdsFn)(unsigned, unsigned, int);
        HMODULE Content() { return GetModuleHandleA("Content.dll"); }
        void Refresh()
        {
            if (Tree)
            {
                auto Render = reinterpret_cast<RenderFn>(GetProcAddress(Content(), "RpgDialogRenderText"));
                auto NodeText = reinterpret_cast<TextFn>(GetProcAddress(Content(), "RpgDialogNodeText"));
                auto Count = reinterpret_cast<CountFn>(GetProcAddress(Content(), "RpgDialogChoiceCount"));
                auto ChoiceText = reinterpret_cast<ChoiceFn>(GetProcAddress(Content(), "RpgDialogChoiceText"));
                auto NodeIds = reinterpret_cast<NodeIdsFn>(GetProcAddress(Content(), "RpgDialogNodeTextIds"));
                auto ChoiceIds = reinterpret_cast<ChoiceIdsFn>(GetProcAddress(Content(), "RpgDialogChoiceTextIds"));
                int N = Count != nullptr ? Count(DialogId, NodeId) : 0;
                wchar_t Caption[512] = {};
                unsigned Ids = NodeIds != nullptr ? NodeIds(DialogId, NodeId) : 0;
                if (Ids) GetIdsStringW(Ids, Caption, 512);
                Text(Reply, Ids ? Caption : Render ? Render(DialogId, NodeId, -1, GetPlayerConnectionId()) :
                     (NodeText != nullptr ? NodeText(DialogId, NodeId) : L""));
                for (int I = 0; I < 4; ++I)
                {
                    bool Visible = I < N;
                    Buttons[I]->Flags = static_cast<unsigned char>((Buttons[I]->Flags & ~3) | (Visible ? 3 : 0));
                    Labels[I]->Flags = static_cast<unsigned char>((Labels[I]->Flags & ~3) | (Visible ? 3 : 0));
                    if (Visible)
                    {
                        unsigned ChoiceId = ChoiceIds != nullptr ? ChoiceIds(DialogId, NodeId, I) : 0;
                        Caption[0] = 0;
                        if (ChoiceId) GetIdsStringW(ChoiceId, Caption, 512);
                        wchar_t const* Words = ChoiceId ? Caption : Render ? Render(DialogId, NodeId, I, GetPlayerConnectionId()) :
                            (ChoiceText != nullptr ? ChoiceText(DialogId, NodeId, I) : L"");
                        wchar_t Buf[200];
                        Buf[0] = static_cast<wchar_t>(L'1' + I);
                        Buf[1] = L'.';
                        Buf[2] = L' ';
                        Buf[3] = 0;
                        if (Words != nullptr)
                            wcsncat(Buf, Words, 180);
                        Text(Labels[I], Buf);
                    }
                }
                return;
            }
            if (Offer)
            {
                Text(Reply, L"\u0425\u043e\u0447\u0435\u0448\u044c \u043c\u0438\u0441\u0441\u0438\u044e?");
                wchar_t const* Answers[] = { L"1. \u0414\u0430.", L"2. \u041d\u0435\u0442." };
                for (int I = 0; I < 4; ++I)
                {
                    bool Visible = I < 2;
                    Buttons[I]->Flags = static_cast<unsigned char>((Buttons[I]->Flags & ~3) | (Visible ? 3 : 0));
                    Labels[I]->Flags = static_cast<unsigned char>((Labels[I]->Flags & ~3) | (Visible ? 3 : 0));
                    if (Visible) Text(Labels[I], Answers[I]);
                }
                return;
            }
            wchar_t const* Choices[] = {
                L"1. \u0427\u0442\u043e \u0437\u0434\u0435\u0441\u044c \u043f\u0440\u043e\u0438\u0441\u0445\u043e\u0434\u0438\u0442?",
                L"2. [\u0423\u0431\u0435\u0436\u0434\u0435\u043d\u0438\u0435] \u0414\u0430\u0432\u0430\u0439 \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0438\u043c\u0441\u044f.",
                L"3. [\u0423\u0433\u0440\u043e\u0437\u0430] \u041b\u0443\u0447\u0448\u0435 \u043e\u0442\u0432\u0435\u0447\u0430\u0439.",
                L"4. \u0417\u0430\u043a\u043e\u043d\u0447\u0438\u0442\u044c \u0440\u0430\u0437\u0433\u043e\u0432\u043e\u0440."};
            wchar_t const* Replies[] = {
                L"\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0440\u0435\u043f\u043b\u0438\u043a\u0443:",
                L"\u041d\u0430 \u0431\u0430\u0437\u0435 \u043f\u043e\u043a\u0430 \u0441\u043f\u043e\u043a\u043e\u0439\u043d\u043e. \u0417\u0430 \u043d\u043e\u0432\u043e\u0441\u0442\u044f\u043c\u0438 \u0437\u0430\u0445\u043e\u0434\u0438 \u043f\u043e\u0437\u0436\u0435.",
                L"\u042f \u0433\u043e\u0442\u043e\u0432 \u0432\u044b\u0441\u043b\u0443\u0448\u0430\u0442\u044c \u0442\u0432\u043e\u0451 \u043f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438\u0435.",
                L"\u041f\u043e\u043b\u0435\u0433\u0447\u0435. \u0421 \u0443\u0433\u0440\u043e\u0437\u0430\u043c\u0438 \u0442\u044b \u043d\u0438\u0447\u0435\u0433\u043e \u043d\u0435 \u0434\u043e\u0431\u044c\u0451\u0448\u044c\u0441\u044f."};
            Text(Reply, Replies[Model.Node]);
            for (int I = 0; I < 4; ++I)
            {
                bool Visible = I < Model.Count();
                Buttons[I]->Flags = static_cast<unsigned char>((Buttons[I]->Flags & ~3) | (Visible ? 3 : 0));
                Labels[I]->Flags = static_cast<unsigned char>((Labels[I]->Flags & ~3) | (Visible ? 3 : 0));
                if (Visible) Text(Labels[I], Model.Node == 0 ? Choices[I] :
                    (I == 0 ? L"1. \u041d\u0430\u0437\u0430\u0434." : L"2. \u0417\u0430\u043a\u043e\u043d\u0447\u0438\u0442\u044c \u0440\u0430\u0437\u0433\u043e\u0432\u043e\u0440."));
            }
        }
        void Choose(int I)
        {
            if (Model.Done || Speaking) return;
            if (Tree) {
                auto Count = reinterpret_cast<CountFn>(GetProcAddress(Content(), "RpgDialogChoiceCount"));
                if (!Count || I < 0 || I >= Count(DialogId, NodeId)) return;
                PendingChoice = I;
                if (StartLine(I)) return;
                PendingChoice = -1;
            }
            ApplyChoice(I);
        }
        void ApplyChoice(int I)
        {
            if (Tree)
            {
                auto ChooseNode = reinterpret_cast<ChooseFn>(GetProcAddress(Content(), "RpgDialogChoose"));
                unsigned Next = ChooseNode != nullptr
                    ? ChooseNode(DialogId, NodeId, I, GetPlayerConnectionId()) : 0;
                if (Next == 0)
                    Model.Done = true;
                else
                {
                    NodeId = Next;
                    PlayNode();
                }
                return;
            }
            if (Offer)
            {
                if (I == 0) PendingAccept = true;
                Model.Done = true;
                return;
            }
            Model.Choose(I);
            if (!Model.Done) Refresh();
        }
        bool Create(Win3D* ParentWindow, void* Data) override
        {
            Offer = WantOffer;
            ClassName = "RpgDialog"; SetName("RpgDialog");
            // Win3DDrawAll visits sublayers 0..7 only.
            DrawLayer = 0x6f; DrawSubLayer = 7;
            if (!Win3D::Create(ParentWindow, Data)) return false;
            float Pos[3] = {-0.48f, -0.15f, 0};
            Reply = CreateRichTextWin("RpgReply", 0.96f, 0.09f, Pos, false);
            Reply->SetNeverHit(true);
            for (int I=0; I<4; ++I)
            {
                Pos[0] = 0; Pos[1] = -0.27f - 0.052f * I;
                float const Extents[3] = {0.49f, 0.024f, 0};
                Buttons[I] = CreateWireButtonControl("RpgChoiceHit", "ui_select_item", Pos, Extents, 0, 1, 0, 0, 0);
                Pos[0] = -0.48f; Pos[1] += 0.023f;
                Labels[I] = CreateRichTextWin("RpgChoiceText", 0.96f, 0.048f, Pos, false);
                Labels[I]->SetNeverHit(true);
            }
            float const Center[3] = {0,0,-1.288f}; SetPosition(Center);
            Refresh(); CaptureMouse();
            return true;
        }
        intptr_t SetProperty(int Msg, uintptr_t A, uintptr_t B) override
        {
            if (Msg == 0x26)
                for(int I=0; I<4; ++I)
                    if(A == reinterpret_cast<uintptr_t>(Buttons[I])) { Choose(I); return 1; }
            return WinControl::SetProperty(Msg,A,B);
        }
    };
    FDialog* Dialog = nullptr;
}
void RpgDialogOpen(FGfScriptSequence* Sequence)
{
    WantOffer = false;
    if (Dialog) return;
    Owner = Sequence;
    Dialog = new FDialog;
    if (!Dialog->Create(nullptr,nullptr))
    {
        delete Dialog; Dialog=nullptr; Owner=nullptr;
        Sequence->Entries[Sequence->Current].Script->Pause();
        return;
    }
    SetLetterboxTarget(0.0f, 3.0f);
    SetClientMouseCursorDrawFlag(1);
}
void RpgDialogOpenTree(FGfScriptSequence* Sequence, unsigned InDialog)
{
    WantOffer = false;
    if (Dialog) return;
    Owner = Sequence;
    Dialog = new FDialog;
    Dialog->Tree = true;
    Dialog->DialogId = InDialog;
    using GroupFn = char const* (__cdecl*)(unsigned);
    auto Group = reinterpret_cast<GroupFn>(GetProcAddress(GetModuleHandleA("Content.dll"), "RpgDialogSceneGroup"));
    if (Group) Dialog->SceneGroup = Group(InDialog);
    auto Gestures = reinterpret_cast<GroupFn>(GetProcAddress(GetModuleHandleA("Content.dll"), "RpgDialogGestureGroup"));
    Dialog->GestureGroup = Gestures ? Gestures(InDialog) : Dialog->SceneGroup;
    auto Start = reinterpret_cast<FDialog::StartFn>(GetProcAddress(GetModuleHandleA("Content.dll"), "RpgDialogStart"));
    auto Begin = reinterpret_cast<FDialog::BeginFn>(GetProcAddress(GetModuleHandleA("Content.dll"), "RpgDialogBeginSession"));
    Dialog->NodeId = Begin ? Begin(InDialog, GetPlayerConnectionId()) : Start != nullptr ? Start(InDialog) : 0;
    if (!Dialog->NodeId || !Dialog->Create(nullptr,nullptr))
    {
        delete Dialog; Dialog=nullptr; Owner=nullptr;
        Sequence->Entries[Sequence->Current].Script->Pause();
        return;
    }
    Dialog->PlayNode();
    SetLetterboxTarget(0.0f, 3.0f);
    SetClientMouseCursorDrawFlag(1);
}
void RpgDialogOpenOffer(FGfScriptSequence* Sequence)
{
    WantOffer = true;
    if (Dialog) return;
    Owner = Sequence;
    Dialog = new FDialog;
    if (!Dialog->Create(nullptr,nullptr))
    {
        delete Dialog; Dialog=nullptr; Owner=nullptr;
        Sequence->Entries[Sequence->Current].Script->Pause();
        return;
    }
    SetLetterboxTarget(0.0f, 3.0f);
    SetClientMouseCursorDrawFlag(1);
}
void RpgDialogClose(FGfScriptSequence* Sequence)
{
    if (Owner != Sequence) return;
    auto End = reinterpret_cast<void (__cdecl*)(unsigned)>(GetProcAddress(GetModuleHandleA("Content.dll"), "RpgDialogEndSession"));
    if (End) End(GetPlayerConnectionId());
    delete Dialog; Dialog=nullptr; Owner=nullptr;
}
void RpgDialogUpdate(FGfScriptSequence* Sequence, int Ms)
{
    if (Owner != Sequence) return;
    if (Dialog) Dialog->UpdateGestures(Ms);
    if (Dialog && Dialog->Speaking) {
        if (Dialog->Speech) {
            if (Dialog->Speech->Script->Update(Ms)) Dialog->FinishSpeech();
        } else if ((Dialog->FallbackMs -= Ms) <= 0) Dialog->FinishSpeech();
    }
    if (Owner == Sequence && Dialog && Dialog->Model.Done)
    {
        RpgDialogClose(Sequence);
        Sequence->Entries[Sequence->Current].Script->Pause();
    }
}
bool RpgDialogConsumeAccept()
{
    bool const Accepted = PendingAccept;
    PendingAccept = false;
    return Accepted;
}
bool RpgDialogHandleKey(unsigned Message, unsigned Key, unsigned Flags)
{
    if (Message == WM_KILLFOCUS || (Message == WM_ACTIVATEAPP && !Key)) EscapeHeld = false;
    if (Key == VK_ESCAPE && EscapeHeld) {
        if (Message == WM_KEYUP || Message == WM_SYSKEYUP) EscapeHeld = false;
        return true;
    }
    if (!Dialog) return false;
    if (Message != WM_KEYDOWN && Message != WM_KEYUP && Message != WM_SYSKEYDOWN && Message != WM_SYSKEYUP) return false;
    if (Message == WM_KEYDOWN && (Flags & (1u<<30)) == 0)
    {
        if(Key >= '1' && Key <= '4') Dialog->Choose(static_cast<int>(Key-'1'));
        else if(Key == VK_ESCAPE) {
            EscapeHeld = true;
            if (Dialog->Speaking) Dialog->FinishSpeech();
            else {
                using EscapeFn = unsigned (__cdecl*)(unsigned, unsigned, unsigned);
                auto Escape = reinterpret_cast<EscapeFn>(GetProcAddress(GetModuleHandleA("Content.dll"), "RpgDialogEscape"));
                unsigned const Next = Escape && !Dialog->SceneGroup.empty() ? Escape(Dialog->DialogId, Dialog->NodeId, GetPlayerConnectionId()) : 0;
                if (Next) { Dialog->NodeId = Next; Dialog->PlayNode(); }
                else Dialog->Model.Done = true;
            }
        }
    }
    return true;
}
#endif
