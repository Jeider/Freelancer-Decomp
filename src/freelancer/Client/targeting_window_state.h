#pragma once

// Desired visibility is independent of the scale/slide animation in progress.
struct TargetingWindowState
{
    unsigned targetId = 0;
    bool open = false;
    bool locked = false;
    bool restorePending = false;
    bool restoredOpen = false;
    bool autoOpenAllowed = false;

    void Restore(bool wasOpen, bool wasLocked)
    {
        targetId = 0;
        open = wasLocked && wasOpen;
        locked = wasLocked;
        restorePending = !wasLocked;
        restoredOpen = wasOpen;
        autoOpenAllowed = false;
    }

    void Observe(unsigned eligibleTarget, bool hostileShip)
    {
        autoOpenAllowed = eligibleTarget != 0 && hostileShip;
        if (!eligibleTarget && !locked) open = false;
        else if (restorePending && autoOpenAllowed) { open = restoredOpen; restorePending = false; }
        else if (eligibleTarget != targetId && autoOpenAllowed && !locked) open = true;
        targetId = eligibleTarget;
    }
    void ToggleOpen() { open = (targetId != 0 || locked) && !open; restorePending = false; }
    void SetLocked(bool value)
    {
        if (locked == value) return;
        locked = value;
        restorePending = false;
        if (!locked && !targetId) open = false;
        else if (!locked && autoOpenAllowed) open = true;
    }
    void ToggleLock() { SetLocked(!locked); }
};
