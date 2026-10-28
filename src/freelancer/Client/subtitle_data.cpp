#include "subtitle_data.h"
#include <windows.h>
#include <xmllite.h>
#include <shlwapi.h>
#include <wrl/client.h>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <cwctype>
#include <stdexcept>
#pragma comment(lib, "xmllite.lib")
#pragma comment(lib, "shlwapi.lib")

namespace NativeSubtitles
{
namespace
{
    std::wstring Trim(std::wstring s)
    {
        auto a = s.find_first_not_of(L" \r\n\t");
        if (a == s.npos) return {};
        return s.substr(a, s.find_last_not_of(L" \r\n\t") - a + 1);
    }
    std::wstring Attr(IXmlReader* r, wchar_t const* name, bool required = true)
    {
        if (r->MoveToAttributeByName(name, nullptr) != S_OK)
        {
            r->MoveToElement();
            if (required) throw std::runtime_error("Missing XML attribute");
            return {};
        }
        wchar_t const* value = nullptr;
        if (FAILED(r->GetValue(&value, nullptr))) throw std::runtime_error("Invalid attribute");
        std::wstring text = value;
        r->MoveToElement();
        return text;
    }
    double Time(std::wstring const& s)
    {
        double total = 0;
        size_t start = 0;
        int count = 0;
        for (;;)
        {
            auto end = s.find(L':', start);
            auto piece = s.substr(start, end == s.npos ? end : end - start);
            wchar_t* tail = nullptr;
            double n = wcstod(piece.c_str(), &tail);
            if (piece.empty() || *tail || !std::isfinite(n) || n < 0 || ++count > 3)
                throw std::runtime_error("Invalid timestamp");
            total = total * 60 + n;
            if (end == s.npos) break;
            start = end + 1;
        }
        if (!std::isfinite(total)) throw std::runtime_error("Timestamp overflow");
        return total;
    }
}

std::wstring AudioKey(std::wstring path)
{
    path = Trim(path);
    for (auto& c : path) c = c == L'\\' ? L'/' : wchar_t(towlower(c));
    auto audio = path.rfind(L"/audio/");
    if (audio != path.npos) path.erase(0, audio + 7);
    else if (path.compare(0, 6, L"audio/") == 0) path.erase(0, 6);
    while (path.compare(0, 2, L"./") == 0) path.erase(0, 2);
    auto bar = path.find(L'|');
    if (bar != path.npos)
    {
        auto suffix = path.substr(bar + 1);
        wchar_t* end = nullptr;
        auto id = wcstoul(suffix.c_str(), &end, 16);
        if (suffix.empty() || *end || suffix.size() > 10)
            throw std::runtime_error("Invalid UTF audio ID");
        wchar_t hex[16];
        swprintf_s(hex, L"|0x%08lx", id);
        path.resize(bar);
        path += hex;
    }
    return path;
}

std::wstring Entry::At(double seconds) const
{
    if (seconds < 0 || !std::isfinite(seconds)) return {};
    if (parts.empty()) return text;
    std::wstring result;
    for (auto const& p : parts)
        if (seconds >= p.start && seconds < p.end)
        {
            if (!result.empty()) result += L'\n';
            result += p.text;
        }
    return result;
}

void Playback::Sync(double seconds, bool active, bool paused, float dt)
{
    started = active;
    if (seconds >= 0 && std::isfinite(seconds)) time = seconds;
    else if (active && !paused && std::isfinite(dt) && dt > 0) time += dt;
}

bool ReadXml(wchar_t const* path, Database& result, std::wstring& error)
{
    using Microsoft::WRL::ComPtr;
    ComPtr<IStream> stream;
    ComPtr<IXmlReader> reader;
    Database parsed;
    error.clear();
    try
    {
        if (FAILED(SHCreateStreamOnFileEx(path, STGM_READ | STGM_SHARE_DENY_WRITE,
            FILE_ATTRIBUTE_NORMAL, FALSE, nullptr, &stream))) throw std::runtime_error("Cannot open XML");
        STATSTG stat = {};
        if (FAILED(stream->Stat(&stat, STATFLAG_NONAME)) || stat.cbSize.QuadPart > 32 * 1024 * 1024)
            throw std::runtime_error("XML exceeds 32 MB");
        if (FAILED(CreateXmlReader(__uuidof(IXmlReader), reinterpret_cast<void**>(reader.GetAddressOf()), nullptr)))
            throw std::runtime_error("Cannot create XML reader");
        reader->SetProperty(XmlReaderProperty_DtdProcessing, DtdProcessing_Prohibit);
        reader->SetProperty(XmlReaderProperty_MaxElementDepth, 8);
        if (FAILED(reader->SetInput(stream.Get()))) throw std::runtime_error("Cannot read XML");
        XmlNodeType type;
        HRESULT hr;
        bool root = false, inside = false, dynamic = false, inPart = false;
        Entry entry;
        Part part;
        std::wstring key;
        auto finishEntry = [&]() {
            if (dynamic && entry.parts.empty()) throw std::runtime_error("Empty Dynamic entry");
            entry.text = Trim(entry.text);
            if (!parsed.emplace(key, std::move(entry)).second) throw std::runtime_error("Duplicate AudioFile");
            inside = false;
        };
        while ((hr = reader->Read(&type)) == S_OK)
        {
            wchar_t const* value = nullptr;
            UINT depth = 0;
            reader->GetDepth(&depth);
            if (type == XmlNodeType_Element)
            {
                reader->GetLocalName(&value, nullptr);
                std::wstring name = value;
                if (depth == 0 && name == L"Subtitles" && !root) root = true;
                else if (root && depth == 1 && (name == L"Static" || name == L"Dynamic") && !inside)
                {
                    entry = Entry{};
                    key = AudioKey(Attr(reader.Get(), L"AudioFile"));
                    if (key.empty()) throw std::runtime_error("Empty AudioFile");
                    entry.area = Attr(reader.Get(), L"TextArea");
                    static wchar_t const* areas[] = {L"Debug", L"Cinematic", L"News", L"Ingame", L"Ingame_BG", L"Ingame_NN"};
                    if (std::none_of(std::begin(areas), std::end(areas), [&](auto a) { return entry.area == a; }))
                        throw std::runtime_error("Unknown TextArea");
                    auto hack = Attr(reader.Get(), L"Hack", false);
                    if (!hack.empty() && hack != L"Streamed") throw std::runtime_error("Unknown Hack");
                    inside = true;
                    dynamic = name == L"Dynamic";
                    if (reader->IsEmptyElement()) finishEntry();
                }
                else if (inside && dynamic && !inPart && depth == 2 && name == L"Part")
                {
                    part = Part{};
                    part.start = Time(Attr(reader.Get(), L"Start"));
                    part.end = Time(Attr(reader.Get(), L"End"));
                    if (part.end <= part.start) throw std::runtime_error("Invalid Part interval");
                    inPart = true;
                    if (reader->IsEmptyElement()) { entry.parts.push_back(part); inPart = false; }
                }
                else throw std::runtime_error("Unexpected XML element: depth=" + std::to_string(depth) +
                    " inside=" + std::to_string(inside));
            }
            else if (type == XmlNodeType_EndElement)
            {
                // XmlLite reports EndElement at the depth of its content, one
                // deeper than the corresponding opening element.
                if (depth == 3 && inPart) { part.text = Trim(part.text); entry.parts.push_back(std::move(part)); inPart = false; }
                else if (depth == 2 && inside) finishEntry();
            }
            else if (type == XmlNodeType_Text || type == XmlNodeType_CDATA || type == XmlNodeType_Whitespace)
            {
                reader->GetValue(&value, nullptr);
                if (inPart) part.text += value;
                else if (inside && !dynamic) entry.text += value;
                else if (!Trim(value).empty()) throw std::runtime_error("Unexpected text");
            }
        }
        if (FAILED(hr) || !root || inside || inPart) throw std::runtime_error("Malformed subtitle XML");
        result.swap(parsed);
        return true;
    }
    catch (std::exception const& e)
    {
        UINT line = 0;
        if (reader) reader->GetLineNumber(&line);
        error = std::wstring(e.what(), e.what() + strlen(e.what())) + L" (line " + std::to_wstring(line) + L")";
        return false;
    }
}
}
