#pragma once

// Desired visibility is independent of the scale/slide animation in progress.
struct TargetingWindowState
{
    unsigned targetId = 0;
    bool open = false;
    bool locked = false;
    bool restorePending = false;
    bool restoredOpen = false;

    void Restore(bool wasOpen, bool wasLocked)
    {
        targetId = 0;
        open = false;
        locked = wasLocked;
        restorePending = true;
        restoredOpen = wasOpen;
    }

    void Observe(unsigned eligibleTarget)
    {
        if (!eligibleTarget) open = false;
        else if (restorePending) { open = restoredOpen; restorePending = false; }
        else if (eligibleTarget != targetId && !locked) open = true;
        targetId = eligibleTarget;
    }
    void ToggleOpen() { open = targetId != 0 && !open; restorePending = false; }
    void SetLocked(bool value)
    {
        if (locked == value) return;
        locked = value;
        restorePending = false;
        if (!locked && targetId) open = true;
    }
    void ToggleLock() { SetLocked(!locked); }
};
