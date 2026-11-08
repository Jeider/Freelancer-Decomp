#include <windows.h>

extern "C" __declspec(dllexport) int __cdecl EBUEula(char const* /*RegKey*/, char* /*EulaFile*/,
                                                     char* /*WarrantyFile*/, int /*Arg4*/)
{
    return 1;
}
