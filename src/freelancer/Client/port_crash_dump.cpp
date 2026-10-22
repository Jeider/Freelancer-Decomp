#include "port_crash_dump.h"

#include "port_config.h"

#include <dbghelp.h>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <algorithm>

namespace PortCrashDump
{
namespace
{
typedef BOOL(WINAPI* FMiniDumpWriteDump)(HANDLE, DWORD, HANDLE, MINIDUMP_TYPE, PMINIDUMP_EXCEPTION_INFORMATION,
                                         PMINIDUMP_USER_STREAM_INFORMATION, PMINIDUMP_CALLBACK_INFORMATION);
typedef BOOL(WINAPI* FSymInitialize)(HANDLE, PCSTR, BOOL);
typedef DWORD(WINAPI* FSymSetOptions)(DWORD);
typedef BOOL(WINAPI* FStackWalk64)(DWORD, HANDLE, HANDLE, LPSTACKFRAME64, PVOID, PREAD_PROCESS_MEMORY_ROUTINE64,
                                    PFUNCTION_TABLE_ACCESS_ROUTINE64, PGET_MODULE_BASE_ROUTINE64,
                                    PTRANSLATE_ADDRESS_ROUTINE64);
typedef BOOL(WINAPI* FSymFromAddr)(HANDLE, DWORD64, PDWORD64, PSYMBOL_INFO);
typedef BOOL(WINAPI* FSymGetLineFromAddr64)(HANDLE, DWORD64, PDWORD, PIMAGEHLP_LINE64);

bool GbEnabled = false;
bool GbWriting = false;
int GKeep = 5;
char GDirectory[MAX_PATH] = {};
HMODULE GDbgHelp = nullptr;
FMiniDumpWriteDump GMiniDumpWriteDump = nullptr;
FSymInitialize GSymInitialize = nullptr;
FSymSetOptions GSymSetOptions = nullptr;
FStackWalk64 GStackWalk64 = nullptr;
FSymFromAddr GSymFromAddr = nullptr;
FSymGetLineFromAddr64 GSymGetLineFromAddr64 = nullptr;
PFUNCTION_TABLE_ACCESS_ROUTINE64 GSymFunctionTableAccess64 = nullptr;
PGET_MODULE_BASE_ROUTINE64 GSymGetModuleBase64 = nullptr;

// "Common.dll+2a101" for an address inside a module.
void ModuleOffset(DWORD64 Address, char* Out, size_t Size)
{
    HMODULE Module = nullptr;
    char Path[MAX_PATH] = "?";
    if (GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                           (LPCSTR)(uintptr_t)Address, &Module) &&
        Module != nullptr)
        GetModuleFileNameA(Module, Path, MAX_PATH);
    const char* Name = strrchr(Path, '\\');
    Name = Name != nullptr ? Name + 1 : Path;
    _snprintf(Out, Size, "%s+%llx", Name, (unsigned long long)(Address - (DWORD64)(uintptr_t)Module));
    Out[Size - 1] = 0;
}

void Describe(FILE* File, HANDLE Process, DWORD64 Address)
{
    char Where[MAX_PATH + 32];
    ModuleOffset(Address, Where, sizeof(Where));
    fprintf(File, "  %08llx  %s", (unsigned long long)Address, Where);
    if (GSymFromAddr != nullptr)
    {
        unsigned char Buffer[sizeof(SYMBOL_INFO) + 512] = {};
        SYMBOL_INFO* Symbol = (SYMBOL_INFO*)Buffer;
        Symbol->SizeOfStruct = sizeof(SYMBOL_INFO);
        Symbol->MaxNameLen = 511;
        DWORD64 Displacement = 0;
        if (GSymFromAddr(Process, Address, &Displacement, Symbol))
            fprintf(File, "  %s+0x%llx", Symbol->Name, (unsigned long long)Displacement);
    }
    if (GSymGetLineFromAddr64 != nullptr)
    {
        IMAGEHLP_LINE64 Line = {};
        Line.SizeOfStruct = sizeof(Line);
        DWORD Displacement = 0;
        if (GSymGetLineFromAddr64(Process, Address, &Displacement, &Line))
            fprintf(File, "  %s:%lu", Line.FileName, Line.LineNumber);
    }
    fputc('\n', File);
}

// Keeps the newest Keep-1 dumps (the one about to be written makes Keep).
void PruneOld()
{
    std::vector<std::string> Names;
    WIN32_FIND_DATAA Found;
    const std::string Pattern = std::string(GDirectory) + "\\freelancer_*.dmp";
    HANDLE Find = FindFirstFileA(Pattern.c_str(), &Found);
    if (Find == INVALID_HANDLE_VALUE)
        return;
    do
        Names.push_back(Found.cFileName);
    while (FindNextFileA(Find, &Found));
    FindClose(Find);
    std::sort(Names.begin(), Names.end()); // the names sort by date and time
    for (size_t I = 0; I + (size_t)(std::max)(GKeep - 1, 0) < Names.size(); ++I)
    {
        const std::string Base = std::string(GDirectory) + "\\" + Names[I];
        DeleteFileA(Base.c_str());
        DeleteFileA((Base.substr(0, Base.size() - 4) + ".txt").c_str());
    }
}
} // namespace

