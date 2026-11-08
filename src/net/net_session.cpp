#include "../include/net_session.h"

#include <winsock2.h>
#include <ws2tcpip.h>

#include <cstdint>
#include <cstring>
#include <vector>

#pragma comment(lib, "ws2_32.lib")

namespace
{
    unsigned int const kMagic = 0x314E4C46u;
    unsigned int const kMaxPayload = 0x2800u;
    unsigned int const kReliableBudget = 32768u;
    int const kWindow = 32;

    unsigned char const kKindConnect = 1;
    unsigned char const kKindData = 2;
    unsigned char const kKindDisconnect = 3;
    unsigned char const kKindAck = 4;

    int const kLanePose = 0;
    int const kLaneReliable = 1;

    bool g_Wsa = false;

    void EnsureWsa()
    {
        if (g_Wsa)
            return;
        WSADATA Data;
        if (WSAStartup(MAKEWORD(2, 2), &Data) == 0)
            g_Wsa = true;
    }

    bool Newer(unsigned short Seq, unsigned short Last)
    {
        return static_cast<short>(Seq - Last) > 0;
    }

    struct Datagram
    {
        unsigned char Kind = 0;
        unsigned char Lane = 0;
        unsigned short Seq = 0;
        unsigned short Ack = 0;
        unsigned int AckBits = 0;
        unsigned short PayloadLen = 0;
        unsigned char Payload[kMaxPayload];
    };

    int Encode(unsigned char* Out, unsigned int Cap, Datagram const& Msg)
    {
        unsigned int const Need = 12u + Msg.PayloadLen;
        if (Need > Cap || Msg.PayloadLen > kMaxPayload)
            return 0;
        unsigned int Cursor = 0;
        std::memcpy(Out + Cursor, &kMagic, 4);
        Cursor += 4;
        Out[Cursor++] = Msg.Kind;
        Out[Cursor++] = Msg.Lane;
        std::memcpy(Out + Cursor, &Msg.Seq, 2);
        Cursor += 2;
        std::memcpy(Out + Cursor, &Msg.Ack, 2);
        Cursor += 2;
        std::memcpy(Out + Cursor, &Msg.AckBits, 4);
        Cursor += 4;
        std::memcpy(Out + Cursor, Msg.Payload, Msg.PayloadLen);
        return static_cast<int>(Need);
    }

    bool Decode(unsigned char const* In, int Size, Datagram& Msg)
    {
        if (Size < 12)
            return false;
        unsigned int Magic = 0;
        std::memcpy(&Magic, In, 4);
        if (Magic != kMagic)
            return false;
        Msg.Kind = In[4];
        Msg.Lane = In[5];
        std::memcpy(&Msg.Seq, In + 6, 2);
        std::memcpy(&Msg.Ack, In + 8, 2);
        std::memcpy(&Msg.AckBits, In + 10, 4);
        int const Payload = Size - 12;
        if (Payload < 0 || static_cast<unsigned int>(Payload) > kMaxPayload)
            return false;
        Msg.PayloadLen = static_cast<unsigned short>(Payload);
        if (Payload > 0)
            std::memcpy(Msg.Payload, In + 12, static_cast<size_t>(Payload));
        return true;
    }
}

int NetLaneForPacket(unsigned char const* Data, unsigned int Size)
{
    if (Data == nullptr || Size < 2)
        return kLaneReliable;
    unsigned short Header = 0;
    std::memcpy(&Header, Data, 2);
    unsigned int const Channel = Header >> 8;
    unsigned int const Opcode = Header & 0xffu;
    if (Channel == 1 && (Opcode == 0x01 || Opcode == 0x02 || Opcode == 0x0e || Opcode == 0x15))
        return kLanePose;
    if (Channel == 3 && Opcode == 0x01)
        return kLanePose;
    return kLaneReliable;
}

struct ReliableSlot
{
    unsigned short Seq = 0;
    DWORD SentAt = 0;
    std::vector<unsigned char> Bytes;
};

