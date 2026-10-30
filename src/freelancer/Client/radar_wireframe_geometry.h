#pragma once
#include "radar_symbols.h"
#include <cstdint>
#include <cstring>
#include <vector>

namespace RadarWireframe
{
    using Vec3 = RadarProjection::Vec3;
    // A private element type avoids instantiating Common.dll's exported STL vector type.
    struct Index
    {
        unsigned short value;
        Index(unsigned short v) : value(v) {}
        operator unsigned short() const { return value; }
    };
    struct Geometry { std::vector<Vec3> vertices; std::vector<Index> indices; };

    template<class T> T Read(void const* data, size_t offset)
    {
        T result;
        std::memcpy(&result, static_cast<unsigned char const*>(data) + offset, sizeof result);
        return result;
    }

    inline unsigned VertexStride(unsigned fvf)
    {
        // VMeshWire points into the model's FVF vertex pool. No triangle fallback.
        if ((fvf & 0x0e) != 2 || ((fvf >> 8) & 15) > 8) return 0;
        unsigned stride = 12 + ((fvf & 0x10) ? 12 : 0) + ((fvf & 0x40) ? 4 : 0) + ((fvf & 0x80) ? 4 : 0);
        unsigned const sizes[] = {8, 12, 16, 4};
        for (unsigned i = 0; i < ((fvf >> 8) & 15); ++i) stride += sizes[(fvf >> (16 + i * 2)) & 3];
        return stride;
    }

    inline size_t MeshBytes(void const* mesh)
    {
        unsigned const stride = VertexStride(Read<unsigned short>(mesh, 12));
        return 16u + 12u * Read<unsigned short>(mesh, 8) + 2u * Read<unsigned short>(mesh, 10)
            + size_t(stride) * Read<unsigned short>(mesh, 14);
    }

    inline bool Decode(void const* mesh, size_t meshBytes, void const* wire, size_t wireBytes, Geometry& out)
    {
        out = {};
        if (!mesh || !wire || meshBytes < 16 || wireBytes < 16 || Read<unsigned>(wire, 0) != 16) return false;
        unsigned const stride = VertexStride(Read<unsigned short>(mesh, 12));
        unsigned const count = Read<unsigned short>(mesh, 14), base = Read<unsigned short>(wire, 8);
        unsigned const indexCount = Read<unsigned short>(wire, 12);
        size_t const vertexStart = 16u + 12u * Read<unsigned short>(mesh, 8) + 2u * Read<unsigned short>(mesh, 10);
        if (!stride || !indexCount || (indexCount & 1) || vertexStart + size_t(count) * stride > meshBytes ||
            16u + 2u * indexCount > wireBytes) return false;
        Geometry result;
        std::vector<int> remap(count, -1);
        result.indices.reserve(indexCount);
        for (unsigned i = 0; i < indexCount; ++i)
        {
            unsigned const index = base + Read<unsigned short>(wire, 16 + i * 2);
            if (index >= count) return false;
            if (remap[index] < 0)
            {
                Vec3 const p = Read<Vec3>(mesh, vertexStart + size_t(index) * stride);
                if (!std::isfinite(p.x) || !std::isfinite(p.y) || !std::isfinite(p.z)) return false;
                remap[index] = static_cast<int>(result.vertices.size());
                result.vertices.push_back(p);
            }
            result.indices.push_back(static_cast<unsigned short>(remap[index]));
        }
        out = std::move(result);
        return true;
    }

    struct Point { float x, y; };
    inline bool ClipToDish(RadarProjection::Layout const& layout, float& ax, float& ay, float& bx, float& by)
    {
        double const rx = layout.radius, ry = layout.radius * layout.ellipse;
        if (!std::isfinite(rx) || !std::isfinite(ry) || rx <= 0 || ry <= 0 ||
            !RadarSymbols::Clip(layout, ax, ay, bx, by)) return false;
        // Normalize the saucer ellipse to a unit circle. Clip the segment itself,
        // so a model need not fit entirely inside the dish to remain visible.
        double const x = (double(ax) - layout.x) / rx, y = (double(ay) - layout.y) / ry;
        double const dx = (double(bx) - ax) / rx, dy = (double(by) - ay) / ry;
        double const a = dx*dx + dy*dy, b = x*dx + y*dy, c = x*x + y*y - 1;
        if (a == 0) return c <= 0;
        double const discriminant = b*b - a*c;
        if (discriminant < 0) return false;
        double const root = std::sqrt(discriminant);
        double const lo = (std::max)(0.0, (-b-root)/a);
        double const hi = (std::min)(1.0, (-b+root)/a);
        if (lo > hi) return false;
        double const sx = double(bx)-ax, sy = double(by)-ay;
        bx = float(ax + hi*sx); by = float(ay + hi*sy);
        ax = float(ax + lo*sx); ay = float(ay + lo*sy);
        return true;
    }

    inline Point Project(Vec3 const& v, float const* model, Vec3 origin, float const rotation[3][3],
                         float range, RadarProjection::Layout const& layout)
    {
        // Each compound part supplies its live world transform, including door animation.
        double const delta[] = {
            double(model[0])*v.x + double(model[1])*v.y + double(model[2])*v.z + model[9] - origin.x,
            double(model[3])*v.x + double(model[4])*v.y + double(model[5])*v.z + model[10] - origin.y,
            double(model[6])*v.x + double(model[7])*v.y + double(model[8])*v.z + model[11] - origin.z};
        double local[3] = {};
        float level[3][3];
        if (layout.topDown) { RadarProjection::LevelRotation(rotation,level); rotation=level; }
        for (int axis = 0; axis < 3; ++axis)
            for (int row = 0; row < 3; ++row) local[axis] += delta[row] * rotation[row][axis];
        double const scale = double(layout.radius) / range;
        return {float(layout.x + local[0]*scale),
                float(layout.y + (local[2]*layout.ellipse - local[1]*layout.elevation)*scale)};
    }

    template<class DrawLine>
    unsigned Emit(Geometry const& geometry, float const* model, Vec3 origin, float const rotation[3][3],
                  float range, RadarProjection::Layout const& layout, unsigned color,
                  std::vector<Point>& scratch, DrawLine draw)
    {
        if (!model || !std::isfinite(range) || range <= 0) return 0;
        scratch.clear();
        for (auto const& v : geometry.vertices) scratch.push_back(Project(v, model, origin, rotation, range, layout));
        unsigned emitted = 0;
        for (size_t i = 0; i + 1 < geometry.indices.size(); i += 2)
        {
            auto a = scratch[geometry.indices[i]], b = scratch[geometry.indices[i+1]];
            // No object-centre/range rejection: a long corridor may cross the entire radar.
            if (ClipToDish(layout, a.x, a.y, b.x, b.y))
            {
                draw(a.x, a.y, b.x, b.y, color, 1.f);
                ++emitted;
            }
        }
        return emitted;
    }
}
