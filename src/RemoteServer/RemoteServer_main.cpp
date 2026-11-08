// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

#include <windows.h>
#define RPCLOCAL_EXPORTS
#define REMOTESERVER_INSTANCE_DEFINITION
#include "../include/rpc_iserver.h"
#undef REMOTESERVER_INSTANCE_DEFINITION
#include "../include/common_server.h"
#include "../include/rpc_iclient.h"
#include "../include/freelancer_client.h"
#include "../include/common_misc.h" // SinglePlayer
// CollisionGroupDesc's complete definition (ch2 0x48, IClient::SendServerSetCollisionGroups).
#include "../include/common_archetype.h"
#include "../include/net_session.h"
#include "../include/rpc_packet.h"
#include "../include/rpc_packet_codec.h"
#include "../include/rpc_server_channel_codec.h" // Canonical hardpoint dictionary builder.
#include "../include/msvcrt_compat.h"
#include "rpc_server_channel_receive_private.h"

#include <list>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cwchar>

#include "../include/rpc_iclient_args.h"

namespace
{
    IClient* GGameClient = static_cast<IClient*>(&Client);
    IChatClient* GGameChatClient = static_cast<IChatClient*>(&Client);

    HMODULE GClientModule = nullptr;
    IClient* GLoadedClient = nullptr;
    IChatClient* GLoadedChatClient = nullptr;
    IClient* GStartupClient = nullptr;

    typedef IClient* (__cdecl* FGetClientInterface)();
    typedef IChatClient* (__cdecl* FGetChatClientInterface)();

    // FUN_06bd1000: the caller's SStartupInfo owns the client-module path.
    IClient* LoadClientModule(const char* ModulePath)
    {
        GClientModule = LoadLibraryA(ModulePath);
        if (GClientModule != nullptr) {
            FGetClientInterface ClientGetter = reinterpret_cast<FGetClientInterface>(GetProcAddress(GClientModule, "GetClientInterface"));
            GLoadedClient = ClientGetter();
            FGetChatClientInterface ChatGetter = reinterpret_cast<FGetChatClientInterface>(GetProcAddress(GClientModule, "GetChatClientInterface"));
            GLoadedChatClient = ChatGetter();
        }
        return GLoadedClient;
    }

    // FUN_06bd1050: release the matching module reference and clear both facades.
    void UnloadClientModule()
    {
        if (GClientModule != nullptr) {
            FreeLibrary(GClientModule);
            GClientModule = nullptr;
            GLoadedClient = nullptr;
            GLoadedChatClient = nullptr;
        }
    }
}

class FRemoteServerClient;

// Native derived vtables: 06c0b8d8 (IServer) and 06c0b8d0 (IChatServer).
// Internal C++ layout follows our current compiler; only the RPC wire is fixed.
struct FRemoteServerImpl final : IServerImpl
{
    bool Startup(const SStartupInfo& Info) override;
    void Shutdown() override;
    int Update() override;
    void PushToServer(CDAPacket* Packet) override;
    void Connect(const char* ServerName, unsigned short* Password) override;
    void DisConnect(unsigned int SessionId, EFLConnection Type) override;
    void SetActiveConnection(EFLConnection Connection) override;
    bool SwapConnections(EFLConnection ConnA, EFLConnection ConnB) override;

    NetClient* Transport = nullptr;
    CRITICAL_SECTION CriticalSection;
    bool bConnected = false;
    EFLConnection ActiveConnection = static_cast<EFLConnection>(0);
};

extern "C" __declspec(dllexport) FRemoteServerImpl Server;
FRemoteServerImpl Server;

void OnRemoteConnect(long Result, void*);
void OnRemoteReceive(unsigned char* Data, unsigned int Size, void*);
void OnRemoteDisconnect(void*);

extern int RegisterChannel1Packets(FPacketSerializer* Serializer);
extern int RegisterChannel2Packets(FPacketSerializer* Serializer);
extern int RegisterChannel3Packets(FPacketSerializer* Serializer);

