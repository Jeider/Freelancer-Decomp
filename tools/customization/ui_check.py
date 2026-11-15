"""Capture or click inside one explicitly selected Freelancer test window."""
import argparse
import ctypes as c
from ctypes import wintypes as w
from pathlib import Path
import time
from PIL import ImageGrab

p=argparse.ArgumentParser(); p.add_argument('pid',type=int)
p.add_argument('--click',nargs=2,type=float); p.add_argument('--escape',action='store_true')
p.add_argument('--capture',type=Path); args=p.parse_args()
u=c.WinDLL('user32',use_last_error=True); found=[]
callback=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
@callback
def visit(hwnd,unused):
    owner=w.DWORD(); u.GetWindowThreadProcessId(hwnd,c.byref(owner))
    name=c.create_unicode_buffer(128); u.GetClassNameW(hwnd,name,128)
    if owner.value==args.pid and name.value=='Freelancer': found.append(hwnd)
    return True
u.EnumWindows(visit,0); assert len(found)==1,found
hwnd=found[0]; u.SetForegroundWindow(hwnd); time.sleep(.2)
assert u.GetForegroundWindow()==hwnd,'Test window is not foreground'
if args.click:
    x,y=args.click; assert 0<=x<=1 and 0<=y<=1
    rect=w.RECT(); u.GetClientRect(hwnd,c.byref(rect))
    point=w.POINT(int(rect.right*x),int(rect.bottom*y)); u.ClientToScreen(hwnd,c.byref(point))
    u.SetCursorPos(point.x,point.y); time.sleep(.1)
    u.mouse_event(2,0,0,0,0); time.sleep(.1); u.mouse_event(4,0,0,0,0)
if args.escape:
    u.keybd_event(27,0,0,0); time.sleep(.1); u.keybd_event(27,0,2,0)
time.sleep(.7)
if args.capture:
    rect=w.RECT(); assert u.GetWindowRect(hwnd,c.byref(rect))
    args.capture.parent.mkdir(parents=True,exist_ok=True)
    ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom)).save(args.capture)
    print(args.capture)
