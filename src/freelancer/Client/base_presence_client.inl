// Shares walk-mode pose/animation resources, but never enters scripted room slots.
namespace {
struct FBasePeer {
    BasePresence::Packet state;
    FCharacterObject* body = nullptr;
    FBaseWalkPose pose;
    DWORD received = 0;
    int motionHandle = -1, motion = -1;
    unsigned animationSerial = 0, scriptId = 0;
    float duration = 0;
    std::unique_ptr<FFontString> label;
    ~FBasePeer() { ClearBody(); }
    void ClearBody() {
        if (!body) return;
        if (motionHandle != -1 && body->Lod.Instance) {
            DALib::Deform->DestroyHandle(body->Lod.Instance, motionHandle);
            body->RemoveMotionHandle(motionHandle);
        }
        motionHandle = motion = -1;
        if (scriptId) { GetCharacterInfoDb()->ReleaseScript(scriptId); scriptId = 0; }
        auto* old = body; body = nullptr; delete old;
    }
};
std::map<unsigned, std::unique_ptr<FBasePeer>> GBasePeers;
FRoomRuntime* GBasePeerRoom = nullptr;
DWORD GBasePresenceSent = 0;

void BasePresenceClear() {
    GBasePeers.clear(); GBasePeerRoom = nullptr; GBasePresenceSent = 0;
}
void BasePresenceRoomDestroyed(FRoomRuntime* room) {
    if (room == GBasePeerRoom) BasePresenceClear();
}
void PeerMotion(FBasePeer& peer) {
    int kind = static_cast<int>(peer.state.motion);
    if (!peer.body || !peer.body->Lod.Instance) return;
    float elapsed = kind >= 3 ? (peer.state.animationMs + GetTickCount() - peer.received) * .001f : 0.f;
    if (kind == peer.motion && (kind < 3 || peer.animationSerial == peer.state.animationSerial)) {
        HoldEmoteLastFrame(kind, peer.motionHandle, elapsed, peer.duration);
        return;
    }
    if (peer.motionHandle != -1) {
        DALib::Deform->DestroyHandle(peer.body->Lod.Instance, peer.motionHandle);
        peer.body->RemoveMotionHandle(peer.motionHandle); peer.motionHandle = -1;
    }
    auto* db = GetCharacterInfoDb();
    if (!db) return;
    if (peer.scriptId) { db->ReleaseScript(peer.scriptId); peer.scriptId = 0; }
    auto found = db->Scripts.find(CreateID(BaseEmotes::Name(kind)));
    if (found == db->Scripts.end()) return;
    char const* name = found->second.Name.c_str();
    auto* script = db->AcquireScriptByName(name);
    if (script == reinterpret_cast<void*>(static_cast<intptr_t>(-1))) return;
    peer.scriptId = CreateID(name);
    peer.duration = DALib::Anim->GetNamedDuration(script, name);
    // A late observer must still create the playback before posing its final keys.
    float start = BaseEmotes::HoldsLastFrame(kind) && elapsed >= peer.duration ? 0.f : elapsed;
    DALib::Deform->Play(peer.body->Lod.Instance, &peer.motionHandle, script,
        const_cast<char*>(name), AsOpaqueDword(start), AsOpaqueDword(.15f), AsOpaqueDword(BaseEmotes::Rate(kind)),
        AsOpaqueDword(1.f), AsOpaqueDword(kind >= 3 ? 0UL : 2UL), AsOpaqueDword(peer.pose.Yaw + 3.14159265359f), nullptr);
    if (peer.motionHandle != -1) peer.body->AddMotionHandle(peer.motionHandle);
    HoldEmoteLastFrame(kind, peer.motionHandle, elapsed, peer.duration);
    peer.motion = kind;
    peer.animationSerial = peer.state.animationSerial;
}

void BasePresenceApply();
void BasePresenceTick(float dt) {
    auto* room = IsBase() ? static_cast<FRoomRuntime*>(GetClientCurrentLocationRuntime()) : nullptr;
    if (SinglePlayer() || !room) { BasePresenceClear(); return; }
    if (room != GBasePeerRoom) { BasePresenceClear(); GBasePeerRoom = room; }
    DWORD now = GetTickCount();
    bool available = RoomAvailable(room);
    if (now - GBasePresenceSent >= BasePresence::IntervalMs) {
        GBasePresenceSent = now;
        BasePresence::Packet packet;
        packet.base = GetRoomRuntimeBaseId(room); packet.room = GetRoomRuntimeRoomId(room);
        packet.visible = available && G_BaseWalk.bEnabled && G_BaseWalk.Room == room &&
            G_BaseWalk.Player && WorldAvailable(room, G_BaseWalk.Player);
        if (packet.visible) {
            std::memcpy(packet.position, G_BaseWalk.Pose.Position, sizeof(packet.position));
            packet.yaw = G_BaseWalk.Pose.Yaw;
            packet.motion = static_cast<unsigned>((std::max)(0, G_BaseWalk.MotionKind));
            packet.animationSerial = GEmoteSerial;
            if (packet.motion >= 3) packet.animationMs = (std::min)(GetTickCount() - GEmoteStart, DWORD(300000));
        }
        if (auto* server = static_cast<IChatServer*>(G_ChatServer))
            server->SubmitChat(CHAT_ID(GetPlayerConnectionId() & 0xffffu), sizeof(packet), &packet,
                               CHAT_ID(BasePresence::Channel), -1);
    }
    float const blend = 1.f - std::exp(-14.f * (std::max)(0.f, (std::min)(dt, .25f)));
    for (auto it = GBasePeers.begin(); it != GBasePeers.end();) {
        auto& peer = *it->second;
        if (now - peer.received > BasePresence::TimeoutMs ||
            !BasePresence::SameRoom(peer.state.base, peer.state.room, GetRoomRuntimeBaseId(room), GetRoomRuntimeRoomId(room))) {
            it = GBasePeers.erase(it); continue;
        }
        if (!available || !peer.state.visible) { peer.ClearBody(); ++it; continue; }
        if (!peer.body) {
            Costume costume = {};
            std::memcpy(costume.PartIds, peer.state.parts, sizeof(costume.PartIds));
            std::memcpy(costume.AccessoryIds, peer.state.accessories, sizeof(costume.AccessoryIds));
            costume.AccessoryCount = peer.state.accessoryCount;
            peer.body = CreateWalkPlayer(room, &costume);
            if (peer.body) {
                peer.body->SetOwnScript(nullptr, 0);
                peer.body->bNoUpdate = 0; // normal room tick advances the animation mixer
                std::memcpy(peer.pose.Position, peer.state.position, sizeof(peer.pose.Position));
                peer.pose.Yaw = peer.state.yaw;
            }
        }
        for (int axis = 0; axis < 3; ++axis)
            peer.pose.Position[axis] += (peer.state.position[axis] - peer.pose.Position[axis]) * blend;
        float delta = std::remainder(peer.state.yaw - peer.pose.Yaw, 6.28318530718f);
        peer.pose.Yaw += delta * blend;
        PeerMotion(peer); ++it;
    }
    BasePresenceApply();
}

void BasePresenceApply() {
    if (!GBasePeerRoom) return;
    if (!RoomAvailable(GBasePeerRoom)) {
        for (auto& item : GBasePeers) item.second->ClearBody();
        return;
    }
    for (auto& item : GBasePeers) {
        auto& peer = *item.second;
        if (!peer.body || !peer.body->Lod.Instance) continue;
        void* instance = peer.body->GetEngineInstance();
        if (!instance || instance == reinterpret_cast<void*>(static_cast<intptr_t>(-1))) continue;
        float orientation[9]; peer.pose.CharacterOrientation(orientation);
        DALib::Deform->SetPosePos(peer.body->Lod.Instance, peer.pose.Position);
        DALib::Deform->SetPoseOri(peer.body->Lod.Instance, orientation);
        DALib::Engine->SetInstancePosition(instance, peer.pose.Position);
        peer.body->bPoseDirty = 1;
        DALib::Engine->UpdateInstance(instance, 0, nullptr);
    }
}
}

