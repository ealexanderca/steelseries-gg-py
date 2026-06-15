"""
SteelSeries Auto Sonar
================================
Detects the active foreground application and automatically adjusts
SteelSeries Sonar EQ + mixer settings via its local REST API.

Requirements:
    pip install pywin32 requests pillow

Run:
    pythonw AutoSonar.py        (background / no console)
    python  AutoSonar.py        (with console for debugging)
"""

import pythoncom
import sys
import os
import json
import time
import datetime
import threading
import logging
from ctypes import wintypes
import ctypes
from pathlib import Path
from typing import Optional
import win32api
import win32con
from tkinter import messagebox
import pystray
from PIL import Image, ImageDraw
import traceback
import random
import re
import win32gui
import win32process
import psutil
from steelseries_gg_py import GG
import exceptions as GGex

# ── constants ─────────────────────────────────────────────────────────────────

APP_DIR   = Path(os.environ.get("APPDATA", "~")).expanduser() / "AutoSonar"
CONFIG_FILE  = APP_DIR / "config.json"
LOG_FILE     = APP_DIR / "AutoSonar.log"
APP_DIR.mkdir(parents=True, exist_ok=True)
PAUSE_APPS=["lockapp.exe", "logonui.exe"]
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
# ── logging ───────────────────────────────────────────────────────────────────

latest_warning = "No warnings"  # global variable

class WarningCaptureHandler(logging.Handler):
    def __init__(self,app):
        super().__init__()
        self.app = app
        
    def emit(self, record):
        global latest_warning
        if record.levelno == logging.WARNING:
            latest_warning = record.msg
            try:
                self.app.icon.update_menu()
            except Exception:
                latest_warning += "\n" + traceback.format_exc()

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

log = logging.getLogger("AutoSonar")

def log_uncaught_exception(exc_type, exc_value, exc_traceback):
    # Ignore CTRL+C
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    log.critical(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )

sys.excepthook = log_uncaught_exception

def unraisable_exception_handler(unraisable):
    log.critical(
        f"Unraisable exception: {unraisable.err_msg}",
        exc_info=(unraisable.exc_type, unraisable.exc_value, unraisable.exc_traceback),
    )

sys.unraisablehook = unraisable_exception_handler

# ── default config ────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "poll_interval_ms": 500,
    "app_detection_enabled":True,
    "coreProps_path": "",
    "profiles": {
        "default": {
            "color": ["#A94DC1","#bb78cc"],
            "description": "Default profile",
            "sonar":{
                "volume": {"all":1.0},
                "EQ": {"all":"flat","game":"Rainbow Six Siege"},
                "mute": {"all":False,}
            },
        },
    },
}

# ── config helpers ────────────────────────────────────────────────────────────

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                cfg = json.load(f)
            # Merge in any missing defaults
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception as e:
            log.warning(f"Config load error ({e}), using defaults.")
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()

def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def get_next_available_key(keys, prefix):
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
    
    used_numbers = set()
    
    for key in keys:
        match = pattern.match(key)
        if match:
            used_numbers.add(int(match.group(1)))
    
    i = 1
    while i in used_numbers:
        i += 1
    
    return f"{prefix}{i}"

# ── active window detection ───────────────────────────────────────────────────

def get_window_pid(hwnd:int) -> tuple[int, int]:
    # using this because GetWindowThreadProcessId seems to return 0 for some windows where win32process.GetWindowThreadProcessId returns the correct PID, even though they should be doing the same thing. Go figure.
    user32 = ctypes.WinDLL("user32", use_last_error=True)

    GetWindowThreadProcessId = user32.GetWindowThreadProcessId
    GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD)
    ]
    GetWindowThreadProcessId.restype = wintypes.DWORD

    pid = wintypes.DWORD()

    thread_id = GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

    return thread_id, pid.value

def get_foreground_exe() -> tuple[int | None, str | None, str | None]:
    hwnd = win32gui.GetForegroundWindow()
    _, pid = get_window_pid(hwnd)
    if not pid:
        return None, None, None
    try:
        process_name = psutil.Process(pid).name()
    except:
        process_name = "lockapp.exe"
    if process_name.lower() in PAUSE_APPS:
        return None, None, process_name.lower()
    elif process_name.lower() in ["taskmgr.exe"]:
        return None,None, None

    try:
        handle = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
            False,
            pid
        )
    except:
        return None,None, None
        

    exe_path = win32process.GetModuleFileNameEx(handle, 0)
    win32api.CloseHandle(handle)

    folder = os.path.dirname(exe_path).lower()
    exe = os.path.basename(exe_path).lower()

    return pid, folder, exe,

# ── system tray icon ──────────────────────────────────────────────────────────

