#!/usr/bin/env python3
"""
Continuous Screenshot Tool for macOS
- Shows selection border while dragging
- Final screenshot is completely clean
- ESC to quit
"""

import subprocess, sys, os, signal
from datetime import datetime

def ensure_deps():
    for pkg, mod in [("pyobjc-core", "objc"), ("pyobjc-framework-Cocoa", "AppKit"), ("pyobjc-framework-Quartz", "Quartz")]:
        try:
            __import__(mod)
        except ImportError:
            print(f"Installing {pkg}…")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

ensure_deps()

import objc
from Foundation import NSDate, NSRunLoop
from AppKit import (
    NSApplication, NSApp, NSWindow, NSView, NSColor, NSBezierPath,
    NSScreen, NSFont, NSString, NSAttributedString,
    NSFontAttributeName, NSForegroundColorAttributeName,
    NSWindowStyleMaskBorderless, NSBackingStoreBuffered,
    NSFloatingWindowLevel, NSCursor,
    NSMakeRect, NSMakePoint,
    NSApplicationActivationPolicyRegular,
)
from Cocoa import NSObject
import Quartz

DESKTOP  = os.path.expanduser("~/Desktop")
ACCENT   = NSColor.colorWithCalibratedWhite_alpha_(0.9, 0.9)  
SEL_FILL = NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.15) 

signal.signal(signal.SIGINT, lambda *_: NSApp.terminate_(None))


def do_capture(x, y, w, h):
    ts   = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]
    path = os.path.join(DESKTOP, f"screenshot_{ts}.png")
    ret  = subprocess.run(
        ["screencapture", "-x", "-R", f"{x},{y},{w},{h}", path],
        capture_output=True,
    )
    return ret.returncode == 0, ts, ret.stderr.decode().strip()


class OverlayView(NSView):

    def initWithFrame_(self, frame):
        self = objc.super(OverlayView, self).initWithFrame_(frame)
        if self is None:
            return None
        self._start       = None
        self._current     = None
        self._dragging    = False
        self._show_sel    = False
        self._flash_msg   = None
        self._flash_until = 0.0
        self._count       = 0
        self._mouse_pos   = NSMakePoint(0, 0)
        return self

    def drawRect_(self, dirty):
        NSColor.clearColor().setFill()
        NSBezierPath.fillRect_(self.bounds())

        w   = self.bounds().size.width
        h   = self.bounds().size.height
        mx  = self._mouse_pos.x
        my  = self._mouse_pos.y
        now = datetime.now().timestamp()

        # crosshair
        '''ACCENT.colorWithAlphaComponent_(0.6).setStroke()
        path = NSBezierPath.bezierPath()
        path.setLineWidth_(0.8)
        path.setLineDash_count_phase_([6.0, 4.0], 2, 0.0)
        path.moveToPoint_(NSMakePoint(0, my));  path.lineToPoint_(NSMakePoint(w, my))
        path.moveToPoint_(NSMakePoint(mx, 0)); path.lineToPoint_(NSMakePoint(mx, h))
        path.stroke()
        '''
        
        # Draw a clean '+' sign at the cursor
        ACCENT.setStroke()
        plus_path = NSBezierPath.bezierPath()
        plus_path.setLineWidth_(1.5)
        
        # Horizontal line
        plus_path.moveToPoint_(NSMakePoint(mx - 7, my))
        plus_path.lineToPoint_(NSMakePoint(mx + 7, my))
        
        # Vertical line
        plus_path.moveToPoint_(NSMakePoint(mx, my - 7))
        plus_path.lineToPoint_(NSMakePoint(mx, my + 7))
        
        plus_path.stroke()

        

        if self._show_sel and self._start and self._current:
            sx0, sy0 = self._start
            cx,  cy  = self._current
            rx = min(sx0, cx); ry = min(sy0, cy)
            rw = abs(cx - sx0); rh = abs(cy - sy0)
            rect = NSMakeRect(rx, ry, rw, rh)
            SEL_FILL.setFill()
            NSBezierPath.fillRect_(rect)
            ACCENT.setStroke()
            bp = NSBezierPath.bezierPathWithRect_(rect)
            bp.setLineWidth_(1.5)
            bp.stroke()

        dim_attrs = {
            NSFontAttributeName: NSFont.systemFontOfSize_(11), 
            NSForegroundColorAttributeName: ACCENT.colorWithAlphaComponent_(0.75),
        }
        NSAttributedString.alloc().initWithString_attributes_(
            NSString.stringWithString_("Drag to capture   •   ESC to quit"), dim_attrs
        ).drawAtPoint_(NSMakePoint(w - 285, h - 28))

        NSAttributedString.alloc().initWithString_attributes_(
            NSString.stringWithString_(
                f"📸  {self._count} screenshot{'s' if self._count != 1 else ''} saved"
            ), dim_attrs
        ).drawAtPoint_(NSMakePoint(14, 14))

        if self._flash_msg and now < self._flash_until:
            f_attrs = {
                NSFontAttributeName: NSFont.boldSystemFontOfSize_(13),
                NSForegroundColorAttributeName: ACCENT,
            }
            NSAttributedString.alloc().initWithString_attributes_(
                NSString.stringWithString_(self._flash_msg), f_attrs
            ).drawAtPoint_(NSMakePoint(w / 2 - 200, h / 2 - 10))

    def isOpaque(self): return False
    def acceptsFirstResponder(self): return True

    def mouseDown_(self, event):
        p = self.convertPoint_fromView_(event.locationInWindow(), None)
        self._start    = (p.x, p.y)
        self._current  = (p.x, p.y)
        self._dragging = True
        self._show_sel = True
        self.setNeedsDisplay_(True)

    def mouseDragged_(self, event):
        p = self.convertPoint_fromView_(event.locationInWindow(), None)
        self._current   = (p.x, p.y)
        self._mouse_pos = p
        self.setNeedsDisplay_(True)

    def mouseUp_(self, event):
        p = self.convertPoint_fromView_(event.locationInWindow(), None)
        self._dragging = False

        if self._start:
            sx0, sy0 = self._start
            cx, cy   = p.x, p.y
            x1 = int(min(sx0, cx)); y1v = int(min(sy0, cy))
            x2 = int(max(sx0, cx)); y2v = int(max(sy0, cy))
            pw = x2 - x1; ph = y2v - y1v

            if pw > 5 and ph > 5:
                screen_h  = int(NSScreen.mainScreen().frame().size.height)
                sy_screen = screen_h - y2v

                self._show_sel = False
                self._start    = None
                self.window().setAlphaValue_(0.0)

                # ── NEW FIX: Keep the UI running so the screen actually clears ──
                # This gives macOS 0.2 seconds to redraw the desktop without our window,
                # BEFORE the screencapture command fires.
                delay_date = NSDate.dateWithTimeIntervalSinceNow_(0.2)
                NSRunLoop.currentRunLoop().runUntilDate_(delay_date)

                ok, ts, err = do_capture(x1, sy_screen, pw, ph)

                self.window().setAlphaValue_(1.0)
                self.window().makeKeyAndOrderFront_(None)
                NSApp.activateIgnoringOtherApps_(True)
                self.window().makeFirstResponder_(self)

                if ok:
                    self._count      += 1
                    self._flash_msg   = f"✓  Saved: screenshot_{ts}.png"
                else:
                    self._flash_msg   = f"✗  Error: {err}"
                self._flash_until = datetime.now().timestamp() + 1.8
            else:
                self._show_sel = False
                self._start    = None

        self.setNeedsDisplay_(True)

    def mouseMoved_(self, event):
        p = self.convertPoint_fromView_(event.locationInWindow(), None)
        self._mouse_pos = p
        self.setNeedsDisplay_(True)

    def keyDown_(self, event):
        if event.keyCode() == 53:
            NSApp.terminate_(None)


