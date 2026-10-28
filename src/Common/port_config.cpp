// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

// Port-only: port.ini (see port_config.h). Not in retail.

#include "port_config.h"

#if defined(FREELANCER_ADOXA) || defined(FREELANCER_MOD_PLUGINS) || defined(FREELANCER_LANGUAGE) || defined(FREELANCER_EQUIPMENT_SLOTS) || defined(FREELANCER_PLAYER_AUTO_TURRETS)

#include <cstdlib>
#include <cstring>
#include <mutex>
#include <string>
#include <unordered_map>
#include <windows.h>

namespace
{
    char G_ExeDirectory[MAX_PATH] = {};
    char G_IniPath[MAX_PATH] = {};

    // GetPrivateProfileString re-opens and parses port.ini on every call, and render code
    // asks for keys every frame. Raw values are cached per section/key; the file's write time
    // is checked at most once a second so edits made while the game runs still apply.
    struct FPortValue
    {
        bool bPresent;
        std::string Text;
    };
    std::mutex G_CacheLock;
    std::unordered_map<std::string, FPortValue> G_Cache;
    FILETIME G_CacheWriteTime = {};
    DWORD G_CacheCheckedAt = 0;
    bool G_bCacheChecked = false;

    void RefreshCacheLocked()
    {
        DWORD const Now = GetTickCount();
        if (G_bCacheChecked && Now - G_CacheCheckedAt < 1000)
            return;
        G_bCacheChecked = true;
        G_CacheCheckedAt = Now;
        WIN32_FILE_ATTRIBUTE_DATA Data = {};
        FILETIME WriteTime = {};
        if (GetFileAttributesExA(G_IniPath, GetFileExInfoStandard, &Data))
            WriteTime = Data.ftLastWriteTime;
        if (CompareFileTime(&WriteTime, &G_CacheWriteTime) != 0)
        {
            G_Cache.clear();
            G_CacheWriteTime = WriteTime;
        }
    }
    char G_Language[32] = {};
    char G_Voice[32] = {};
    char G_Difficulty[16] = {};
    bool G_bInitialised = false;

    void LowerCase(char* Text)
    {
        for (; *Text != '\0'; ++Text)
            if (*Text >= 'A' && *Text <= 'Z')
                *Text = static_cast<char>(*Text - 'A' + 'a');
    }

    // "-name:value", "-name=value" or "-name value" in the command line into Out (kept when absent).
    void ReadSwitch(char const* CommandLine, char const* Name, char* Out, unsigned OutSize)
    {
        char const* Switch = std::strstr(CommandLine, Name);
        if (Switch == nullptr)
            return;
        Switch += std::strlen(Name);
        if (*Switch == ':' || *Switch == '=' || *Switch == ' ')
            ++Switch;
        while (*Switch == ' ')
            ++Switch;
        unsigned Length = 0;
        while (Switch[Length] != '\0' && Switch[Length] != ' ' && Switch[Length] != '"' && Length + 1 < OutSize)
        {
            Out[Length] = Switch[Length];
            ++Length;
        }
        if (Length != 0)
            Out[Length] = '\0';
    }

    void Initialise()
    {
        if (G_bInitialised)
            return;
        G_bInitialised = true;

        DWORD const Length = GetModuleFileNameA(nullptr, G_ExeDirectory, MAX_PATH);
        if (Length == 0 || Length >= MAX_PATH)
            G_ExeDirectory[0] = '\0';
        else if (char* const Slash = std::strrchr(G_ExeDirectory, '\\'))
            Slash[1] = '\0';
        std::strcpy(G_IniPath, G_ExeDirectory);
        std::strncat(G_IniPath, "port.ini", MAX_PATH - std::strlen(G_IniPath) - 1);

        GetPrivateProfileStringA("Language", "language", "", G_Language, sizeof(G_Language), G_IniPath);
        GetPrivateProfileStringA("Language", "voice", "", G_Voice, sizeof(G_Voice), G_IniPath);
        GetPrivateProfileStringA("Language", "difficulty", "normal", G_Difficulty, sizeof(G_Difficulty), G_IniPath);

        // -lang:xx / -voice:xx / -difficulty:xx on the command line override the file.
        char const* const CommandLine = GetCommandLineA();
        ReadSwitch(CommandLine, "-lang", G_Language, sizeof(G_Language));
        ReadSwitch(CommandLine, "-voice", G_Voice, sizeof(G_Voice));
        ReadSwitch(CommandLine, "-difficulty", G_Difficulty, sizeof(G_Difficulty));
        LowerCase(G_Language);
        LowerCase(G_Voice);
        LowerCase(G_Difficulty);
        // The voice-over language follows the interface language unless it is set separately.
        if (G_Voice[0] == '\0')
            std::strcpy(G_Voice, G_Language);
    }
}

