#pragma once

struct FContentBase;
struct FBarCharacter;

// Port-only presence layer. No character/room ABI changes and no Story dependency.
void RpgContactsEnter(FContentBase& Base, unsigned int PlayerId);
void RpgContactsLeave(FContentBase& Base, unsigned int PlayerId);
void RpgContactsLogout(unsigned int PlayerId);
void RpgContactsUnload(FContentBase& Base);
void RpgContactsClear();
bool RpgContactsOwns(FBarCharacter const* Character);