// LAB_06bd9930. Keep the actual network object separate from exported base no-ops.
bool FRemoteServerImpl::Startup(const SStartupInfo& Info)
{
    bool bResult = false;
    GStartupClient = LoadClientModule(Info.ModulePath);
    if (GStartupClient != nullptr) {
        bResult = GStartupClient->Startup(Info.MaxPlayers, Info.Port);
        Transport = new (std::nothrow) NetClient();
        NetClientHandler Handler = {};
        Handler.OnConnect = &OnRemoteConnect;
        Handler.OnReceive = &OnRemoteReceive;
        Handler.OnDisconnect = &OnRemoteDisconnect;
        Transport->SetHandler(Handler);
        if (bResult) {
            Serializer = RpcGetRemotePacketSerializer();
            if (Serializer != nullptr &&
                RegisterChannel3Packets(Serializer) == 0 &&
                RegisterChannel1Packets(Serializer) == 0 &&
                RegisterChannel2Packets(Serializer) == 0) {
                bResult = true;
            }
        }
    }
    InitializeCriticalSection(&CriticalSection);
    return bResult;
}

// FUN_06bd9a70: the client facade shuts down before its DirectPlay transport.
void FRemoteServerImpl::Shutdown()
{
    if (GStartupClient != nullptr) {
        GStartupClient->Shutdown();
    }
    if (Transport != nullptr) {
        delete Transport;
        Transport = nullptr;
    }
    if (Serializer != nullptr) {
        Serializer->Release();
    }
    DeleteCriticalSection(&CriticalSection);
    UnloadClientModule();
}

// FUN_06bd9c90.
int FRemoteServerImpl::Update()
{
    GiveServerRunPermission();
    Transport->Dispatch();
    WaitForClientRunPermission();
    return 1;
}

// LAB_06bd9ac0 consumes the packet regardless of encode/send outcome.
void FRemoteServerImpl::PushToServer(CDAPacket* Packet)
{
    unsigned char Buffer[0x2800];
    unsigned char* BufferStart = Buffer;
    unsigned int Length;
    FPacketBase* TypedPacket = reinterpret_cast<FPacketBase*>(Packet);
    if (TypedPacket->Encode(&BufferStart, sizeof(Buffer), &Length) == 0) {
        Transport->Send(Buffer, Length);
    }
    TypedPacket->Release();
}

// LAB_06bd98a0 only accepts a nonnull DirectPlay buffer.
void OnRemoteReceive(unsigned char* Data, unsigned int Size, void*)
{
    if (Data != nullptr) {
        extern void RpcDispatchMsgs(IServerImpl*, const unsigned char*, unsigned int);
        RpcDispatchMsgs(&Server, Data, Size);
    }
}

// LAB_06bd98c0.
void OnRemoteDisconnect(void*)
{
    Server.bConnected = false;
    GStartupClient->DisconnectClient(0);
}

// LAB_06bd98e0 reports only failed DirectPlay connections to freelancer.exe.
void OnRemoteConnect(long Result, void*)
{
    if (Result != 0) {
        typedef void (__cdecl* FHandleConnectError)(long);
        FHandleConnectError Handler = reinterpret_cast<FHandleConnectError>(GetProcAddress(GetModuleHandleA(nullptr), "HandleConnectError"));
        Handler(Result);
    } else {
        Server.bConnected = true;
    }
}

// LAB_06bd9b30: the remote server's own slot always answers false.
bool FRemoteServerImpl::SwapConnections(EFLConnection ConnA, EFLConnection ConnB)
{
    return false;
}

// LAB_06bd9b40 uses a signed comparison against connection slot 2.
void FRemoteServerImpl::SetActiveConnection(EFLConnection Connection)
{
    if (static_cast<int>(Connection) < 2) {
        ActiveConnection = Connection;
    }
}

// LAB_06bd9c70 deliberately notifies the facade without closing CDPClient here.
void FRemoteServerImpl::DisConnect(unsigned int SessionId, EFLConnection Type)
{
    bConnected = false;
    GStartupClient->DisconnectClient(0);
}

