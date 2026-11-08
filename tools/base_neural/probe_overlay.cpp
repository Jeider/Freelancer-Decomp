// Test-only add-on; never installed. Checks pixels AFTER ReShade has drawn its GUI.
#include <reshade.hpp>
#include <vector>
#include <cstdio>
static unsigned frames=0;
static void Check(reshade::api::effect_runtime* runtime)
{
    if(frames>=20)return;
    uint32_t width=0,height=0;runtime->get_screenshot_width_and_height(&width,&height);
    std::vector<unsigned char> pixels(static_cast<size_t>(width)*height*4);
    if(!runtime->capture_screenshot(pixels.data())){puts("FAIL overlay capture");fflush(stdout);ExitProcess(41);}
    // probe_wrapper's first frames are a uniform red ramp with G=127, B=241.
    // The stock startup banner overwrites these pixels during those first frames.
    for(size_t i=0;i<pixels.size();i+=4)
        if(pixels[i+1]!=127||pixels[i+2]!=241)
        {printf("FAIL overlay changed pixel %zu on startup frame %u\n",i/4,frames);fflush(stdout);ExitProcess(42);}
    if(++frames==20){puts("PASS first 20 presented frames contain no ReShade banner/overlay pixels");fflush(stdout);}
}
extern "C" __declspec(dllexport) char const* NAME="Base Neural overlay pixel test";
BOOL WINAPI DllMain(HMODULE module,DWORD reason,LPVOID)
{
    if(reason==DLL_PROCESS_ATTACH)
    {
        char enabled[2]={};if(!GetEnvironmentVariableA("FL_BASE_NEURAL_VERIFY_UI",enabled,2))return FALSE;
        if(!reshade::register_addon(module))return FALSE;
        reshade::register_event<reshade::addon_event::reshade_present>(Check);
    }
    else if(reason==DLL_PROCESS_DETACH)
    {
        reshade::unregister_event<reshade::addon_event::reshade_present>(Check);
        reshade::unregister_addon(module);
    }
    return TRUE;
}
