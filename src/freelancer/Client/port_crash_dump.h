#pragma once

#include <windows.h>

// Port-only crash dumps. On an unhandled exception the client writes, into <game>\CRASHDUMPS:
//   freelancer_<date>_<time>.dmp  a minidump with the heap (private read/write memory), threads
//                                 and modules, readable by Visual Studio or WinDbg;
//   freelancer_<date>_<time>.txt  the exception, the registers and the faulting thread's call
//                                 stack resolved against the pdbs next to the modules.
// port.ini [Debug] crash_dumps = 0 turns it off; crash_dumps_keep (default 5) limits how many
// dumps are kept (the oldest go first).
// Hangs too: a watchdog thread writes the same pair (exception E0000001 "hang", the main thread's
// stack) when the main thread has not finished a frame for [Debug] hang_dump_seconds (default
// 30; 0 = off), once per stall.
namespace PortCrashDump
{
    // Reads the settings and loads dbghelp while the process is healthy. Call on the main thread.
    void Initialize();
    // Called first thing in the unhandled-exception filter; never throws. True when the pair
    // was written (the filter then ends the process instead of waiting on Dr. Watson).
    bool Write(EXCEPTION_POINTERS* Info);
    // Once per client frame, on the main thread: the hang watchdog's heartbeat.
    void Heartbeat();
}