class AppDelegate(NSObject):

    def applicationDidFinishLaunching_(self, note):
        screen = NSScreen.mainScreen().frame()
        win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            screen, NSWindowStyleMaskBorderless, NSBackingStoreBuffered, False,
        )
        win.setLevel_(NSFloatingWindowLevel + 1)
        win.setOpaque_(False)
        win.setBackgroundColor_(NSColor.clearColor())
        win.setIgnoresMouseEvents_(False)
        win.setAcceptsMouseMovedEvents_(True)
        win.setCollectionBehavior_(1 << 3)

        view = OverlayView.alloc().initWithFrame_(screen)
        win.setContentView_(view)
        win.makeKeyAndOrderFront_(None)
        win.makeFirstResponder_(view)
        NSApp.activateIgnoringOtherApps_(True)
        NSCursor.crosshairCursor().push()
        self._win  = win
        self._view = view

        mask = Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown)

        def handler(proxy, etype, event, refcon):
            keycode = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGKeyboardEventKeycode
            )
            if keycode == 53:
                NSApp.terminate_(None)
            return event

        self._tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionListenOnly,
            mask,
            handler,
            None,
        )
        if self._tap:
            src = Quartz.CFMachPortCreateRunLoopSource(None, self._tap, 0)
            Quartz.CFRunLoopAddSource(
                Quartz.CFRunLoopGetCurrent(), src, Quartz.kCFRunLoopCommonModes
            )
            Quartz.CGEventTapEnable(self._tap, True)
        else:
            print("⚠️  Global ESC tap failed — grant Accessibility permission")
            print("   System Settings → Privacy & Security → Accessibility")


def main():
    print("=" * 54)
    print("  Continuous Screenshot Tool  (native macOS)")
    print("  • Drag to select → saved to Desktop")
    print("  • ESC to quit  (global)")
    print("  • Ctrl+C in terminal also quits")
    print("=" * 54)
    print("\n⚠️  Permissions needed:")
    print("   Screen Recording  → System Settings → Privacy & Security")
    print("   Accessibility     → same (for global ESC)\n")

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()

if __name__ == "__main__":
    main()