#pragma once

#include <vector>

class NetLink;
class NetHost;
class NetClient;

int NetLaneForPacket(unsigned char const* Data, unsigned int Size);

class NetLink
{
public:
    void Send(void const* Data, unsigned int Size);
    void Disconnect();
    double GetLinkSaturation() const;
    unsigned int GetSendQBytes() const;
    unsigned int GetSendQSize() const;

    unsigned int Slot = 0;
    struct Impl;
    Impl* State = nullptr;
};

struct NetHostHandler
{
    void (*OnConnect)(NetLink* Link, void* User);
    void (*OnReceive)(NetLink* Link, unsigned char* Data, unsigned int Size, void* User);
    void (*OnDisconnect)(NetLink* Link, void* User);
    void* User;
};

class NetHost
{
public:
    NetHost();
    ~NetHost();

    bool BeginHosting(unsigned int Port);
    void Dispatch();
    void Shutdown();

    void SetHandler(NetHostHandler Handler);
    void SetSessionName(wchar_t const* Name);
    void SetPassword(wchar_t const* Password);
    void SetMaxPlayers(int MaxPlayers);
    void SetEnumResponse(void* Data, unsigned long Size);
    void GetPort(std::vector<unsigned long>& Ports);
    NetLink* Find(unsigned int Slot) const;
    void Drop(unsigned int Slot);

    struct Impl;
    Impl* Pipe;
};

struct NetClientHandler
{
    void (*OnConnect)(long Result, void* User);
    void (*OnReceive)(unsigned char* Data, unsigned int Size, void* User);
    void (*OnDisconnect)(void* User);
    void* User;
};

class NetClient
{
public:
    NetClient();
    ~NetClient();

    void SetHandler(NetClientHandler Handler);
    bool Connect(char const* Host, unsigned short Port);
    void Send(void const* Data, unsigned int Size);
    void Dispatch();
    void Close();

    struct Impl;
    Impl* Pipe;
};
