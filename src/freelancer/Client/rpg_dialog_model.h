#pragma once
// Local presentation prototype. No skill rolls or authoritative world mutations.
struct FRpgDialogModel
{
    int Node = 0;
    bool Done = false;
    int Count() const { return Node == 0 ? 4 : 2; }
    void Choose(int Index)
    {
        if (Done || Index < 0 || Index >= Count()) return;
        if (Node == 0) { if (Index == 3) Done = true; else Node = Index + 1; }
        else if (Index == 0) Node = 0;
        else Done = true;
    }
};
