"""Read the windows and controls of a specified smoke-test process; optionally capture its game window."""
import ctypes as c
from ctypes import wintypes as w
import sys

pid = int(sys.argv[1])
u = c.WinDLL('user32', use_last_error=True)
callback = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
u.GetWindowTextW.argtypes = [w.HWND, w.LPWSTR, c.c_int]
u.GetClassNameW.argtypes = [w.HWND, w.LPWSTR, c.c_int]
u.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
u.IsWindowVisible.argtypes = [w.HWND]
u.EnumWindows.argtypes = [callback, w.LPARAM]
u.EnumChildWindows.argtypes = [w.HWND, callback, w.LPARAM]

def describe(hwnd, prefix):
    title = c.create_unicode_buffer(4096)
    name = c.create_unicode_buffer(256)
    u.GetWindowTextW(hwnd, title, len(title))
    u.GetClassNameW(hwnd, name, len(name))
    print(prefix, hex(hwnd), name.value, 'visible='+str(bool(u.IsWindowVisible(hwnd))), repr(title.value), flush=True)

@callback
def child(hwnd, unused):
    describe(hwnd, ' child')
    return True

@callback
def window(hwnd, unused):
    owner = w.DWORD()
    u.GetWindowThreadProcessId(hwnd, c.byref(owner))
    if owner.value == pid:
        describe(hwnd, 'window')
        u.EnumChildWindows(hwnd, child, 0)
        name = c.create_unicode_buffer(256)
        u.GetClassNameW(hwnd, name, len(name))
        if '--activate' in sys.argv and name.value == 'Freelancer':
            u.ShowWindow.argtypes = [w.HWND, c.c_int]
            u.SetForegroundWindow.argtypes = [w.HWND]
            u.ShowWindow(hwnd, 9)
            u.SetForegroundWindow(hwnd)
        if len(sys.argv) >= 3 and not sys.argv[2].startswith('--') and name.value == 'Freelancer' and u.IsWindowVisible(hwnd):
            from PIL import ImageGrab
            rect = w.RECT()
            u.GetWindowRect.argtypes = [w.HWND, c.POINTER(w.RECT)]
            u.GetWindowRect(hwnd, c.byref(rect))
            ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom)).save(sys.argv[2])
    return True

u.EnumWindows(window, 0)