struct NetLink::Impl
{
    sockaddr_in Addr = {};
    bool bClosing = false;
    bool bHavePose = false;
    unsigned short LastPose = 0;
    unsigned short NextPose = 1;
    unsigned short NextReliable = 1;
    unsigned short ExpectReliable = 1;
    unsigned short PeerAck = 0;
    unsigned int PeerAckBits = 0;
    std::vector<ReliableSlot> Unacked;
    std::vector<unsigned char> Held[kWindow];
    bool bHeld[kWindow] = {};
    int QueuedBytes = 0;
    int QueuedCount = 0;
    unsigned long BytesSentReliable = 0;
    unsigned long PacketsSentReliable = 0;
    NetHost::Impl* Host = nullptr;
    NetClient::Impl* Client = nullptr;
};

struct NetHost::Impl
{
    SOCKET Socket = INVALID_SOCKET;
    unsigned short Port = 0;
    int MaxPlayers = 128;
    NetHostHandler Handler = {};
    NetLink Links[128] = {};
    NetLink::Impl States[128] = {};
    bool bUsed[128] = {};
};

struct NetClient::Impl
{
    SOCKET Socket = INVALID_SOCKET;
    sockaddr_in Server = {};
    bool bConnecting = false;
    bool bConnected = false;
    DWORD ConnectSent = 0;
    NetClientHandler Handler = {};
    NetLink::Impl State;
    NetLink Link;
};

namespace
{
    void Recount(NetLink::Impl& State)
    {
        State.QueuedBytes = 0;
        State.QueuedCount = static_cast<int>(State.Unacked.size());
        for (size_t Index = 0; Index < State.Unacked.size(); ++Index)
            State.QueuedBytes += static_cast<int>(State.Unacked[Index].Bytes.size());
    }

    bool SendRaw(SOCKET Socket, sockaddr_in const& Addr, unsigned char const* Bytes, int Size)
    {
        if (Socket == INVALID_SOCKET || Size <= 0)
            return false;
        int const Sent = sendto(Socket, reinterpret_cast<char const*>(Bytes), Size, 0,
            reinterpret_cast<sockaddr const*>(&Addr), sizeof(Addr));
        return Sent == Size;
    }

    void SendDatagram(SOCKET Socket, sockaddr_in const& Addr, Datagram const& Msg)
    {
        unsigned char Raw[12 + kMaxPayload];
        int const Size = Encode(Raw, sizeof(Raw), Msg);
        if (Size > 0)
            SendRaw(Socket, Addr, Raw, Size);
    }

    void ApplyAck(NetLink::Impl& State, unsigned short Ack, unsigned int AckBits)
    {
        State.PeerAck = Ack;
        State.PeerAckBits = AckBits;
        std::vector<ReliableSlot> Keep;
        for (size_t Index = 0; Index < State.Unacked.size(); ++Index)
        {
            unsigned short const Seq = State.Unacked[Index].Seq;
            short const Delta = static_cast<short>(Seq - Ack);
            bool bAcked = Delta <= 0;
            if (!bAcked && Delta > 0 && Delta <= 32)
                bAcked = (AckBits & (1u << (Delta - 1))) != 0;
            if (!bAcked)
                Keep.push_back(State.Unacked[Index]);
        }
        State.Unacked.swap(Keep);
        Recount(State);
    }

    void QueueReliable(SOCKET Socket, NetLink::Impl& State, unsigned char const* Payload, unsigned int Size)
    {
        if (Size > kMaxPayload || State.Unacked.size() >= 64)
            return;
        Datagram Msg;
        Msg.Kind = kKindData;
        Msg.Lane = kLaneReliable;
        Msg.Seq = State.NextReliable++;
        Msg.Ack = static_cast<unsigned short>(State.ExpectReliable - 1);
        Msg.PayloadLen = static_cast<unsigned short>(Size);
        if (Size > 0)
            std::memcpy(Msg.Payload, Payload, Size);
        unsigned char Raw[12 + kMaxPayload];
        int const Encoded = Encode(Raw, sizeof(Raw), Msg);
        if (Encoded <= 0)
            return;
        ReliableSlot Slot;
        Slot.Seq = Msg.Seq;
        Slot.SentAt = GetTickCount();
        Slot.Bytes.assign(Raw, Raw + Encoded);
        State.Unacked.push_back(Slot);
        State.BytesSentReliable += static_cast<unsigned long>(Encoded);
        ++State.PacketsSentReliable;
        Recount(State);
        SendRaw(Socket, State.Addr, Raw, Encoded);
    }

