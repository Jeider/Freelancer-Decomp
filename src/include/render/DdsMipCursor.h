#pragma once

// DDS writers may omit dwPitchOrLinearSize for compressed textures (D3DX9 does).
// DXT mip offsets come from the block grid, never that optional header value.
struct FTextureDdsCursor
{
    const unsigned char* Pixels;
    unsigned long Bytes;
    unsigned long MinimumBlock;
    unsigned long Width;
    unsigned long Height;
    bool Compressed=false;

    static unsigned long CompressedBytes(unsigned long Width,unsigned long Height,unsigned long Block)
    {
        return ((Width+3)/4)*((Height+3)/4)*Block;
    }
    void Advance()
    {
        Pixels+=Bytes;
        Width>>=1;Height>>=1;
        if(Compressed) {
            if(!Width)Width=1;
            if(!Height)Height=1;
            Bytes=CompressedBytes(Width,Height,MinimumBlock);
        } else {
            // Retain the retail uncompressed cursor policy.
            Bytes>>=2;
            if(Bytes<MinimumBlock)Bytes=MinimumBlock;
        }
    }
};
