"""
RepScheduler - Personalized desk exercise reminder for Windows
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Install: pip install -r requirements.txt
Run:     pythonw Repscheduler.py   (no console window)
         python  Repscheduler.py   (with console)
"""

import wx
import wx.adv
import json
import random
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
#  THEME  —  Mem Reduct-style: dark system utility, monospace, tight rows
# ═══════════════════════════════════════════════════════════════════════════════

BG        = wx.Colour(30,  30,  30)   # window / dialog background
SURFACE   = wx.Colour(20,  20,  20)   # recessed surface (section boxes, headers)
BORDER    = wx.Colour(60,  60,  60)   # 1-px dividers and box borders
TEXT      = wx.Colour(220, 220, 220)  # primary text
MUTED     = wx.Colour(130, 130, 130)  # secondary / label text
BTN_BG    = wx.Colour(50,  50,  50)   # default button fill
BTN_HOV   = wx.Colour(68,  68,  68)   # hovered button fill
BTN_PRE   = wx.Colour(35,  35,  35)   # pressed button fill

def _mono(size, weight=wx.FONTWEIGHT_NORMAL):
    """Monospace font stack: Consolas → Courier New → system mono."""
    for f in ["Consolas", "Courier New", ""]:
        font = wx.Font(size, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
                       weight, faceName=f)
        if font.IsOk():
            return font
    return wx.Font(size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, weight)

def _ui(size, weight=wx.FONTWEIGHT_NORMAL):
    """UI font stack: Segoe UI → Tahoma → system default."""
    for f in ["Segoe UI", "Tahoma", ""]:
        font = wx.Font(size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                       weight, faceName=f)
        if font.IsOk():
            return font
    return wx.Font(size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, weight)

def _darken(c, n):
    return wx.Colour(max(0,c.Red()-n), max(0,c.Green()-n), max(0,c.Blue()-n))
def _lighten(c, n):
    return wx.Colour(min(255,c.Red()+n), min(255,c.Green()+n), min(255,c.Blue()+n))


# ═══════════════════════════════════════════════════════════════════════════════
#  LAYOUT HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def _fit_and_centre(win, margin=60):
    """
    Size a window to its full natural content, cap at screen − margin, centre.
    For dialogs with a ScrolledWindow child, reads the content panel's sizer
    min-size directly so horizontal width is never under-reported.
    """
    idx     = wx.Display.GetFromWindow(win)
    display = wx.Display(idx if idx >= 0 else 0)
    geo     = display.GetClientArea()
    max_w   = geo.width  - margin
    max_h   = geo.height - margin

    natural_w = natural_h = 0
    for child in win.GetChildren():
        if isinstance(child, wx.ScrolledWindow):
            for gc in child.GetChildren():
                if isinstance(gc, wx.Panel):
                    sz = gc.GetSizer()
                    if sz:
                        mw, mh = sz.GetMinSize()
                        if mw > 10 and mh > 10:
                            natural_w, natural_h = mw + 16, mh
                    break
            break

    if natural_w > 0:
        win.SetClientSize(min(natural_w, max_w), min(natural_h, max_h))
    else:
        win.Fit()
        cw, ch = win.GetSize()
        win.SetSize(min(cw, max_w), min(ch, max_h))

    win.Layout()
    ww, wh = win.GetSize()
    win.SetPosition(wx.Point(
        geo.x + (geo.width  - ww) // 2,
        geo.y + (geo.height - wh) // 2,
    ))


# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