    void SendPose(SOCKET Socket, NetLink::Impl& State, unsigned char const* Payload, unsigned int Size)
    {
        if (Size > kMaxPayload)
            return;
        Datagram Msg;
        Msg.Kind = kKindData;
        Msg.Lane = kLanePose;
        Msg.Seq = State.NextPose++;
        Msg.PayloadLen = static_cast<unsigned short>(Size);
        if (Size > 0)
            std::memcpy(Msg.Payload, Payload, Size);
        SendDatagram(Socket, State.Addr, Msg);
    }

    void SendAck(SOCKET Socket, NetLink::Impl& State)
    {
        Datagram Msg;
        Msg.Kind = kKindAck;
        Msg.Lane = kLaneReliable;
        Msg.Ack = static_cast<unsigned short>(State.ExpectReliable - 1);
        unsigned int Bits = 0;
        for (int Index = 0; Index < kWindow; ++Index)
        {
            if (State.bHeld[Index])
                Bits |= 1u << Index;
        }
        Msg.AckBits = Bits;
        SendDatagram(Socket, State.Addr, Msg);
    }

    void Retransmit(SOCKET Socket, NetLink::Impl& State)
    {
        DWORD const Now = GetTickCount();
        for (size_t Index = 0; Index < State.Unacked.size(); ++Index)
        {
            if (Now - State.Unacked[Index].SentAt < 100)
                continue;
            SendRaw(Socket, State.Addr, State.Unacked[Index].Bytes.data(),
                static_cast<int>(State.Unacked[Index].Bytes.size()));
            State.Unacked[Index].SentAt = Now;
        }
    }

    void DeliverReliable(NetLink::Impl& State, Datagram const& Msg,
        void (*OnReceive)(NetLink*, unsigned char*, unsigned int, void*),
        NetLink* Link, void* User, SOCKET Socket)
    {
        short const Delta = static_cast<short>(Msg.Seq - State.ExpectReliable);
        if (Delta < 0)
        {
            SendAck(Socket, State);
            return;
        }
        if (Delta >= kWindow)
            return;
        if (Delta > 0)
        {
            if (!State.bHeld[Delta])
            {
                State.Held[Delta].assign(Msg.Payload, Msg.Payload + Msg.PayloadLen);
                State.bHeld[Delta] = true;
            }
            SendAck(Socket, State);
            return;
        }
        if (OnReceive != nullptr && Msg.PayloadLen > 0)
            OnReceive(Link, const_cast<unsigned char*>(Msg.Payload), Msg.PayloadLen, User);
        ++State.ExpectReliable;
        while (State.bHeld[1])
        {
            if (OnReceive != nullptr && !State.Held[1].empty())
                OnReceive(Link, State.Held[1].data(), static_cast<unsigned int>(State.Held[1].size()), User);
            for (int Index = 1; Index < kWindow - 1; ++Index)
            {
                State.Held[Index].swap(State.Held[Index + 1]);
                State.bHeld[Index] = State.bHeld[Index + 1];
            }
            State.Held[kWindow - 1].clear();
            State.bHeld[kWindow - 1] = false;
            ++State.ExpectReliable;
        }
        SendAck(Socket, State);
    }
}

void NetLink::Send(void const* Data, unsigned int Size)
{
    if (State == nullptr || Data == nullptr || Size == 0 || State->bClosing)
        return;
    int const Lane = NetLaneForPacket(static_cast<unsigned char const*>(Data), Size);
    if (State->Host != nullptr)
    {
        SOCKET const Socket = State->Host->Socket;
        if (Lane == kLanePose)
            SendPose(Socket, *State, static_cast<unsigned char const*>(Data), Size);
        else
            QueueReliable(Socket, *State, static_cast<unsigned char const*>(Data), Size);
    }
}

void NetLink::Disconnect()
{
    if (State == nullptr || State->bClosing)
        return;
    State->bClosing = true;
    Datagram Msg;
    Msg.Kind = kKindDisconnect;
    if (State->Host != nullptr)
        SendDatagram(State->Host->Socket, State->Addr, Msg);
}