bool __cdecl PortPluginEnabled(char const* Name)
{
    return PortConfigInt("Plugins", Name, 0) != 0;
}

int __cdecl PortConfigInt(char const* Section, char const* Key, int Default)
{
    char Text[64];
    if (PortConfigString(Section, Key, "", Text, sizeof(Text)) == 0)
        return Default;
    if (_stricmp(Text, "true") == 0 || _stricmp(Text, "yes") == 0 || _stricmp(Text, "on") == 0)
        return 1;
    if (_stricmp(Text, "false") == 0 || _stricmp(Text, "no") == 0 || _stricmp(Text, "off") == 0)
        return 0;
    return static_cast<int>(std::strtol(Text, nullptr, 0));
}

float __cdecl PortConfigFloat(char const* Section, char const* Key, float Default)
{
    char Text[64];
    if (PortConfigString(Section, Key, "", Text, sizeof(Text)) == 0)
        return Default;
    return static_cast<float>(std::atof(Text));
}

unsigned __cdecl PortConfigString(char const* Section, char const* Key, char const* Default, char* Out,
                                  unsigned OutSize)
{
    Initialise();
    if (Out == nullptr || OutSize == 0)
        return 0;
    if (Default == nullptr)
        Default = "";
    char const* Source = Default;
    std::string Cached;
    {
        std::string Name = Section != nullptr ? Section : "";
        Name += '\n';
        Name += Key != nullptr ? Key : "";
        for (char& Char : Name)
            if (Char >= 'A' && Char <= 'Z')
                Char = static_cast<char>(Char - 'A' + 'a');
        std::lock_guard<std::mutex> Lock(G_CacheLock);
        RefreshCacheLocked();
        auto Found = G_Cache.find(Name);
        if (Found == G_Cache.end())
        {
            // A sentinel default tells a missing key from an empty value.
            char Raw[1024];
            GetPrivateProfileStringA(Section, Key, "\x01", Raw, sizeof(Raw), G_IniPath);
            FPortValue Value;
            Value.bPresent = std::strcmp(Raw, "\x01") != 0;
            if (Value.bPresent)
                Value.Text = Raw;
            Found = G_Cache.emplace(std::move(Name), std::move(Value)).first;
        }
        if (Found->second.bPresent)
        {
            Cached = Found->second.Text;
            Source = Cached.c_str();
        }
    }
    std::strncpy(Out, Source, OutSize - 1);
    Out[OutSize - 1] = '\0';
    DWORD Length = static_cast<DWORD>(std::strlen(Out));
    // GetPrivateProfileString keeps an inline "; comment"; cut it and the blanks before it.
    if (char* const Comment = std::strchr(Out, ';'))
    {
        *Comment = '\0';
        Length = static_cast<DWORD>(Comment - Out);
    }
    while (Length != 0 && (Out[Length - 1] == ' ' || Out[Length - 1] == '\t'))
        Out[--Length] = '\0';
    return Length;
}

char const* __cdecl PortLanguage()
{
    Initialise();
    return G_Language;
}

unsigned __cdecl PortLanguageString(char const* Key, char const* Default, char* Out, unsigned OutSize)
{
    Initialise();
    if (G_Language[0] == '\0')
    {
        if (Out == nullptr || OutSize == 0)
            return 0;
        std::strncpy(Out, Default != nullptr ? Default : "", OutSize - 1);
        Out[OutSize - 1] = '\0';
        return static_cast<unsigned>(std::strlen(Out));
    }
    char Section[48] = "Language.";
    std::strncat(Section, G_Language, sizeof(Section) - std::strlen(Section) - 1);
    return PortConfigString(Section, Key, Default != nullptr ? Default : "", Out, OutSize);
}

char const* __cdecl PortVoice()
{
    Initialise();
    return G_Voice;
}

char const* __cdecl PortDifficulty()
{
    Initialise();
    return G_Difficulty;
}

unsigned __cdecl PortVoiceString(char const* Key, char const* Default, char* Out, unsigned OutSize)
{
    Initialise();
    if (G_Voice[0] == '\0')
    {
        if (Out == nullptr || OutSize == 0)
            return 0;
        std::strncpy(Out, Default != nullptr ? Default : "", OutSize - 1);
        Out[OutSize - 1] = '\0';
        return static_cast<unsigned>(std::strlen(Out));
    }
    char Section[48] = "Voice.";
    std::strncat(Section, G_Voice, sizeof(Section) - std::strlen(Section) - 1);
    return PortConfigString(Section, Key, Default != nullptr ? Default : "", Out, OutSize);
}

char const* __cdecl PortExeDirectory()
{
    Initialise();
    return G_ExeDirectory;
}

#endif