def make_icon_image(color: str="#FFFFFF", border_color: str="#000000", border: int=0, scale: int =1, offsets: tuple[float, float]=(0.0, 0.0), size: int = 64) -> Image.Image:
    if isinstance(color,list):
        if len(color)>1:
            color2=color[1]
            color=color[0]
        else:
            color=color[0]
            color2=color
    else:
        color2=color
    if isinstance(border_color,list):
        border_color2=border_color[1]
        border_color=border_color[0]
    else:
        border_color2=border_color
    """Draw a simple headphones-style icon."""
    
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    inner_w = round(6*scale)
    border_w = inner_w + border * 2

    # Helper: add offset first, then scale
    def transform(coords,offsets=[0,0],expansion=0):
        x0, y0, x1, y1 = coords
        return [
            (offsets[0] - expansion + x0) * scale,
            (offsets[1] - expansion + y0) * scale,
            (offsets[0] + expansion + x1) * scale,
            (offsets[1] + expansion+ y1) * scale
        ]

    # --- BORDER ---
    d.arc(transform([8, 8, 56, 48],offsets,border),start=160, end=20,fill=border_color2,width=border_w)
    d.ellipse(transform([4, 30, 20, 54],offsets,border),fill=border_color)
    d.ellipse(transform([44, 30, 60, 54],offsets,border),fill=border_color)

    # --- MAIN SHAPE ---
    d.arc(transform([8, 8, 56, 48],offsets),start=160, end=20,fill=color2,width=inner_w)
    d.ellipse(transform([4, 30, 20, 54],offsets), fill=color)
    d.ellipse(transform([64-20, 30, 64-4, 54],offsets), fill=color)
    
    return img

def random_hex_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

# ── main logic ────────────────────────────────────────────────────────────────