double NetLink::GetLinkSaturation() const
{
    if (State == nullptr)
        return 0.0;
    double const Ratio = static_cast<double>(State->QueuedBytes) / static_cast<double>(kReliableBudget);
    if (Ratio < 0.0)
        return 0.0;
    if (Ratio > 1.0)
        return 1.0;
    return Ratio;
}

unsigned int NetLink::GetSendQBytes() const
{
    return State != nullptr ? static_cast<unsigned int>(State->QueuedBytes) : 0u;
}

unsigned int NetLink::GetSendQSize() const
{
    return State != nullptr ? static_cast<unsigned int>(State->QueuedCount) : 0u;
}

NetHost::NetHost()
    : Pipe(new Impl)
{
}

NetHost::~NetHost()
{
    Shutdown();
    delete Pipe;
    Pipe = nullptr;
}

bool NetHost::BeginHosting(unsigned int Port)
{
    EnsureWsa();
    if (Pipe->Socket != INVALID_SOCKET)
        Shutdown();
    Pipe->Socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (Pipe->Socket == INVALID_SOCKET)
        return false;
    u_long NonBlock = 1;
    ioctlsocket(Pipe->Socket, FIONBIO, &NonBlock);
    sockaddr_in Addr = {};
    Addr.sin_family = AF_INET;
    Addr.sin_addr.s_addr = htonl(INADDR_ANY);
    Addr.sin_port = htons(static_cast<unsigned short>(Port));
    if (bind(Pipe->Socket, reinterpret_cast<sockaddr*>(&Addr), sizeof(Addr)) != 0)
    {
        closesocket(Pipe->Socket);
        Pipe->Socket = INVALID_SOCKET;
        return false;
    }
    sockaddr_in Bound = {};
    int BoundLen = sizeof(Bound);
    if (getsockname(Pipe->Socket, reinterpret_cast<sockaddr*>(&Bound), &BoundLen) == 0)
        Pipe->Port = ntohs(Bound.sin_port);
    else
        Pipe->Port = static_cast<unsigned short>(Port);
    return true;
}

void NetHost::SetHandler(NetHostHandler Handler)
{
    Pipe->Handler = Handler;
}

void NetHost::SetSessionName(wchar_t const*) {}
void NetHost::SetPassword(wchar_t const*) {}
void NetHost::SetMaxPlayers(int MaxPlayers) { Pipe->MaxPlayers = MaxPlayers; }
void NetHost::SetEnumResponse(void*, unsigned long) {}

void NetHost::GetPort(std::vector<unsigned long>& Ports)
{
    Ports.clear();
    if (Pipe->Port != 0)
        Ports.push_back(Pipe->Port);
}

NetLink* NetHost::Find(unsigned int Slot) const
{
    if (Slot == 0 || Slot > 128 || !Pipe->bUsed[Slot - 1])
        return nullptr;
    return &Pipe->Links[Slot - 1];
}

void NetHost::Drop(unsigned int Slot)
{
    if (Pipe == nullptr || Slot == 0 || Slot > 128)
        return;
    Pipe->bUsed[Slot - 1] = false;
}

void NetHost::Shutdown()
{
    if (Pipe == nullptr)
        return;
    if (Pipe->Socket != INVALID_SOCKET)
    {
        closesocket(Pipe->Socket);
        Pipe->Socket = INVALID_SOCKET;
    }
    for (int Index = 0; Index < 128; ++Index)
        Pipe->bUsed[Index] = false;
}

