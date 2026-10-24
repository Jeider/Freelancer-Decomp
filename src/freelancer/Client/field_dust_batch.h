#pragma once
#include <algorithm>
#include <cstring>
#include <vector>

namespace FieldDustBatch
{
    constexpr int MaxFields = 4, FieldRegisters = 28, FirstFieldRegister = 8;
    struct Batch
    {
        float Constants[(FirstFieldRegister + MaxFields * FieldRegisters) * 4] = {};
        float Rect[4] = {1.0f, 1.0f, 0.0f, 0.0f};
        int Count = 0;
    };
    // Append visible fields nearest first. Render batches in reverse order; each shader
    // integrates its own fields front to back, then composites over the farther batches.
    inline float* Append(std::vector<Batch>& Batches, float const* Common, float const* Rect)
    {
        if (Batches.empty() || Batches.back().Count == MaxFields)
        {
            Batches.emplace_back();
            std::memcpy(Batches.back().Constants, Common, FirstFieldRegister * 4 * sizeof(float));
        }
        Batch& B = Batches.back();
        B.Rect[0] = (std::min)(B.Rect[0], Rect[0]); B.Rect[1] = (std::min)(B.Rect[1], Rect[1]);
        B.Rect[2] = (std::max)(B.Rect[2], Rect[2]); B.Rect[3] = (std::max)(B.Rect[3], Rect[3]);
        float* Field = &B.Constants[(FirstFieldRegister + B.Count * FieldRegisters) * 4];
        B.Constants[6 * 4] = static_cast<float>(++B.Count);
        return Field;
    }
}