void Initialize()
{
    GbEnabled = PortConfigInt("Debug", "crash_dumps", 1) != 0;
    GKeep = (std::max)(1, PortConfigInt("Debug", "crash_dumps_keep", 5));
    if (!GbEnabled)
        return;
    // <game>\CRASHDUMPS, next to EXE.
    char Module[MAX_PATH] = {};
    GetModuleFileNameA(nullptr, Module, MAX_PATH);
    char* Slash = strrchr(Module, '\\');
    if (Slash == nullptr)
    {
        GbEnabled = false;
        return;
    }
    *Slash = 0;
    Slash = strrchr(Module, '\\');
    if (Slash != nullptr)
        *Slash = 0;
    _snprintf(GDirectory, sizeof(GDirectory), "%s\\CRASHDUMPS", Module);
    GDirectory[sizeof(GDirectory) - 1] = 0;

    GDbgHelp = LoadLibraryA("dbghelp.dll");
    if (GDbgHelp == nullptr)
    {
        GbEnabled = false;
        return;
    }
    GMiniDumpWriteDump = (FMiniDumpWriteDump)GetProcAddress(GDbgHelp, "MiniDumpWriteDump");
    GSymInitialize = (FSymInitialize)GetProcAddress(GDbgHelp, "SymInitialize");
    GSymSetOptions = (FSymSetOptions)GetProcAddress(GDbgHelp, "SymSetOptions");
    GStackWalk64 = (FStackWalk64)GetProcAddress(GDbgHelp, "StackWalk64");
    GSymFromAddr = (FSymFromAddr)GetProcAddress(GDbgHelp, "SymFromAddr");
    GSymGetLineFromAddr64 = (FSymGetLineFromAddr64)GetProcAddress(GDbgHelp, "SymGetLineFromAddr64");
    GSymFunctionTableAccess64 = (PFUNCTION_TABLE_ACCESS_ROUTINE64)GetProcAddress(GDbgHelp, "SymFunctionTableAccess64");
    GSymGetModuleBase64 = (PGET_MODULE_BASE_ROUTINE64)GetProcAddress(GDbgHelp, "SymGetModuleBase64");
    if (GMiniDumpWriteDump == nullptr)
        GbEnabled = false;
}