bool BaseWalkReceivePresence(unsigned sender, unsigned size, void const* data) {
    if (sender != BasePresence::Channel) return false;
    BasePresence::Packet packet;
    if (SinglePlayer() || !IsBase() || !BasePresence::Decode(data, size, packet) ||
        !packet.player || packet.player > 128 || packet.player == (GetPlayerConnectionId() & 0xffffu) ||
        packet.accessoryCount > 8) return true;
    auto* room = static_cast<FRoomRuntime*>(GetClientCurrentLocationRuntime());
    if (!room || !BasePresence::SameRoom(packet.base, packet.room, GetRoomRuntimeBaseId(room), GetRoomRuntimeRoomId(room))) return true;
    if (room != GBasePeerRoom) { BasePresenceClear(); GBasePeerRoom = room; }
    auto& ptr = GBasePeers[packet.player];
    if (!ptr) ptr.reset(new FBasePeer);
    auto& peer = *ptr;
    packet.name[32] = 0;
    bool renamed = std::memcmp(peer.state.name, packet.name, sizeof(packet.name)) != 0;
    if (renamed || std::memcmp(peer.state.parts, packet.parts, sizeof(packet.parts)) ||
        std::memcmp(peer.state.accessories, packet.accessories, sizeof(packet.accessories)) ||
        peer.state.accessoryCount != packet.accessoryCount) peer.ClearBody();
    if (renamed) peer.label.reset();
    peer.state = packet; peer.received = GetTickCount();
    if (!packet.visible) peer.ClearBody();
    return true;
}

