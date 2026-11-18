// Real D3D9 device fixture. Run before the material/lighting fixtures add their textures.
static void CheckRoomCache(FDirectX9* p, IDirect3DDevice9* d)
{
    auto* e = p->Ex_;
    int first = 0, second = 0;
    IRPRoomMaterialCache* cache = nullptr;
    C(p->QueryInterface(Iids::RPRoomMaterialCache, reinterpret_cast<void**>(&cache)));
    R(cache != nullptr, "separate room-cache ABI is available");
    auto const& hair = kFullHairMaterials[9]; // The Brighton map seen in the hitch log.
    const std::string key = std::string(hair.Name) + "|" + hair.Texture;
    auto loadHair = [&] { C(cache->PreloadRoomMaterial(hair.Name, hair.Texture)); };
    unsigned long start = e->RoomTextureLoads;
    loadHair();
    R(e->RoomTextureLoads == start, "no preload outside a room visit");
    C(cache->BeginRoomMaterialCache(&first, "li01_01_base"));
    C(cache->BeginRoomMaterialCache(&first, "li01_01_base")); // Idempotent owner.
    C(cache->BeginRoomMaterialCache(&second, "li01_01_base"));
    e->RoomBase = "sentinel"; e->RoomDetail = "sentinel-detail"; e->RoomFinish = 3;
    e->bRoomFrame = false; e->bRoomBrick = true; e->bRoomProp = true;
    DWORD before = 0, after = 0;
    C(d->GetRenderState(D3DRS_ALPHABLENDENABLE, &before));
    loadHair();
    C(d->GetRenderState(D3DRS_ALPHABLENDENABLE, &after));
    R(e->RoomTextureLoads == start + 1, "map loads during preload before any draw");
    R(e->RoomVs && e->RoomSkinVs && e->RoomPs, "rigid and skinned shaders ready before draw");
    R(e->RoomBase == "sentinel" && e->RoomDetail == "sentinel-detail" && e->RoomFinish == 3 &&
      !e->bRoomFrame && e->bRoomBrick && e->bRoomProp && before == after && !e->RoomCurrent,
      "preload preserves draw selection and device state");
    std::string lower = key; for (auto& c : lower) c = char(tolower((unsigned char)c));
    auto& profile = e->RoomProfiles.at(lower);
    auto* texture = profile.Texture;
    R(texture != nullptr, "real hair PNG decoded and uploaded");
    auto& alias = e->RoomProfiles["cache_alias|cache_alias.tga"];
    alias.Map = hair.Map;
    C(cache->PreloadRoomMaterial("cache_alias", "cache_alias.tga"));
    R(alias.Texture == texture && e->RoomTextureLoads == start + 1, "shared map uses one GPU texture");
    for (unsigned i = 0; i < 1000; ++i)
    {
        C(p->SetRoomMaterialFrame(1)); C(p->SetRoomMaterialFrame(0)); loadHair();
    }
    R(profile.Texture == texture && e->RoomTextureLoads == start + 1,
      "1000 off-camera frames and repeated requests do not evict or reload");
    auto& missing = e->RoomProfiles["cache_missing|cache_missing.tga"];
    missing.Map = "missing_room_cache_fixture.dds";
    for (unsigned i = 0; i < 3; ++i) C(cache->PreloadRoomMaterial("cache_missing", "cache_missing.tga"));
    R(missing.Tried && !missing.Texture && e->RoomTextureLoads == start + 2,
      "missing map tried once per visit; native fallback stays available");
    C(cache->EndRoomMaterialCache(&first));
    C(cache->EndRoomMaterialCache(&first));
    R(profile.Texture == texture, "overlapping room retains its shared maps");
    C(cache->EndRoomMaterialCache(&second));
    R(!profile.Texture && !alias.Texture && !missing.Tried && e->RoomPreloadedMaterials.empty(),
      "last room releases maps and negative cache");
    C(cache->BeginRoomMaterialCache(&first, "li01_01_base")); loadHair();
    R(profile.Texture && e->RoomTextureLoads == start + 3, "next visit preloads again");
    // Ordinary device-reset cleanup must keep managed textures alive.
    texture = profile.Texture; p->ExReleaseDeviceResources();
    R(profile.Texture == texture, "managed room maps survive ordinary device reset cleanup");
    p->ExRoomMaterialRelease(); loadHair();
    R(profile.Texture && e->RoomTextureLoads == start + 4, "full GPU release invalidates preload bookkeeping");
    C(cache->EndRoomMaterialCache(&first));
    C(p->SetRoomMaterialFrame(1)); C(p->SetRoomMaterial(hair.Name, hair.Texture));
    p->ExRoomMaterialLoad();
    for (unsigned i = 0; i < 360; ++i) C(p->SetRoomMaterialFrame(1));
    R(!profile.Texture, "legacy client without room ownership keeps bounded aging");
    C(p->SetRoomMaterialFrame(0)); C(p->SetRoomBase(""));
    e->RoomDetail.clear(); e->RoomFinish = 0;
    e->RoomProfiles.erase("cache_alias|cache_alias.tga");
    e->RoomProfiles.erase("cache_missing|cache_missing.tga");
    cache->Release();
    puts("PASS: room preload, state preservation, off-camera retention, shared maps, owners, missing maps and device cleanup");
}