void NetHost::Dispatch()
{
    if (Pipe->Socket == INVALID_SOCKET)
        return;
    for (;;)
    {
        unsigned char Raw[12 + kMaxPayload];
        sockaddr_in From = {};
        int FromLen = sizeof(From);
        int const Got = recvfrom(Pipe->Socket, reinterpret_cast<char*>(Raw), sizeof(Raw), 0,
            reinterpret_cast<sockaddr*>(&From), &FromLen);
        if (Got == SOCKET_ERROR || Got <= 0)
            break;
        Datagram Msg;
        if (!Decode(Raw, Got, Msg))
            continue;
        int Slot = -1;
        for (int Index = 0; Index < 128; ++Index)
        {
            if (!Pipe->bUsed[Index])
                continue;
            if (Pipe->States[Index].Addr.sin_addr.s_addr == From.sin_addr.s_addr &&
                Pipe->States[Index].Addr.sin_port == From.sin_port)
            {
                Slot = Index;
                break;
            }
        }
        if (Msg.Kind == kKindConnect && Slot < 0)
        {
            if (Pipe->MaxPlayers < 1)
                continue;
            int Free = -1;
            int Used = 0;
            for (int Index = 0; Index < 128; ++Index)
            {
                if (Pipe->bUsed[Index])
                    ++Used;
                else if (Free < 0)
                    Free = Index;
            }
            if (Free < 0 || Used >= Pipe->MaxPlayers)
                continue;
            Pipe->bUsed[Free] = true;
            Pipe->States[Free] = NetLink::Impl();
            Pipe->States[Free].Addr = From;
            Pipe->States[Free].Host = Pipe;
            Pipe->Links[Free].State = &Pipe->States[Free];
            Pipe->Links[Free].Slot = static_cast<unsigned int>(Free + 1);
            Slot = Free;
            if (Pipe->Handler.OnConnect != nullptr)
                Pipe->Handler.OnConnect(&Pipe->Links[Free], Pipe->Handler.User);
            continue;
        }
        if (Slot < 0)
            continue;
        NetLink::Impl& State = Pipe->States[Slot];
        if (Msg.Kind == kKindAck || Msg.Kind == kKindData)
            ApplyAck(State, Msg.Ack, Msg.AckBits);
        if (Msg.Kind == kKindDisconnect)
        {
            if (Pipe->Handler.OnDisconnect != nullptr)
                Pipe->Handler.OnDisconnect(&Pipe->Links[Slot], Pipe->Handler.User);
            Pipe->bUsed[Slot] = false;
            continue;
        }
        if (Msg.Kind != kKindData || Msg.PayloadLen == 0)
            continue;
        if (Msg.Lane == kLanePose)
        {
            if (!State.bHavePose || Newer(Msg.Seq, State.LastPose))
            {
                State.bHavePose = true;
                State.LastPose = Msg.Seq;
                if (Pipe->Handler.OnReceive != nullptr)
                    Pipe->Handler.OnReceive(&Pipe->Links[Slot], Msg.Payload, Msg.PayloadLen, Pipe->Handler.User);
            }
            continue;
        }
        DeliverReliable(State, Msg, Pipe->Handler.OnReceive, &Pipe->Links[Slot], Pipe->Handler.User, Pipe->Socket);
    }
    for (int Index = 0; Index < 128; ++Index)
    {
        if (Pipe->bUsed[Index])
            Retransmit(Pipe->Socket, Pipe->States[Index]);
    }
}

NetClient::NetClient()
    : Pipe(new Impl)
{
    Pipe->Link.State = &Pipe->State;
}

NetClient::~NetClient()
{
    Close();
    delete Pipe;
    Pipe = nullptr;
}

void NetClient::SetHandler(NetClientHandler Handler)
{
    Pipe->Handler = Handler;
}

bool NetClient::Connect(char const* Host, unsigned short Port)
{
    EnsureWsa();
    Close();
    Pipe->Socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (Pipe->Socket == INVALID_SOCKET)
        return false;
    u_long NonBlock = 1;
    ioctlsocket(Pipe->Socket, FIONBIO, &NonBlock);
    Pipe->Server = {};
    Pipe->Server.sin_family = AF_INET;
    Pipe->Server.sin_port = htons(Port);
    if (inet_pton(AF_INET, Host, &Pipe->Server.sin_addr) != 1)
    {
        addrinfo Hints = {};
        Hints.ai_family = AF_INET;
        Hints.ai_socktype = SOCK_DGRAM;
        addrinfo* Result = nullptr;
        if (getaddrinfo(Host, nullptr, &Hints, &Result) != 0 || Result == nullptr)
        {
            closesocket(Pipe->Socket);
            Pipe->Socket = INVALID_SOCKET;
            return false;
        }
        Pipe->Server.sin_addr = reinterpret_cast<sockaddr_in*>(Result->ai_addr)->sin_addr;
        freeaddrinfo(Result);
    }
    Pipe->State = NetLink::Impl();
    Pipe->State.Addr = Pipe->Server;
    Pipe->State.Client = Pipe;
    Pipe->Link.State = &Pipe->State;
    Pipe->bConnecting = true;
    Pipe->bConnected = false;
    Pipe->ConnectSent = 0;
    return true;
}