void BaseWalkDrawNames() {
    if (IsBase() && G_BaseWalk.bEnabled && G_BaseWalk.Player &&
        RoomAvailable(G_BaseWalk.Room) && InputAvailable() && !G_BaseWalk.bLooking) {
        auto* font = FindMenuFontImp("Normal");
        if (font) {
            static wchar_t const* labels[] = {L"\u0422\u0430\u043d\u0446\u0435\u0432\u0430\u0442\u044c", L"\u041e\u0442\u0434\u0430\u0442\u044c \u0447\u0435\u0441\u0442\u044c", L"\u041f\u044c\u044f\u043d\u0430\u044f \u043f\u043e\u0445\u043e\u0434\u043a\u0430", L"\u0421\u043a\u0440\u0435\u0441\u0442\u0438\u0442\u044c \u0440\u0443\u043a\u0438", L"\u041f\u043e\u0434\u043d\u044f\u0442\u044c \u0440\u0443\u043a\u0438"};
            int viewport[4]; Win3DGetViewport(0xba2, viewport);
            unsigned color = FontAtlasDrawColor(); UiOverlayPrepPipeline();
            Win3DSetViewportRect(0, 0, static_cast<int>(G_RenderSurfaceWidth), static_cast<int>(G_RenderSurfaceHeight), __FILE__, __LINE__);
            for (int i = 0; i < 5; ++i) {
                FFontString text; FontStringSetText(&text, labels[i]); FontStringSetFont(&text, font);
                FFontStringDrawOrigin origin = {};
                origin.X = 16; origin.Y = G_RenderSurfaceHeight - 160 + i * 28;
                origin.Scale = 230; origin.Height = 28; origin.Field10 = 1;
                FontAtlasSetDrawColor(i == GEmoteHover ? 0xffffffff : 0xffa8e8ff);
                FontStringDrawChildren(&origin, &text, nullptr, nullptr);
            }
            FontAtlasSetDrawColor(color); UiOverlayPrepPipeline();
            Win3DSetViewportRect(viewport[0], viewport[1], viewport[2], viewport[3], __FILE__, __LINE__);
        }
    }
    if (!IsBase() || !GBasePeerRoom || !RoomAvailable(GBasePeerRoom)) return;
    auto* camera = GetRoomRuntimeRoomCamera(GBasePeerRoom);
    auto* font = FindMenuFontImp("Normal");
    if (!camera || !font) return;
    int viewport[4]; Win3DGetViewport(0xba2, viewport);
    unsigned color = FontAtlasDrawColor();
    UiOverlayPrepPipeline();
    Win3DSetViewportRect(0, 0, static_cast<int>(G_RenderSurfaceWidth), static_cast<int>(G_RenderSurfaceHeight), __FILE__, __LINE__);
    for (auto& item : GBasePeers) {
        auto& peer = *item.second;
        if (!peer.body || !peer.state.visible) continue;
        float head[3] = {peer.pose.Position[0], peer.pose.Position[1] + 1.80f, peer.pose.Position[2]};
        float x, y, z;
        if (!camera->Project(&x, &y, &z, head) || z > 35.f || x < 0 || y < 0 ||
            x > G_RenderSurfaceWidth || y > G_RenderSurfaceHeight) continue;
        if (!peer.label) {
            wchar_t name[33] = {};
            for (int n=0; n<32; ++n) name[n] = static_cast<wchar_t>(peer.state.name[n]);
            peer.label.reset(new FFontString); FontStringSetText(peer.label.get(), name);
        }
        FontStringSetFont(peer.label.get(), font);
        int extent[2] = {}; FontStringGetExtent(peer.label.get(), extent);
        FFontStringDrawOrigin origin = {};
        origin.X = x - 120; origin.Y = y - extent[1] + 4; origin.Scale = 240;
        origin.Height = static_cast<float>((std::max)(extent[1], 24)); origin.Field10 = 1;
        FontAtlasSetDrawColor(0xff000000); FontStringDrawChildren(&origin, peer.label.get(), nullptr, nullptr);
        origin.X -= 1; origin.Y -= 1;
        FontAtlasSetDrawColor(0xffa8e8ff); FontStringDrawChildren(&origin, peer.label.get(), nullptr, nullptr);
    }
    FontAtlasSetDrawColor(color); UiOverlayPrepPipeline();
    Win3DSetViewportRect(viewport[0], viewport[1], viewport[2], viewport[3], __FILE__, __LINE__);
}