// LAB_06bd9b50 skips the native seven-byte URL prefix and tries ports right to left.
void FRemoteServerImpl::Connect(const char* ServerName, unsigned short* Password)
{
    (void)Password;
    char* Copy = _strdup(ServerName);
    char Host[256] = "127.0.0.1";
    unsigned short Port = 2302;
    char* NamePos = std::strstr(Copy, "hostname=");
    if (NamePos != nullptr) {
        NamePos += 9;
        char* End = std::strchr(NamePos, ';');
        if (End != nullptr)
            *End = '\0';
        strncpy(Host, NamePos, sizeof(Host) - 1);
    }
    char* PortPos = std::strstr(Copy, "port=");
    if (PortPos != nullptr)
        Port = static_cast<unsigned short>(MsvcrtAtoi(PortPos + 5));
    else {
        char* Separator = std::strrchr(Copy, ':');
        if (Separator != nullptr && NamePos == nullptr) {
            *Separator = '\0';
            strncpy(Host, Copy, sizeof(Host) - 1);
            Port = static_cast<unsigned short>(MsvcrtAtoi(Separator + 1));
        }
    }
    Transport->Connect(Host, Port);
    std::free(Copy);
}

extern "C" __declspec(dllexport) IServer* __cdecl GetServerInterface()
{
    return &Server;
}

extern "C" __declspec(dllexport) void* __cdecl GetChatServerInterface()
{
    return static_cast<IChatServer*>(&Server);
}

// Each network DLL emits the trivial abstract IClient special members, as retail.
IClient::IClient() {}
IClient::IClient(const IClient& Other) {}
IClient& IClient::operator=(const IClient& Other) { return *this; }

