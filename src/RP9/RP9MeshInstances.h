#pragma once
#include <d3d9.h>

// Shared with the D3D9 render check. No game-side object is created for an instance.
struct FRp9MeshInstances
{
    IDirect3DVertexDeclaration9* Declaration = nullptr;
    IDirect3DIndexBuffer9* Indices = nullptr;
    void Release()
    {
        if (Declaration) { Declaration->Release(); Declaration = nullptr; }
        if (Indices) { Indices->Release(); Indices = nullptr; }
    }
    HRESULT Draw(IDirect3DDevice9* Device, IDirect3DVertexBuffer9* Geometry,
                 IDirect3DVertexBuffer9* Instances, UINT Vertices, UINT First, UINT Count)
    {
        if (!Geometry || !Instances || !Vertices || Vertices > 65535 || Vertices % 3 || !Count ||
            Count >= D3DSTREAMSOURCE_INDEXEDDATA || First > 0xffffffffu / 36)
            return D3DERR_INVALIDCALL;
        HRESULT Hr = S_OK;
        if (!Declaration)
        {
            D3DVERTEXELEMENT9 const Elements[] = {
                {0, 0, D3DDECLTYPE_FLOAT3, 0, D3DDECLUSAGE_POSITION, 0},
                {0, 12, D3DDECLTYPE_FLOAT3, 0, D3DDECLUSAGE_NORMAL, 0},
                {0, 24, D3DDECLTYPE_FLOAT2, 0, D3DDECLUSAGE_TEXCOORD, 0},
                {1, 0, D3DDECLTYPE_FLOAT4, 0, D3DDECLUSAGE_TEXCOORD, 1},
                {1, 16, D3DDECLTYPE_FLOAT4, 0, D3DDECLUSAGE_TEXCOORD, 2},
                {1, 32, D3DDECLTYPE_D3DCOLOR, 0, D3DDECLUSAGE_COLOR, 0}, D3DDECL_END()};
            Hr = Device->CreateVertexDeclaration(Elements, &Declaration);
        }
        if (SUCCEEDED(Hr) && !Indices)
        {
            Hr = Device->CreateIndexBuffer(65535 * 2, D3DUSAGE_WRITEONLY, D3DFMT_INDEX16,
                                           D3DPOOL_MANAGED, &Indices, nullptr);
            if (SUCCEEDED(Hr))
            {
                void* Data = nullptr;
                Hr = Indices->Lock(0, 0, &Data, 0);
                if (SUCCEEDED(Hr))
                {
                    for (unsigned I = 0; I < 65535; ++I) static_cast<unsigned short*>(Data)[I] = (unsigned short)I;
                    Hr = Indices->Unlock();
                }
                if (FAILED(Hr)) { Indices->Release(); Indices = nullptr; }
            }
        }
        if (SUCCEEDED(Hr)) Hr = Device->SetVertexDeclaration(Declaration);
        if (SUCCEEDED(Hr)) Hr = Device->SetIndices(Indices);
        if (SUCCEEDED(Hr)) Hr = Device->SetStreamSource(0, Geometry, 0, 32);
        if (SUCCEEDED(Hr)) Hr = Device->SetStreamSource(1, Instances, First * 36, 36);
        if (SUCCEEDED(Hr)) Hr = Device->SetStreamSourceFreq(0, D3DSTREAMSOURCE_INDEXEDDATA | Count);
        if (SUCCEEDED(Hr)) Hr = Device->SetStreamSourceFreq(1, D3DSTREAMSOURCE_INSTANCEDATA | 1);
        if (SUCCEEDED(Hr)) Hr = Device->DrawIndexedPrimitive(D3DPT_TRIANGLELIST, 0, 0, Vertices, 0, Vertices / 3);
        // These are device states, not part of the vertex declaration. Always undo instancing.
        Device->SetStreamSourceFreq(0, 1); Device->SetStreamSourceFreq(1, 1);
        Device->SetStreamSource(0, nullptr, 0, 0); Device->SetStreamSource(1, nullptr, 0, 0);
        Device->SetIndices(nullptr);
        return Hr;
    }
};