CONFIG_DIR  = Path.home() / ".repscheduler"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "first_run": True,
    "profile": "survivor",
    "interval_minutes": 50,
    "fitness": {
        "pullups_avg": 0, "pullups_max": 0,
        "pushups_avg": 0, "pushups_max": 0,
        "squats_avg":  0, "squats_max":  0,
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
#  EXERCISE DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

EXERCISES = {
    "survivor": [
        {"name": "Neck Rolls",           "unit": "reps",    "min": 5,  "max": 10},
        {"name": "Shoulder Shrugs",      "unit": "reps",    "min": 10, "max": 20},
        {"name": "Standing Calf Raises", "unit": "reps",    "min": 15, "max": 30},
        {"name": "Arm Circles",          "unit": "reps",    "min": 10, "max": 20},
        {"name": "Seated Leg Raises",    "unit": "reps",    "min": 10, "max": 20},
        {"name": "Desk Push-offs",       "unit": "reps",    "min": 10, "max": 20},
        {"name": "Wrist Circles",        "unit": "seconds", "min": 15, "max": 30},
        {"name": "Torso Twists",         "unit": "reps",    "min": 10, "max": 20},
        {"name": "Hip Circles",          "unit": "reps",    "min": 8,  "max": 16},
    ],
    "grind": [
        {"name": "Squats",        "unit": "reps",    "fitness_key": "squats",  "min": 10, "max": 25},
        {"name": "Push-ups",      "unit": "reps",    "fitness_key": "pushups", "min": 8,  "max": 20},
        {"name": "Lunges (each)", "unit": "reps",    "min": 10, "max": 20},
        {"name": "Plank Hold",    "unit": "seconds", "min": 20, "max": 45},
        {"name": "Glute Bridges", "unit": "reps",    "min": 15, "max": 25},
        {"name": "Wall Sit",      "unit": "seconds", "min": 20, "max": 45},
        {"name": "Tricep Dips",   "unit": "reps",    "min": 8,  "max": 15},
        {"name": "Pike Push-ups", "unit": "reps",    "min": 6,  "max": 15},
        {"name": "Step-ups",      "unit": "reps",    "min": 10, "max": 20},
    ],
    "drenched": [
        {"name": "Burpees",           "unit": "reps",    "min": 8,  "max": 20},
        {"name": "Jump Squats",       "unit": "reps",    "fitness_key": "squats",  "min": 15, "max": 30},
        {"name": "Push-ups",          "unit": "reps",    "fitness_key": "pushups", "min": 15, "max": 35},
        {"name": "Pull-ups",          "unit": "reps",    "fitness_key": "pullups", "min": 3,  "max": 12},
        {"name": "Mountain Climbers", "unit": "reps",    "min": 20, "max": 40},
        {"name": "High Knees",        "unit": "seconds", "min": 30, "max": 60},
        {"name": "Diamond Push-ups",  "unit": "reps",    "min": 8,  "max": 20},
        {"name": "Jump Lunges",       "unit": "reps",    "min": 10, "max": 20},
        {"name": "Tuck Jumps",        "unit": "reps",    "min": 8,  "max": 15},
    ]
}

PROFILES = {
    "survivor": {
        "label":    "Survivor Mode",
        "tagline":  "Bare minimum. Body stays alive.",
        "color":    wx.Colour(80,  160,  80),
        "ex_count": (1, 2),
        "sets":     (1, 2),
    },
    "grind": {
        "label":    "The Daily Grind",
        "tagline":  "Working-pro energy. Won't kill you.",
        "color":    wx.Colour(210, 120,  30),
        "ex_count": (1, 3),
        "sets":     (2, 3),
    },
    "drenched": {
        "label":    "Drenched",
        "tagline":  "Keyboard will smell like effort.",
        "color":    wx.Colour(200,  60,  60),
        "ex_count": (2, 4),
        "sets":     (3, 5),
    }
}
PROFILE_KEYS = ["survivor", "grind", "drenched"]


# ═══════════════════════════════════════════════════════════════════════════════
#  LOGIC HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in data:
                    data[k] = v
            for k, v in DEFAULT_CONFIG["fitness"].items():
                if k not in data.get("fitness", {}):
                    data.setdefault("fitness", {})[k] = v
            return data
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)

