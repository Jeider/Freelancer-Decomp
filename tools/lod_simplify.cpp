// Offline-only wrapper. Build as an x64 DLL for Python's ctypes.
#include "vendor/meshoptimizer/meshoptimizer.h"
extern "C" __declspec(dllexport) size_t simplify_lod(unsigned int* out,
    const unsigned int* indices, size_t count, const float* vertices,
    size_t vertex_count, const unsigned char* locks, size_t target, float error,
    float* result_error)
{
    // UV continuity takes priority over reduction. Never use permissive seam
    // collapses: they can connect unrelated atlas islands through a new face.
    const float weights[]={0.05f,0.05f,0.05f,1.0f,1.0f,10.0f};
    size_t n=meshopt_simplifyWithAttributes(out,indices,count,vertices,vertex_count,36,
        vertices+3,36,weights,6,locks,target,error,meshopt_SimplifyLockBorder,result_error);
    meshopt_optimizeVertexCache(out,out,n,vertex_count);
    return n;
}