class AutoSonar:
    def __init__(self):
        self.current_pid: int|None = None
        self.current_exe: Optional[str] = None
        self.running: bool = True
        self.icon: pystray._base.Icon|None = None
        self._icon_img_cache: dict = {}
        self._reload_config()
        self.gg:GG = GG(self.config["coreProps_path"])

    def _get_icon(self, profile_data:dict,profile_name:str|None) -> Image.Image:
        if profile_name not in self._icon_img_cache:
            if "color" in profile_data:
                self._icon_img_cache[profile_name]=make_icon_image(color=profile_data["color"])
            else:
                self._icon_img_cache[profile_name]= make_icon_image()
        return self._icon_img_cache[profile_name]

    def _reload_profiles(self):
        self.profile_items = []

        for name in self.config["profiles"]:

            def make_activate(n):
                def activate(icon, item):
                    self._write_profile_by_name(n)
                    self.current_profile_name=n
                    if self.icon:
                        self.icon.icon = self._get_icon(self.config["profiles"][n],n)
                        self.icon.update_menu()
                    self.app_detection_enabled=False
                return activate

            self.profile_items.append(
                pystray.MenuItem(
                    name,
                    make_activate(name),
                    checked=lambda item, n=name: self.current_profile_name == n
                )
            )
    
    def _build_menu(self) -> pystray.Menu:
        self._reload_profiles()
        return pystray.Menu(
            pystray.MenuItem(self._status_text, None, enabled=False),
            pystray.MenuItem(latest_warning, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Enable Detection",
                self.toggle_app_detection,
                checked=lambda item: self.app_detection_enabled
            ),
            pystray.MenuItem(lambda item: f"Profiles: {self.current_profile_name}", pystray.Menu(lambda:self.profile_items)),
            pystray.MenuItem("Open config folder", self._open_config_folder),
            pystray.MenuItem("Reload config", self._reload_config),
            pystray.MenuItem("Save current settings", self.save_state),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.quit),
        )

    def _status_text(self, *_) -> str:
        conn = "✓" if self.gg.sonar.isRunning else "✗ (Sonar not detected)"
        return f"Auto Sonar [{conn}]"

    def _open_config_folder(self, *_):
        os.startfile(str(APP_DIR))

    def _reload_config(self, *_):
        self.config = load_config()
        self.poll_interval = self.config.get("poll_interval_ms", 500) / 1000.0
        if "app_detection_enabled" in self.config:
            self.app_detection_enabled = self.config["app_detection_enabled"]
        self.current_profile_name:str|None = None
        self.current_exe=None
        self.current_pid=None
        self._icon_img_cache.clear()
        self._reload_profiles()
        if self.icon:
            self.icon.update_menu()

        log.info("Config reloaded.")

    def quit(self, *_):
        self.running = False
        self._quit_icon()

    def _quit_icon(self, *_):
        if self.icon:
            self.icon.stop()
        self.icon=None

    def check_restart_icon(self):
        if not self.has_started:
            self.has_started = bool(self.icon) and self.icon.visible
        elif self.icon and not self.icon.visible:
            log.info("Icon has disappeared, stopping icon")
            self._quit_icon()
            self.has_started=False
            log.info("poll_loop finished shutting down icon")

    def toggle_app_detection(self, *_):
        self.app_detection_enabled = not self.app_detection_enabled

    def _write_profile_by_name(self, profile_name: str,pid: int|None=None):
        profile_data = self.config["profiles"].get(profile_name)
        if not profile_data:
            log.warning(f"Unknown profile: {profile_name}")
            return
        log.info(f"profile '{profile_name}' (app: {self.current_exe})")
        self._write_sonar(profile_name,profile_data,pid)

    def _move_channel(self,profile_name: str, pid: int):
        profile_data = self.config["profiles"].get(profile_name)
        if not profile_data:
            return
        if pid and profile_data.get("channel"):
            if not self.gg.write_channel(profile_data.get("channel"),pid):
                log.warning(f"could not move {pid} to {profile_data["channel"]}")

    def _write_sonar(self,profile_name: str,profile_data: dict, pid: int|None=None):
        if "sonar" in profile_data:
            try:
                if not self.gg.sonar.isRunning:
                    self.gg._reinit()
                if self.gg.sonar.isRunning:
                    ok = self.gg.write_sonar(profile_data["sonar"],lambda x,y,z:log.warning(f"Failed to apply {x} value '{y}' to channel {z}"),pid=pid)
                    if ok:
                        
                        log.info(f"Sonar profile '{profile_name}' applied")
                    else:
                        log.warning(f"Failed to apply full Sonar profile '{profile_name}', Check logs for more info.")
                else:
                    log.warning(f"Could Not connect to Sonar")
            except GGex.GGError:
                log.warning(f"Sonar profile Write Failed catastophically")

    def _poll_loop(self):
        pythoncom.CoInitialize()
        self.has_started=False
        while self.running:
            time.sleep(self.poll_interval)
            
            pid, folder, exe = get_foreground_exe()
            if exe in PAUSE_APPS or not pid or not folder or not exe or pid == os.getpid():
                continue

            self.check_restart_icon()

            if not self.app_detection_enabled:
                continue

            if exe == self.current_exe:
                continue

            self.current_exe = exe
            self.current_pid = pid
            profile_name = self._match_application(folder, exe)
            
            if self.current_profile_name != profile_name:
                self._write_profile_by_name(profile_name, pid)
                self.current_profile_name = profile_name
            else:
                try:
                    self._move_channel(profile_name, pid)
                except:
                    log.warning(f"Failed to move channel for {exe} (pid {pid})")
            
            if self.icon:
                self.icon.icon = self._get_icon(self.config["profiles"][profile_name],profile_name)
                self.icon.update_menu()

    def _match_application(self, folder: str, exe: str) -> str:
        profiles = self.config["profiles"]
        matched_folders = set()
        matched_names = set()

        for name, profile in profiles.items():
            if name == "default":
                continue

            folders = profile.get("folders", [])
            names = profile.get("names", [])

            if folders==[] or any(os.path.expandvars(f).lower() in folder for f in folders):
                matched_folders.add(name)

            if names==[] or any(n in exe for n in names):
                matched_names.add(name)

        matches = matched_folders & matched_names

        return next((name for name in profiles if name in matches), "default")

    def run(self):
        log.info("Auto Sonar started. Right-click the tray icon to manage.")
        self.t = threading.Thread(target=self._poll_loop, daemon=True)
        self.t.start()
        while self.running:
            log.info("initialising tray icon...")
            self._init_icon()

    def save_state(self):
        self._reload_config()
        key=get_next_available_key(list(self.config["profiles"].keys()),"exp")
        profile={"folders":[],"names":[],"color":[random_hex_color(),random_hex_color()],"description":f"export of settings at {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"}
        profile["sonar"]=self.gg.read_sonar()
        self.config["profiles"][key]=profile
        save_config(self.config)
        log.info(f"current seetings saved to profile {key}")
        self._reload_config()

    def _init_icon(self):
        if self.icon:
            self.icon.stop()
            self.icon=None
        try:
            icon = self._get_icon(self.config["profiles"][self.current_profile_name],self.current_profile_name)
        except:
            icon=self._get_icon({},"none")
        self.icon = pystray.Icon(
            name="AutoSonar",
            icon = icon,
            title="AutoSonar",
            menu=self._build_menu(),
        )
        self.icon.run()
        log.info("icon runnning stopped")

# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "AutoSonar_SingleInstance")
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        messagebox.showinfo("Already running", "Auto Sonar is already running in the system tray.")
        sys.exit(3)

    app = AutoSonar()

    warning_handler = WarningCaptureHandler(app)
    warning_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    log.addHandler(warning_handler)

    app.run()