void NetClient::Send(void const* Data, unsigned int Size)
{
    if (!Pipe->bConnected || Data == nullptr || Size == 0)
        return;
    int const Lane = NetLaneForPacket(static_cast<unsigned char const*>(Data), Size);
    if (Lane == kLanePose)
        SendPose(Pipe->Socket, Pipe->State, static_cast<unsigned char const*>(Data), Size);
    else
        QueueReliable(Pipe->Socket, Pipe->State, static_cast<unsigned char const*>(Data), Size);
}

void NetClient::Close()
{
    if (Pipe->Socket != INVALID_SOCKET)
    {
        if (Pipe->bConnected)
        {
            Datagram Msg;
            Msg.Kind = kKindDisconnect;
            SendDatagram(Pipe->Socket, Pipe->Server, Msg);
        }
        closesocket(Pipe->Socket);
        Pipe->Socket = INVALID_SOCKET;
    }
    Pipe->bConnecting = false;
    Pipe->bConnected = false;
}

void NetClient::Dispatch()
{
    if (Pipe->Socket == INVALID_SOCKET)
        return;
    DWORD const Now = GetTickCount();
    if (Pipe->bConnecting && !Pipe->bConnected && Now - Pipe->ConnectSent >= 200)
    {
        Datagram Hello;
        Hello.Kind = kKindConnect;
        SendDatagram(Pipe->Socket, Pipe->Server, Hello);
        Pipe->ConnectSent = Now;
    }
    for (;;)
    {
        unsigned char Raw[12 + kMaxPayload];
        sockaddr_in From = {};
        int FromLen = sizeof(From);
        int const Got = recvfrom(Pipe->Socket, reinterpret_cast<char*>(Raw), sizeof(Raw), 0,
            reinterpret_cast<sockaddr*>(&From), &FromLen);
        if (Got == SOCKET_ERROR || Got <= 0)
            break;
        Datagram Msg;
        if (!Decode(Raw, Got, Msg))
            continue;
        if (!Pipe->bConnected)
        {
            Pipe->bConnected = true;
            Pipe->bConnecting = false;
            if (Pipe->Handler.OnConnect != nullptr)
                Pipe->Handler.OnConnect(0, Pipe->Handler.User);
        }
        if (Msg.Kind == kKindAck || Msg.Kind == kKindData)
            ApplyAck(Pipe->State, Msg.Ack, Msg.AckBits);
        if (Msg.Kind == kKindDisconnect)
        {
            Pipe->bConnected = false;
            if (Pipe->Handler.OnDisconnect != nullptr)
                Pipe->Handler.OnDisconnect(Pipe->Handler.User);
            continue;
        }
        if (Msg.Kind != kKindData || Msg.PayloadLen == 0)
            continue;
        if (Msg.Lane == kLanePose)
        {
            if (!Pipe->State.bHavePose || Newer(Msg.Seq, Pipe->State.LastPose))
            {
                Pipe->State.bHavePose = true;
                Pipe->State.LastPose = Msg.Seq;
                if (Pipe->Handler.OnReceive != nullptr)
                    Pipe->Handler.OnReceive(Msg.Payload, Msg.PayloadLen, Pipe->Handler.User);
            }
            continue;
        }
        DeliverReliable(Pipe->State, Msg,
            [](NetLink*, unsigned char* Data, unsigned int Size, void* User) {
                NetClient::Impl* Self = static_cast<NetClient::Impl*>(User);
                if (Self->Handler.OnReceive != nullptr)
                    Self->Handler.OnReceive(Data, Size, Self->Handler.User);
            },
            &Pipe->Link, Pipe, Pipe->Socket);
    }
    if (Pipe->bConnected)
        Retransmit(Pipe->Socket, Pipe->State);
}