void HandlePacket(unsigned int ClientId, CDAPacket* Packet)
{
    IClient* Client = GGameClient;

    unsigned int Channel = Packet->GetChannel();
    unsigned int Opcode = Packet->GetOpcode();
    const unsigned char* Payload = (const unsigned char*)Packet + 0x20;

    if (Channel == 1)
    {
        // COMMON payloads are reconstructed into real owning argument objects.
        // Dispatch coverage is tracked separately from the packet registry.
        switch (Opcode)
        {
            case 0x01:
            {
                const FRpcUpdateObjectPacket* Wire = reinterpret_cast<const FRpcUpdateObjectPacket*>(Packet);
                FCommonUpdateObjectInfo Info;
                Info.ObjectId = Wire->ObjectId;
                Info.Orientation = Wire->Orientation;
                Info.Position = Wire->Position;
                const float* TimeSource = &Wire->UpdateTime;
                const float* FieldSource = &Wire->Field_0x28;
                float TimeRounded;
                float FieldRounded;
                float* TimeDestination = &Info.Field_0x20;
                float* FieldDestination = &Info.Field_0x24;
                // 06bd3b9a..3bca retains the two intermediate FST operations.
                __asm {
                    mov eax, TimeSource
                    fld dword ptr [eax]
                    fst dword ptr TimeRounded
                    mov eax, FieldSource
                    fld dword ptr [eax]
                    fst dword ptr FieldRounded
                    fxch st(1)
                    mov eax, TimeDestination
                    fstp dword ptr [eax]
                    mov eax, FieldDestination
                    fstp dword ptr [eax]
                }
                Info.Field_0x28 = Wire->Field_0x00;
                Client->SendCommonUpdateObject(1, Info);
                break;
            }
            case 0x02:
            {
                const FRpcFireWeaponPacket* Wire = reinterpret_cast<const FRpcFireWeaponPacket*>(Packet);
                XFireWeaponInfo Info;
                Info.ObjectId = Wire->ObjectId;
                Info.TargetPos = Wire->TargetPos;
                Info.Hardpoints = Wire->Hardpoints;
                Client->SendCommonFireWeapon(1, Info);
                break;
            }
            case 0x04:
            {
                const FRpcSetTargetPacket* Wire = reinterpret_cast<const FRpcSetTargetPacket*>(Packet);
                XSetTarget Info;
                Info.ObjectId = Wire->ObjectId;
                Info.SubObjId = Wire->SubObjId;
                Info.TargetObjectId = Wire->TargetId;
                Info.TargetSubObjId = Wire->TargetSubObjId;
                Client->SendCommonSetTarget(1, Info);
                break;
            }
            case 0x05:
            {
                const FRpcChatMsgPacket* Wire = reinterpret_cast<const FRpcChatMsgPacket*>(Packet);
                GGameChatClient->SendCommonChatMsg(CHAT_ID(1u), CHAT_ID(Wire->Field_0x04), Wire->DataSize,
                    Wire->Data);
                break;
            }
            case 0x08:
            {
                const FRpcActivateEquipPacket* Wire = reinterpret_cast<const FRpcActivateEquipPacket*>(Packet);
                XActivateEquip Info;
                Info.ObjectId = Wire->ObjectId;
                Info.EquipId = Wire->EquipId;
                Info.bActivate = (Wire->bActive != 0);
                Client->SendCommonActivateEquip(1, Info);
                break;
            }
            case 0x0e:
            {
                const FRpcActivateCruisePacket* Wire = reinterpret_cast<const FRpcActivateCruisePacket*>(Packet);
                XActivateCruise Info;
                Info.ObjectId = Wire->ObjectId;
                Info.bActivate = (Wire->bActive != 0);
                Info.Field_0x05 = (Wire->Field_0x05 != 0);
                Client->SendCommonActivateCruise(1, Info);
                break;
            }
            case 0x0f:
            {
                const FRpcGoTradeLanePacket* Wire = reinterpret_cast<const FRpcGoTradeLanePacket*>(Packet);
                XGoTradelane Info;
                Info.ObjectId = Wire->ObjectId;
                Info.TradelaneRing1 = Wire->TradelaneRing1;
                Info.TradelaneRing2 = Wire->TradelaneRing2;
                Info.Field_0x0c = (Wire->Field_0x0c != 0);
                Client->SendCommonGoTradeLane(1, Info);
                break;
            }
            case 0x10:
            {
                const FRpcStopTradeLanePacket* Wire = reinterpret_cast<const FRpcStopTradeLanePacket*>(Packet);
                Client->SendCommonStopTradeLane(1, Wire->ShipId, Wire->TradeLaneRing1, Wire->TradeLaneRing2);
                break;
            }
            case 0x11:
            {
                const FRpcSetWeaponGroupPacket* Wire = reinterpret_cast<const FRpcSetWeaponGroupPacket*>(Packet);
                Client->SendCommonSetWeaponGroup(1, Wire->Data, Wire->DataSize);
                break;
            }
            case 0x12:
            {
                const FRpcPlayerTradePacket* Wire = reinterpret_cast<const FRpcPlayerTradePacket*>(Packet);
                switch (Wire->Action)
                {
                    case 0x01:
                        Client->SendCommonPlayerTradeInitiateTrade(1, Wire->TargetPlayer);
                        break;
                    case 0x02:
                        Client->SendCommonPlayerTradeTerminateTrade(1, Wire->Reason);
                        break;
                    case 0x04:
                        Client->SendCommonPlayerTradeSetTradeMoney(1, Wire->TargetPlayer,
                            static_cast<unsigned long>(Wire->Money));
                        break;
                    case 0x08:
                    {
                        EquipDesc Equip;
                        Equip.set_arch_id(Wire->EquipArchId);
                        Equip.set_count(Wire->EquipCount);
                        Equip.set_status(Wire->EquipHealth);
                        Equip.set_id(Wire->EquipId);
                        Client->SendCommonPlayerTradeAddTradeEquip(1, Wire->TargetPlayer, Equip);
                        break;
                    }
                    case 0x10:
                    {
                        EquipDesc Equip;
                        Equip.set_arch_id(Wire->EquipArchId);
                        Equip.set_count(Wire->EquipCount);
                        Equip.set_id(Wire->EquipId);
                        Client->SendCommonPlayerTradeDelTradeEquip(1, Wire->TargetPlayer, Equip);
                        break;
                    }
                    case 0x20:
                        Client->SendCommonPlayerTradeRequestTrade(1, Wire->TargetPlayer);
                        break;
                    case 0x40:
                        // The wire byte as the bool: the callee keeps one byte (rpclocal
                        // 06d8b963), so only values above 1 would differ.
                        Client->SendCommonPlayerTradeAcceptTrade(1, Wire->TargetPlayer, Wire->bAccepted != 0);
                        break;
                    case 0x80:
                        Client->SendCommonPlayerTradeStopTradeRequest(1, Wire->TargetPlayer);
                        break;
                }
                break;
            }
            case 0x13:
            {
                const FRpcSetVisitedStatePacket* Wire = reinterpret_cast<const FRpcSetVisitedStatePacket*>(Packet);
                Client->SendCommonSetVisitedState(1, Wire->Data, Wire->DataSize);
                break;
            }
            case 0x14:
            {
                const FRpcJettisonCargoPacket* Wire = reinterpret_cast<const FRpcJettisonCargoPacket*>(Packet);
                XJettisonCargo Info;
                Info.ObjectId = Wire->ObjectId;
                Info.ItemId = Wire->ItemId;
                Info.Count = Wire->Count;
                Client->SendCommonJettisonCargo(1, Info);
                break;
            }
            case 0x15:
            {
                const FRpcActivateThrustersPacket* Wire = reinterpret_cast<const FRpcActivateThrustersPacket*>(Packet);
                XActivateThrusters Info;
                Info.ObjectId = Wire->ObjectId;
                Info.bActivate = (Wire->bActive != 0);
                Client->SendCommonActivateThrusters(1, Info);
                break;
            }
            case 0x16:
            {
                const FRpcRequestBestPathPacket* Wire = reinterpret_cast<const FRpcRequestBestPathPacket*>(Packet);
                Client->SendCommonRequestBestPath(1, Wire->Data, Wire->DataSize);
                break;
            }
            case 0x17:
            {
                const FRpcRequestGroupPositionsPacket* Wire = reinterpret_cast<const FRpcRequestGroupPositionsPacket*>(Packet);
                Client->SendCommonRequestGroupPositions(1, Wire->Data, Wire->DataSize);
                break;
            }
            case 0x18:
            {
                const FRpcRequestPlayerStatsPacket* Wire = reinterpret_cast<const FRpcRequestPlayerStatsPacket*>(Packet);
                Client->SendCommonRequestPlayerStats(1, Wire->Data, Wire->DataSize);
                break;
            }
            case 0x19:
            {
                const FRpcSetMissionLogPacket* Wire = reinterpret_cast<const FRpcSetMissionLogPacket*>(Packet);
                Client->SendCommonSetMissionLog(1, Wire->Data, Wire->DataSize);
                break;
            }
            case 0x1a:
            {
                const FRpcRequestRankLevelPacket* Wire = reinterpret_cast<const FRpcRequestRankLevelPacket*>(Packet);
                Client->SendCommonRequestRankLevel(1, Wire->Data, Wire->DataSize);
                break;
            }
            case 0x1b:
            {
                const FRpcPopUpDialogPacket* Wire = reinterpret_cast<const FRpcPopUpDialogPacket*>(Packet);
                FmtStr TextA;
                FmtStr TextB;
                TextA.unflatten(Wire->DataA, Wire->SizeA);
                TextB.unflatten(Wire->DataB, Wire->SizeB);
                Client->SendCommonPopUpDialog(1, TextA, TextB, Wire->Field_0x10);
                break;
            }
            case 0x1c:
            {
                const FRpcSetInterfaceStatePacket* Wire = reinterpret_cast<const FRpcSetInterfaceStatePacket*>(Packet);
                Client->SendCommonSetInterfaceState(1, Wire->Data, Wire->DataSize);
                break;
            }
            case 0x1d:
            {
                const FRpcTractorObjectsPacket* Wire = reinterpret_cast<const FRpcTractorObjectsPacket*>(Packet);
                XTractorObjects Info;
                Info.ObjectId = Wire->ObjectId;
                Info.TractorEquipId = Wire->TractorEquipId;
                Info.TargetIds = Wire->TargetIds;
                Client->SendCommonTractorObjects(1, Info);
                break;
            }
        }
    }

    if (Channel == 2)
    {
        RpcReceiveServerChannel(ClientId, reinterpret_cast<FPacketBase*>(Packet), Client);
    }
}

