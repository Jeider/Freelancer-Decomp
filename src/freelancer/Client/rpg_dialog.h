#pragma once
struct FGfScriptSequence;
void RpgDialogOpen(FGfScriptSequence* Sequence);
void RpgDialogOpenOffer(FGfScriptSequence* Sequence);
void RpgDialogOpenTree(FGfScriptSequence* Sequence, unsigned DialogId);
void RpgDialogClose(FGfScriptSequence* Sequence);
void RpgDialogUpdate(FGfScriptSequence* Sequence, int Ms);
bool RpgDialogConsumeAccept();
bool RpgDialogHandleKey(unsigned Message, unsigned Key, unsigned Flags);