namespace
{
void WriteFiles(EXCEPTION_POINTERS* Info)
{
    {
        CreateDirectoryA(GDirectory, nullptr);
        PruneOld();
        SYSTEMTIME Now;
        GetLocalTime(&Now);
        char Base[MAX_PATH];
        _snprintf(Base, sizeof(Base), "%s\\freelancer_%04u-%02u-%02u_%02u-%02u-%02u", GDirectory, Now.wYear,
                  Now.wMonth, Now.wDay, Now.wHour, Now.wMinute, Now.wSecond);
        Base[sizeof(Base) - 1] = 0;
        const HANDLE Process = GetCurrentProcess();

        // The dump: heap and stacks, enough to inspect any object; the file is a few hundred MB.
        const std::string DumpPath = std::string(Base) + ".dmp";
        HANDLE DumpFile = CreateFileA(DumpPath.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS,
                                      FILE_ATTRIBUTE_NORMAL, nullptr);
        bool bDumped = false;
        if (DumpFile != INVALID_HANDLE_VALUE)
        {
            MINIDUMP_EXCEPTION_INFORMATION Exception;
            Exception.ThreadId = GetCurrentThreadId();
            Exception.ExceptionPointers = Info;
            Exception.ClientPointers = FALSE;
            const MINIDUMP_TYPE Type = (MINIDUMP_TYPE)(MiniDumpWithPrivateReadWriteMemory | MiniDumpWithDataSegs |
                                                       MiniDumpWithHandleData | MiniDumpWithThreadInfo |
                                                       MiniDumpWithUnloadedModules |
                                                       MiniDumpWithIndirectlyReferencedMemory);
            bDumped = GMiniDumpWriteDump(Process, GetCurrentProcessId(), DumpFile, Type, &Exception, nullptr,
                                         nullptr) != FALSE;
            CloseHandle(DumpFile);
        }

        // The report: readable without a debugger.
        FILE* File = fopen((std::string(Base) + ".txt").c_str(), "w");
        if (File != nullptr)
        {
            const EXCEPTION_RECORD* Record = Info->ExceptionRecord;
            const CONTEXT* Context = Info->ContextRecord;
            fprintf(File, "Freelancer crash %04u-%02u-%02u %02u:%02u:%02u, thread %lu\n", Now.wYear, Now.wMonth,
                    Now.wDay, Now.wHour, Now.wMinute, Now.wSecond, GetCurrentThreadId());
            fprintf(File, "exception %08lx at %p", Record->ExceptionCode, Record->ExceptionAddress);
            if (Record->ExceptionCode == EXCEPTION_ACCESS_VIOLATION && Record->NumberParameters >= 2)
                fprintf(File, ", %s of %08lx",
                        Record->ExceptionInformation[0] == 0 ? "read" :
                        (Record->ExceptionInformation[0] == 1 ? "write" : "execute"),
                        (unsigned long)Record->ExceptionInformation[1]);
            fprintf(File, "\ndump: %s\n\n", bDumped ? DumpPath.c_str() : "(failed)");
            fprintf(File, "eax=%08lx ebx=%08lx ecx=%08lx edx=%08lx esi=%08lx edi=%08lx\n", Context->Eax,
                    Context->Ebx, Context->Ecx, Context->Edx, Context->Esi, Context->Edi);
            fprintf(File, "eip=%08lx esp=%08lx ebp=%08lx efl=%08lx\n\ncall stack:\n", Context->Eip, Context->Esp,
                    Context->Ebp, Context->EFlags);
            fflush(File);

            // Symbols from the pdbs next to the modules (bin\).
            if (GSymInitialize != nullptr && GStackWalk64 != nullptr)
            {
                if (GSymSetOptions != nullptr)
                    GSymSetOptions(SYMOPT_UNDNAME | SYMOPT_LOAD_LINES | SYMOPT_DEFERRED_LOADS | SYMOPT_FAIL_CRITICAL_ERRORS);
                GSymInitialize(Process, nullptr, TRUE);
                CONTEXT Walk = *Context;
                STACKFRAME64 Frame = {};
                Frame.AddrPC.Offset = Walk.Eip;
                Frame.AddrPC.Mode = AddrModeFlat;
                Frame.AddrFrame.Offset = Walk.Ebp;
                Frame.AddrFrame.Mode = AddrModeFlat;
                Frame.AddrStack.Offset = Walk.Esp;
                Frame.AddrStack.Mode = AddrModeFlat;
                for (int Depth = 0; Depth < 64; ++Depth)
                {
                    if (!GStackWalk64(IMAGE_FILE_MACHINE_I386, Process, GetCurrentThread(), &Frame, &Walk, nullptr,
                                      GSymFunctionTableAccess64, GSymGetModuleBase64, nullptr) ||
                        Frame.AddrPC.Offset == 0)
                        break;
                    Describe(File, Process, Frame.AddrPC.Offset);
                    fflush(File);
                }
            }
            fclose(File);
        }
    }
}

int Guarded(EXCEPTION_POINTERS* Info)
{
    __try
    {
        WriteFiles(Info);
    }
    __except (EXCEPTION_EXECUTE_HANDLER)
    {
        return 0;
    }
    return 1;
}
} // namespace

void Write(EXCEPTION_POINTERS* Info)
{
    if (!GbEnabled || GbWriting || Info == nullptr)
        return;
    GbWriting = true; // a crash inside the writer must not recurse
    Guarded(Info);
    GbWriting = false;
}
} // namespace PortCrashDump
