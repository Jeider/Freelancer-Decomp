#pragma once
extern "C" char const* __cdecl RpgDialogGestureGroup(unsigned DialogId);

struct INI_Reader;

unsigned RpgDialogLoadFile(char const* Path);
bool RpgDialogConsumeHeader(INI_Reader& Reader, unsigned DialogId);
char const* RpgPendingScript();
unsigned RpgPendingCourierWagons();
char const* RpgDialogSessionScript(unsigned DialogId);
extern "C" char const* __cdecl RpgDialogSceneGroup(unsigned DialogId);
extern "C" char const* __cdecl RpgDialogFragment(unsigned DialogId, unsigned NodeId, int Index, unsigned SessionId);
extern "C" unsigned __cdecl RpgDialogEscape(unsigned DialogId, unsigned NodeId, unsigned SessionId);
extern "C" unsigned __cdecl RpgDialogNodeTextIds(unsigned DialogId, unsigned NodeId);
extern "C" unsigned __cdecl RpgDialogChoiceTextIds(unsigned DialogId, unsigned NodeId, int Index);

extern "C" unsigned __cdecl RpgDialogStart(unsigned DialogId);
extern "C" unsigned __cdecl RpgDialogBeginSession(unsigned DialogId, unsigned SessionId);
extern "C" void __cdecl RpgDialogEndSession(unsigned SessionId);
extern "C" wchar_t const* __cdecl RpgDialogRenderText(unsigned DialogId, unsigned NodeId, int Choice, unsigned SessionId);
extern "C" int __cdecl RpgDialogChoiceCount(unsigned DialogId, unsigned NodeId);
extern "C" wchar_t const* __cdecl RpgDialogNodeText(unsigned DialogId, unsigned NodeId);
extern "C" wchar_t const* __cdecl RpgDialogChoiceText(unsigned DialogId, unsigned NodeId, int Index);
extern "C" unsigned __cdecl RpgDialogChoose(unsigned DialogId, unsigned NodeId, int Index,
                                            unsigned SessionId);