def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def compute_rep_range(ex, fitness):
    lo, hi = ex["min"], ex["max"]
    key = ex.get("fitness_key")
    if key:
        avg = fitness.get(f"{key}_avg", 0)
        mx  = fitness.get(f"{key}_max", 0)
        if avg > 10:
            lo = max(lo, avg - 10)
        elif avg > 0:
            lo = max(lo, avg // 2)
        if mx >= 10:
            hi = max(hi, mx - 5)
        elif mx > 0:
            hi = max(hi, mx)
    return max(1, lo), max(lo + 1, hi)

def generate_workout(profile_key, fitness):
    pool   = EXERCISES[profile_key]
    prof   = PROFILES[profile_key]
    n_ex   = random.randint(*prof["ex_count"])
    n_sets = random.randint(*prof["sets"])
    chosen = random.sample(pool, min(n_ex, len(pool)))
    items  = []
    for ex in chosen:
        lo, hi = compute_rep_range(ex, fitness)
        reps = random.randint(lo, hi)
        items.append({"name": ex["name"], "reps": reps, "unit": ex["unit"]})
    return {"exercises": items, "sets": n_sets, "profile": profile_key}

def make_tray_icon(profile_key):
    color = PROFILES[profile_key]["color"]
    bmp   = wx.Bitmap(16, 16, 32)
    dc    = wx.MemoryDC(bmp)
    dc.SetBackground(wx.Brush(BG))
    dc.Clear()
    dc.SetBrush(wx.Brush(color))
    dc.SetPen(wx.Pen(color))
    dc.DrawRectangle(1, 1, 14, 14)
    dc.SetTextForeground(wx.WHITE)
    dc.SetFont(wx.Font(6, wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
    dc.DrawText("FB", 2, 4)
    dc.SelectObject(wx.NullBitmap)
    icon = wx.Icon()
    icon.CopyFromBitmap(bmp)
    return icon


# ═══════════════════════════════════════════════════════════════════════════════
#  WIDGET HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _lbl(parent, text, size=9, weight=wx.FONTWEIGHT_NORMAL,
         color=None, mono=False):
    """StaticText with correct min-size so sizer never clips it."""
    lbl = wx.StaticText(parent, label=text, style=wx.ST_NO_AUTORESIZE)
    lbl.SetFont(_mono(size, weight) if mono else _ui(size, weight))
    lbl.SetForegroundColour(color or TEXT)
    lbl.SetBackgroundColour(parent.GetBackgroundColour())
    lbl.InvalidateBestSize()
    w, h = lbl.GetBestSize()
    lbl.SetMinSize((w + 2, h))
    return lbl

def _panel(parent, bg=None):
    p = wx.Panel(parent, style=wx.BORDER_NONE)
    p.SetBackgroundColour(bg or BG)
    return p

def _hline(parent):
    """1-px horizontal rule."""
    s = wx.Panel(parent, size=(-1, 1), style=wx.BORDER_NONE)
    s.SetBackgroundColour(BORDER)
    return s

def _section_header(parent, text):
    """Mem Reduct-style recessed section label row."""
    row = _panel(parent, SURFACE)
    lbl = _lbl(row, text, 8, wx.FONTWEIGHT_BOLD, MUTED)
    sz  = wx.BoxSizer(wx.HORIZONTAL)
    sz.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 6)
    row.SetSizer(sz)
    row.SetMinSize((-1, 20))
    return row


# ═══════════════════════════════════════════════════════════════════════════════
#  CUSTOM BUTTON  (flat, sharp corners, monospace label)
# ═══════════════════════════════════════════════════════════════════════════════

class UtilBtn(wx.Panel):
    """Sharp-cornered utility button matching the Mem Reduct style."""

    def __init__(self, parent, label, accent=None,
                 min_w=110, min_h=26, callback=None, outline=False):
        super().__init__(parent, style=wx.BORDER_NONE)
        self._label   = label
        self._accent  = accent or BTN_BG
        self._outline = outline
        self._cb      = callback
        self._hover   = False
        self._pressed = False
        self.SetBackgroundColour(parent.GetBackgroundColour())
        self.SetMinSize((min_w, min_h))
        self.Bind(wx.EVT_PAINT,        self._paint)
        self.Bind(wx.EVT_ENTER_WINDOW, lambda _: self._s(hover=True))
        self.Bind(wx.EVT_LEAVE_WINDOW, lambda _: self._s(hover=False))
        self.Bind(wx.EVT_LEFT_DOWN,    self._down)
        self.Bind(wx.EVT_LEFT_UP,      self._up)
        self.Bind(wx.EVT_SIZE,         lambda _: self.Refresh())

    def _s(self, hover=False):
        self._hover = hover
        self.Refresh()

    def _down(self, e):
        self._pressed = True; self.Refresh(); e.Skip()

    def _up(self, e):
        if self._pressed:
            self._pressed = False; self.Refresh()
            w, h = self.GetSize()
            if self._cb and wx.Rect(0, 0, w, h).Contains(e.GetPosition()):
                self._cb()
        e.Skip()

    def _paint(self, _):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        w, h = self.GetSize()

        if self._outline:
            bg = _lighten(BG, 8) if self._hover else BG
            gc.SetBrush(gc.CreateBrush(wx.Brush(bg)))
            col = _lighten(self._accent, 30) if self._hover else self._accent
            gc.SetPen(gc.CreatePen(wx.GraphicsPenInfo(col).Width(1)))
            gc.DrawRectangle(0.5, 0.5, w - 1, h - 1)
            fg = col
        else:
            if self._pressed:
                bg = _darken(self._accent, 25)
            elif self._hover:
                bg = _lighten(self._accent, 20)
            else:
                bg = self._accent
            gc.SetBrush(gc.CreateBrush(wx.Brush(bg)))
            gc.SetPen(wx.TRANSPARENT_PEN)
            gc.DrawRectangle(0, 0, w, h)
            fg = TEXT

        gc.SetFont(gc.CreateFont(_mono(9, wx.FONTWEIGHT_BOLD), fg))
        tw, th = gc.GetTextExtent(self._label)
        gc.DrawText(self._label, (w - tw) / 2, (h - th) / 2)


# ═══════════════════════════════════════════════════════════════════════════════
#  PROFILE ROW  (compact single-line selectable row, like a list item)
# ═══════════════════════════════════════════════════════════════════════════════

class ProfileRow(wx.Panel):
    """Single-line selectable profile entry."""

    def __init__(self, parent, key, selected=False, callback=None):
        super().__init__(parent, style=wx.BORDER_NONE)
        self._key      = key
        self._selected = selected
        self._hover    = False
        self._cb       = callback
        self._color    = PROFILES[key]["color"]
        self.SetBackgroundColour(BG)
        # Measure the widest text we'll draw to set a reliable min-width
        self.SetMinSize((320, 38))
        self.Bind(wx.EVT_PAINT,        self._paint)
        self.Bind(wx.EVT_LEFT_DOWN,    lambda _: self._cb and self._cb(key))
        self.Bind(wx.EVT_ENTER_WINDOW, lambda _: self._h(True))
        self.Bind(wx.EVT_LEAVE_WINDOW, lambda _: self._h(False))
        self.Bind(wx.EVT_SIZE,         lambda _: self.Refresh())

    def _h(self, v):
        self._hover = v; self.Refresh()

    def set_selected(self, v):
        self._selected = v; self.Refresh()

    def _paint(self, _):
        dc  = wx.PaintDC(self)
        gc  = wx.GraphicsContext.Create(dc)
        w, h = self.GetSize()

        # Row background
        if self._selected:
            bg = SURFACE
        elif self._hover:
            bg = _lighten(BG, 8)
        else:
            bg = BG
        gc.SetBrush(gc.CreateBrush(wx.Brush(bg)))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)

        # Left selection bar
        bar_col = self._color if self._selected else (
            _lighten(BORDER, 10) if self._hover else BORDER)
        gc.SetBrush(gc.CreateBrush(wx.Brush(bar_col)))
        gc.DrawRectangle(0, 0, 3, h)

        # Label
        label_col = self._color if self._selected else TEXT
        gc.SetFont(gc.CreateFont(_mono(9, wx.FONTWEIGHT_BOLD), label_col))
        gc.DrawText(PROFILES[self._key]["label"], 12, 4)

        # Tagline
        gc.SetFont(gc.CreateFont(_ui(8), MUTED))
        gc.DrawText(PROFILES[self._key]["tagline"], 12, 22)

        # Bottom border
        gc.SetPen(gc.CreatePen(wx.GraphicsPenInfo(BORDER).Width(1)))
        gc.StrokeLine(0, h - 1, w, h - 1)


