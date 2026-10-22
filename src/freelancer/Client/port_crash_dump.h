#pragma once

#include <windows.h>

// Port-only crash dumps. On an unhandled exception the client writes, into <game>\CRASHDUMPS:
//   freelancer_<date>_<time>.dmp  a minidump with the heap (private read/write memory), threads
//                                 and modules, readable by Visual Studio or WinDbg;
//   freelancer_<date>_<time>.txt  the exception, the registers and the faulting thread's call
//                                 stack resolved against the pdbs next to the modules.
// port.ini [Debug] crash_dumps = 0 turns it off; crash_dumps_keep (default 5) limits how many
// dumps are kept (the oldest go first).
namespace PortCrashDump
{
    // Reads the settings and loads dbghelp while the process is healthy.
    void Initialize();
    // Called first thing in the unhandled-exception filter; never throws.
    void Write(EXCEPTION_POINTERS* Info);
}
