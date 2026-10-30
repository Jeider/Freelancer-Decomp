#pragma once

class INI_Reader;
struct FClientGameobj;

// Optional solar companion settings, kept outside the retail ABI layouts.
bool TradeLaneRingAnimRead(void const* Companion, INI_Reader& Reader);
void TradeLaneRingAnimCopy(void const* Destination, void const* Source);
void TradeLaneRingAnimForgetConfig(void const* Companion);
bool TradeLaneRingAnimConfigured(FClientGameobj* Solar, unsigned Side);

// Called only for a server-accepted activation of an idle entrance ring.
void TradeLaneRingAnimStart(FClientGameobj* Solar, unsigned Side);
void TradeLaneRingAnimTick();
void TradeLaneRingAnimForget(FClientGameobj* Solar);
void TradeLaneRingAnimShutdown();