# ═══════════════════════════════════════════════════════════════════════════════
#  SPIN CONTROL
# ═══════════════════════════════════════════════════════════════════════════════

class UtilSpin(wx.Panel):
    """Compact monospace spin control."""

    def __init__(self, parent, min_val=0, max_val=999, initial=0):
        super().__init__(parent, style=wx.BORDER_NONE)
        self._min = min_val
        self._max = max_val
        self.SetBackgroundColour(BG)

        self._txt = wx.TextCtrl(
            self, value=str(initial),
            style=wx.TE_CENTRE | wx.BORDER_SIMPLE,
            size=(46, 22)
        )
        self._txt.SetBackgroundColour(SURFACE)
        self._txt.SetForegroundColour(TEXT)
        self._txt.SetFont(_mono(9, wx.FONTWEIGHT_BOLD))
        self._txt.Bind(wx.EVT_CHAR, self._char)

        up   = self._abtn("▲", +1)
        down = self._abtn("▼", -1)

        col = wx.BoxSizer(wx.VERTICAL)
        col.Add(up,   1, wx.EXPAND)
        col.Add(down, 1, wx.EXPAND)

        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(self._txt, 0, wx.ALIGN_CENTER_VERTICAL)
        row.Add(col, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 1)
        self.SetSizer(row)
        self.SetMinSize((68, 24))

    def _abtn(self, sym, delta):
        b = wx.Panel(self, size=(14, 11), style=wx.BORDER_NONE)
        b.SetBackgroundColour(SURFACE)
        b._hov = False

        def paint(_):
            dc = wx.PaintDC(b)
            gc = wx.GraphicsContext.Create(dc)
            bw, bh = b.GetSize()
            gc.SetBrush(gc.CreateBrush(wx.Brush(BTN_HOV if b._hov else SURFACE)))
            gc.SetPen(wx.TRANSPARENT_PEN)
            gc.DrawRectangle(0, 0, bw, bh)
            gc.SetFont(gc.CreateFont(_ui(6), MUTED))
            tw, th = gc.GetTextExtent(sym)
            gc.DrawText(sym, (bw - tw) / 2, (bh - th) / 2)

        b.Bind(wx.EVT_PAINT, paint)
        b.Bind(wx.EVT_LEFT_DOWN, lambda _: self._step(delta))
        b.Bind(wx.EVT_ENTER_WINDOW, lambda _: self._bh(b, True))
        b.Bind(wx.EVT_LEAVE_WINDOW, lambda _: self._bh(b, False))
        return b

    def _bh(self, b, v):
        b._hov = v; b.Refresh()

    def _step(self, d):
        try:
            v = max(self._min, min(self._max, int(self._txt.GetValue()) + d))
            self._txt.SetValue(str(v))
        except ValueError:
            self._txt.SetValue(str(self._min))

    def _char(self, e):
        if e.GetKeyCode() in (wx.WXK_BACK, wx.WXK_DELETE,
                               wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_TAB):
            e.Skip(); return
        if chr(e.GetKeyCode()).isdigit():
            e.Skip()

    def GetValue(self):
        try:
            return max(self._min, min(self._max, int(self._txt.GetValue())))
        except ValueError:
            return self._min


# ═══════════════════════════════════════════════════════════════════════════════
#  DRAGGABLE MIXIN  (for borderless popup)
# ═══════════════════════════════════════════════════════════════════════════════

class DraggableMixin:
    def _make_draggable(self, w):
        w.Bind(wx.EVT_LEFT_DOWN, self._dstart)
        w.Bind(wx.EVT_LEFT_UP,   self._dend)
        w.Bind(wx.EVT_MOTION,    self._dmove)
        self._dorg = None

    def _dstart(self, e):
        self._dorg = e.GetPosition()
        e.GetEventObject().CaptureMouse()

    def _dend(self, e):
        obj = e.GetEventObject()
        if obj.HasCapture(): obj.ReleaseMouse()
        self._dorg = None

    def _dmove(self, e):
        if self._dorg and e.Dragging() and e.LeftIsDown():
            self.SetPosition(self.GetPosition() + e.GetPosition() - self._dorg)


# ═══════════════════════════════════════════════════════════════════════════════
#  EXERCISE POPUP
# ═══════════════════════════════════════════════════════════════════════════════

class ExercisePopup(DraggableMixin, wx.Frame):

    def __init__(self, parent, workout):
        self._snoozed = False
        self._accent  = PROFILES[workout["profile"]]["color"]
        self._prof    = PROFILES[workout["profile"]]

        super().__init__(
            parent,
            style=(wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP | wx.NO_BORDER)
        )
        self.SetBackgroundColour(BG)
        self._build(workout)
        _fit_and_centre(self)
        self.Show()
        self.Raise()

    def _build(self, workout):
        root = _panel(self)
        vs   = wx.BoxSizer(wx.VERTICAL)

        # ── Title bar (drag handle) ────────────────────────────────────────
        tbar = _panel(root, SURFACE)
        ths  = wx.BoxSizer(wx.HORIZONTAL)

        # Accent square
        dot = wx.Panel(tbar, size=(10, 10))
        dot.SetBackgroundColour(self._accent)

        title = _lbl(tbar, f"RepScheduler  —  {self._prof['label'].upper()}",
                     8, wx.FONTWEIGHT_BOLD, MUTED)
        close = UtilBtn(tbar, "✕", BTN_BG, min_w=28, min_h=22,
                        callback=self._on_done)

        ths.Add(dot,   0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
        ths.Add(title, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 6)
        ths.AddStretchSpacer()
        ths.Add(close, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        tbar.SetSizer(ths)
        tbar.SetMinSize((-1, 30))
        self._make_draggable(tbar)
        self._make_draggable(title)

        vs.Add(tbar, 0, wx.EXPAND)
        vs.Add(_hline(root), 0, wx.EXPAND)

        # ── Exercise rows ──────────────────────────────────────────────────
        body = _panel(root)
        bvs  = wx.BoxSizer(wx.VERTICAL)

        last = workout["exercises"][-1]
        for item in workout["exercises"]:
            val_str = (f"{item['reps']} sec"
                       if item["unit"] == "seconds"
                       else f"× {item['reps']}")
            row = _panel(body, SURFACE if item is not last else SURFACE)
            rs  = wx.BoxSizer(wx.HORIZONTAL)

            name_lbl = _lbl(row, item["name"], 9, wx.FONTWEIGHT_BOLD)
            val_lbl  = _lbl(row, val_str, 11, wx.FONTWEIGHT_BOLD,
                            self._accent, mono=True)

            rs.Add(name_lbl, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
            rs.Add(val_lbl,  0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
            row.SetSizer(rs)
            row.SetMinSize((-1, 28))
            bvs.Add(row, 0, wx.EXPAND)
            bvs.Add(_hline(body), 0, wx.EXPAND)

        # Sets count row
        n       = workout["sets"]
        set_row = _panel(body, BG)
        ss      = wx.BoxSizer(wx.HORIZONTAL)
        ss.AddStretchSpacer()
        ss.Add(_lbl(set_row, f"{n} SET{'S' if n > 1 else ''}",
                    8, wx.FONTWEIGHT_BOLD, MUTED, mono=True),
               0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        set_row.SetSizer(ss)
        set_row.SetMinSize((-1, 22))
        bvs.Add(set_row, 0, wx.EXPAND)

        body.SetSizer(bvs)
        vs.Add(body, 0, wx.EXPAND)
        vs.Add(_hline(root), 0, wx.EXPAND)

        # ── Buttons ────────────────────────────────────────────────────────
        btn_row = _panel(root, SURFACE)
        bhs = wx.BoxSizer(wx.HORIZONTAL)
        bhs.Add(UtilBtn(btn_row, "SNOOZE 5 MIN", BTN_BG,
                        min_w=120, min_h=28, callback=self._on_snooze,
                        outline=True),
                1, wx.ALL, 6)
        bhs.Add(UtilBtn(btn_row, "DONE  ✓", self._accent,
                        min_w=120, min_h=28, callback=self._on_done),
                1, wx.ALL, 6)
        btn_row.SetSizer(bhs)
        vs.Add(btn_row, 0, wx.EXPAND)

        root.SetSizer(vs)
        outer = wx.BoxSizer()
        outer.Add(root, 1, wx.EXPAND)
        self.SetSizer(outer)

    def _on_done(self):
        self._snoozed = False; self.Close()

    def _on_snooze(self):
        self._snoozed = True; self.Close()

    def was_snoozed(self):
        return self._snoozed


# ═══════════════════════════════════════════════════════════════════════════════
#  SETUP WIZARD
# ═══════════════════════════════════════════════════════════════════════════════

class SetupWizard(wx.Dialog):

    def __init__(self, parent):
        super().__init__(parent, title="RepScheduler — First Time Calibration",
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.SetBackgroundColour(BG)
        self._spins    = {}
        self._rows     = {}
        self._selected = "survivor"
        self._build()
        _fit_and_centre(self)

    def _build(self):
        scroller = wx.ScrolledWindow(self, style=wx.BORDER_NONE)
        scroller.SetScrollRate(0, 12)
        scroller.SetBackgroundColour(BG)

        panel = _panel(scroller)
        vs    = wx.BoxSizer(wx.VERTICAL)

        # ── YOUR NUMBERS section ──────────────────────────────────────────
        vs.Add(_section_header(panel, "YOUR NUMBERS"), 0, wx.EXPAND)
        vs.Add(_hline(panel), 0, wx.EXPAND)

        # sub-header row
        hdr_row = _panel(panel, BG)
        hhs = wx.BoxSizer(wx.HORIZONTAL)
        hhs.Add(wx.Panel(hdr_row, size=(130, 1)), 0)  # spacer aligning with labels
        for cap in ["avg", "max"]:
            hhs.Add(_lbl(hdr_row, cap, 8, color=MUTED, mono=True),
                    0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 14)
            hhs.Add(wx.Panel(hdr_row, size=(28, 1)), 0)  # spin gap
        hdr_row.SetSizer(hhs)
        hdr_row.SetMinSize((-1, 20))
        vs.Add(hdr_row, 0, wx.EXPAND | wx.LEFT, 8)

        for key, label in [("pullups","Pull-ups"),
                            ("pushups","Push-ups"),
                            ("squats", "Squats")]:
            row = _panel(panel, SURFACE)
            rs  = wx.BoxSizer(wx.HORIZONTAL)
            rs.Add(_lbl(row, label, 9, wx.FONTWEIGHT_BOLD), 0,
                   wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
            rs.AddStretchSpacer()
            for stat in ["avg", "max"]:
                spin = UtilSpin(row, 0, 999, 0)
                self._spins[f"{key}_{stat}"] = spin
                rs.Add(spin, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 8)
            row.SetSizer(rs)
            row.SetMinSize((-1, 34))
            vs.Add(row, 0, wx.EXPAND)
            vs.Add(_hline(panel), 0, wx.EXPAND)

        vs.AddSpacer(6)

        # ── PROFILE section ───────────────────────────────────────────────
        vs.Add(_section_header(panel, "STARTING PROFILE"), 0, wx.EXPAND)
        vs.Add(_hline(panel), 0, wx.EXPAND)

        for key in PROFILE_KEYS:
            row = ProfileRow(panel, key,
                             selected=(key == self._selected),
                             callback=self._select)
            self._rows[key] = row
            vs.Add(row, 0, wx.EXPAND)

        vs.AddSpacer(6)

        # ── LET'S GO button ───────────────────────────────────────────────
        vs.Add(_hline(panel), 0, wx.EXPAND)
        btn_p = _panel(panel, SURFACE)
        bhs   = wx.BoxSizer(wx.HORIZONTAL)
        self._go_btn = UtilBtn(btn_p, "LET'S GO  →",
                               PROFILES[self._selected]["color"],
                               min_w=0, min_h=30, callback=self._ok)
        bhs.Add(self._go_btn, 1, wx.ALL, 6)
        btn_p.SetSizer(bhs)
        vs.Add(btn_p, 0, wx.EXPAND)

        panel.SetSizer(vs)
        scr_sz = wx.BoxSizer(wx.VERTICAL)
        scr_sz.Add(panel, 0, wx.EXPAND)
        scroller.SetSizer(scr_sz)
        scroller.Layout()
        scroller.FitInside()

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(scroller, 1, wx.EXPAND)
        self.SetSizer(outer)

    def _select(self, key):
        self._selected = key
        for k, r in self._rows.items():
            r.set_selected(k == key)
        self._go_btn._accent = PROFILES[key]["color"]
        self._go_btn.Refresh()

    def _ok(self):
        self.EndModal(wx.ID_OK)

    def get_fitness(self):
        return {k: s.GetValue() for k, s in self._spins.items()}

    def get_profile(self):
        return self._selected


# ═══════════════════════════════════════════════════════════════════════════════
#  SETTINGS DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class SettingsDialog(wx.Dialog):

    def __init__(self, parent, config):
        super().__init__(parent, title="RepScheduler — Settings",
                         style=wx.DEFAULT_DIALOG_STYLE)
        self._config   = config
        self._rows     = {}
        self._selected = config.get("profile", "survivor")
        self.SetBackgroundColour(BG)
        self._build()
        _fit_and_centre(self)

    def _build(self):
        scroller = wx.ScrolledWindow(self, style=wx.BORDER_NONE)
        scroller.SetScrollRate(0, 12)
        scroller.SetBackgroundColour(BG)

        panel = _panel(scroller)
        vs    = wx.BoxSizer(wx.VERTICAL)

        # ── Interval section ──────────────────────────────────────────────
        vs.Add(_section_header(panel, "REMINDER INTERVAL"), 0, wx.EXPAND)
        vs.Add(_hline(panel), 0, wx.EXPAND)

        int_row = _panel(panel, SURFACE)
        irs = wx.BoxSizer(wx.HORIZONTAL)
        irs.Add(_lbl(int_row, "Remind every", 9), 0,
                wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        self._spin = UtilSpin(int_row, 5, 240,
                               self._config.get("interval_minutes", 50))
        irs.Add(self._spin, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 10)
        irs.Add(_lbl(int_row, "minutes", 9, color=MUTED), 0,
                wx.ALIGN_CENTER_VERTICAL)
        int_row.SetSizer(irs)
        int_row.SetMinSize((-1, 34))
        vs.Add(int_row, 0, wx.EXPAND)
        vs.Add(_hline(panel), 0, wx.EXPAND)
        vs.AddSpacer(6)

        # ── Profile section ───────────────────────────────────────────────
        vs.Add(_section_header(panel, "ACTIVE PROFILE"), 0, wx.EXPAND)
        vs.Add(_hline(panel), 0, wx.EXPAND)

        cur = self._config.get("profile", "survivor")
        for key in PROFILE_KEYS:
            row = ProfileRow(panel, key,
                             selected=(key == cur),
                             callback=self._select)
            self._rows[key] = row
            vs.Add(row, 0, wx.EXPAND)

        vs.AddSpacer(6)

        # ── Re-calibrate + Save ───────────────────────────────────────────
        vs.Add(_hline(panel), 0, wx.EXPAND)
        btn_p = _panel(panel, SURFACE)
        bhs   = wx.BoxSizer(wx.HORIZONTAL)
        bhs.Add(UtilBtn(btn_p, "RECALIBRATE FITNESS", BTN_BG,
                        min_w=160, min_h=30, callback=self._refit,
                        outline=True),
                0, wx.ALL, 6)
        bhs.AddStretchSpacer()
        self._save_btn = UtilBtn(btn_p, "SAVE  ✓",
                                  PROFILES[self._selected]["color"],
                                  min_w=100, min_h=30, callback=self._save)
        bhs.Add(self._save_btn, 0, wx.ALL, 6)
        btn_p.SetSizer(bhs)
        vs.Add(btn_p, 0, wx.EXPAND)

        panel.SetSizer(vs)
        scr_sz = wx.BoxSizer(wx.VERTICAL)
        scr_sz.Add(panel, 0, wx.EXPAND)
        scroller.SetSizer(scr_sz)
        scroller.Layout()
        scroller.FitInside()

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(scroller, 1, wx.EXPAND)
        self.SetSizer(outer)

    def _select(self, key):
        self._selected = key
        for k, r in self._rows.items():
            r.set_selected(k == key)
        self._save_btn._accent = PROFILES[key]["color"]
        self._save_btn.Refresh()

    def _refit(self):
        dlg = SetupWizard(self)
        if dlg.ShowModal() == wx.ID_OK:
            self._config["fitness"] = dlg.get_fitness()
            new_prof = dlg.get_profile()
            self._config["profile"] = new_prof
            self._select(new_prof)
            save_config(self._config)
        dlg.Destroy()

    def _save(self):
        self.EndModal(wx.ID_OK)

    def get_interval(self):
        return self._spin.GetValue()

    def get_profile(self):
        return self._selected


# ═══════════════════════════════════════════════════════════════════════════════
#  SYSTEM TRAY
# ═══════════════════════════════════════════════════════════════════════════════

class RepSchedulerTrayIcon(wx.adv.TaskBarIcon):

    def __init__(self, app_frame):
        super().__init__()
        self._app = app_frame
        self.refresh_icon()
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK,
                  lambda _: self._app.trigger_popup())

    def refresh_icon(self):
        k = self._app.config.get("profile", "survivor")
        self.SetIcon(make_tray_icon(k), f"RepScheduler – {PROFILES[k]['label']}")

    def CreatePopupMenu(self):
        menu = wx.Menu()
        k    = self._app.config.get("profile", "survivor")
        m, s = divmod(self._app.remaining_seconds(), 60)
        info = menu.Append(wx.ID_ANY,
            f"Next break in {m:02d}:{s:02d}  ·  {PROFILES[k]['label']}")
        info.Enable(False)
        menu.AppendSeparator()
        t = menu.Append(wx.ID_ANY, "Test Popup Now")
        self.Bind(wx.EVT_MENU, lambda _: self._app.trigger_popup(), t)
        s2 = menu.Append(wx.ID_ANY, "Settings…")
        self.Bind(wx.EVT_MENU, lambda _: self._app.open_settings(), s2)
        menu.AppendSeparator()
        q = menu.Append(wx.ID_ANY, "Quit RepScheduler")
        self.Bind(wx.EVT_MENU, lambda _: self._app.quit(), q)
        return menu


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN FRAME
# ═══════════════════════════════════════════════════════════════════════════════

class RepSchedulerFrame(wx.Frame):

    def __init__(self):
        super().__init__(None, title="RepScheduler", size=(1, 1))
        self.config   = load_config()
        self._popup   = None
        self._timer   = None
        self._elapsed = 0
        self._target  = 0
        self.Hide()

        if self.config.get("first_run", True):
            if not self._run_setup():
                wx.CallAfter(self.Destroy)
                return

        self._tray = RepSchedulerTrayIcon(self)
        self._start_timer(self.config.get("interval_minutes", 50) * 60)

    def _run_setup(self):
        dlg    = SetupWizard(self)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            self.config["fitness"]   = dlg.get_fitness()
            self.config["profile"]   = dlg.get_profile()
            self.config["first_run"] = False
            save_config(self.config)
            dlg.Destroy()
            return True
        dlg.Destroy()
        return False

    def _start_timer(self, seconds):
        if self._timer:
            self._timer.Stop()
        self._elapsed = 0
        self._target  = max(1, seconds)
        self._timer   = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_tick, self._timer)
        self._timer.Start(1000)

    def _on_tick(self, _):
        self._elapsed += 1
        if self._elapsed >= self._target:
            self.trigger_popup()

    def remaining_seconds(self):
        return max(0, self._target - self._elapsed)

    def trigger_popup(self):
        self._elapsed = 0
        if self._popup and self._popup.IsShown():
            self._popup.Close()
        workout     = generate_workout(
            self.config.get("profile", "survivor"),
            self.config.get("fitness", {})
        )
        self._popup = ExercisePopup(self, workout)
        self._popup.Bind(wx.EVT_CLOSE, self._on_popup_close)

    def _on_popup_close(self, event):
        snoozed = self._popup.was_snoozed() if self._popup else False
        if snoozed:
            self._elapsed = max(0, self._target - 300)
        event.Skip()

    def open_settings(self):
        dlg = SettingsDialog(self, self.config)
        if dlg.ShowModal() == wx.ID_OK:
            self.config["interval_minutes"] = dlg.get_interval()
            self.config["profile"]          = dlg.get_profile()
            save_config(self.config)
            self._start_timer(self.config["interval_minutes"] * 60)
            self._tray.refresh_icon()
        dlg.Destroy()

    def quit(self):
        if self._timer:
            self._timer.Stop()
        if hasattr(self, '_tray'):
            self._tray.RemoveIcon()
            self._tray.Destroy()
        self.Destroy()
        wx.GetApp().ExitMainLoop()


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

class RepSchedulerApp(wx.App):
    def OnInit(self):
        self.SetTopWindow(RepSchedulerFrame())
        return True

if __name__ == "__main__":
    RepSchedulerApp(redirect=False).MainLoop()
