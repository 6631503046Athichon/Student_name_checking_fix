"""
main.py
โปรแกรมบริหารจัดการโรงเรียน Desktop App
ใช้ CustomTkinter สำหรับ UI
Version 3.0 - Design System Refactor (60-30-10 Rule)
"""

import customtkinter as ctk
from datetime import datetime
import importlib
import os
import sys
import threading
import time

# Auto-reload imports
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

# Import database
from database.db import Database

# Import modules
from modules.students import StudentsModule
from modules.classrooms import ClassroomsModule
from modules.attendance import AttendanceModule
from modules.health import HealthModule
from modules.grades import GradesModule
from modules.schedule import ScheduleModule
from modules.reports import ReportsModule
from modules.icons import IconManager


# ==================== AUTO RELOAD ====================
class FileWatcher(FileSystemEventHandler):
    """Watch for file changes and trigger reload"""
    def __init__(self, app, paths):
        self.app = app
        self.paths = paths
        self.last_reload = 0
        self.reload_delay = 0.5  # Debounce 0.5s
    
    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.py'):
            # Check if it's in watched paths or is main.py
            for path in self.paths:
                if path in event.src_path or event.src_path.endswith('main.py'):
                    self._trigger_reload()
                    break
    
    def _trigger_reload(self):
        now = time.time()
        if now - self.last_reload < self.reload_delay:
            return
        self.last_reload = now
        # Schedule UI update on main thread
        self.app.after(100, self._do_reload)
    
    def _do_reload(self):
        if hasattr(self.app, 'current_show_func') and self.app.current_show_func:
            # Reload all modules
            for mod_name in ['modules.students', 'modules.classrooms', 'modules.attendance',
                           'modules.health', 'modules.grades', 'modules.schedule', 'modules.reports']:
                try:
                    mod = importlib.import_module(mod_name)
                    importlib.reload(mod)
                except Exception as e:
                    print(f"Reload {mod_name}: {e}")
            
            # Refresh current page
            self.app.current_show_func()
            print(f"[Auto-reload] Refreshed at {datetime.now().strftime('%H:%M:%S')}")


# ==================== DESIGN SYSTEM v4.0 ====================
# 60% Background - Modern Soft Palette
BG_LIGHT = "#F8FAFC"  # ขาวนวล
BG_DARK = "#0F172A"   # น้ำเงินเข้ม

# 30% Surface/Component
SURFACE_LIGHT = "#FFFFFF"
SURFACE_DARK = "#1E293B"

# 10% Accent - Vibrant & Balanced
PRIMARY = "#3B82F6"    # Blue สดใส
SUCCESS = "#10B981"    # Green สด
WARNING = "#F59E0B"    # Amber อบอุ่น
DANGER = "#EF4444"     # Red เข้ม
NEUTRAL = "#64748B"   # Slate

# Typography Colors - Better Contrast
TEXT_H1 = "#0F172A"    # Near black
TEXT_H2 = "#1E293B"   # Dark slate
TEXT_H3 = "#334155"   # Medium slate
TEXT_BODY = "#475569"  # Body text
TEXT_CAPTION = "#94A3B8"  # Muted

# Table - Modern Clean Look
TABLE_HEADER_BG_LIGHT = "#F1F5F9"  # Slate-100
TABLE_HEADER_BG_DARK = "#334155"
TABLE_HOVER = "#E0F2FE"  # Light blue tint
TABLE_STRIPE = "#F8FAFC"  # Very light
TABLE_BORDER = "#E2E8F0"  # Light border

# Spacing (8px Grid) - More generous
XS = 4
S = 8
M = 16
L = 24
XL = 32
XXL = 48

# Border Radius - Softer edges
RADIUS_BUTTON = 8
RADIUS_CARD = 12
RADIUS_MODAL = 16
RADIUS_INPUT = 8

# Shadows - Subtle depth
SHADOW_SM = "0 1px 2px rgba(0,0,0,0.05)"
SHADOW_MD = "0 4px 6px rgba(0,0,0,0.07)"
SHADOW_LG = "0 10px 15px rgba(0,0,0,0.1)"

# Layout
SIDEBAR_WIDTH = 220
HEADER_HEIGHT = 60
CONTENT_PADDING = 24


class SchoolManagementApp(ctk.CTk):
    """คลาสหลักของแอพพลิเคชัน - Design System v3.0"""

    def __init__(self):
        super().__init__()

        # ตั้งค่าหน้าต่างหลัก
        self.title("โปรแกรมบริหารจัดการโรงเรียน")
        self.geometry("1400x850")

        # ตั้งขนาดต่ำสุดของหน้าต่าง เพื่อไม่ให้ย่อจนเนื้อหาหาย
        self.minsize(1100, 700)

        # ตั้งค่าให้เปิดหน้าต่างตรงกลางจอ
        self.center_window()

        # ตั้งค่า theme (เริ่มต้น light mode)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # สถานะ theme
        self.is_dark_mode = False

        # ========== Design System Colors ==========
        self.PRIMARY = PRIMARY
        self.SUCCESS = SUCCESS
        self.WARNING = WARNING
        self.DANGER = DANGER
        self.NEUTRAL = NEUTRAL

        # พื้นหลังตามโหมด
        self.BG_COLOR = BG_LIGHT
        self.SURFACE_COLOR = SURFACE_LIGHT

        # Sidebar - Modern Dark Theme
        self.SIDEBAR_BG = "#0F172A"  # Slate-900
        self.SIDEBAR_HOVER = "#1E293B"  # Slate-800
        self.SIDEBAR_ACTIVE = "#3B82F6"  # Blue-500
        
        # Header - Clean white with subtle shadow
        self.HEADER_BG = "#FFFFFF"
        
        # Text - Better hierarchy
        self.TEXT_H1 = TEXT_H1
        self.TEXT_H2 = TEXT_H2
        self.TEXT_BODY = TEXT_BODY
        self.TEXT_CAPTION = TEXT_CAPTION

        # เชื่อมต่อฐานข้อมูล
        self.db = Database("school_data.db")

        # ข้อมูลปีการศึกษาปัจจุบัน
        current_year = datetime.now().year
        thai_year = current_year + 543
        self.current_academic_year = f"{thai_year}"

        # ห้องเรียนที่เลือก (เริ่มต้นไม่มี)
        self.selected_classroom = None

        # สร้าง UI
        self.create_layout()
        self.create_sidebar()
        self.create_header()
        self.create_main_content()

        # Hot reload: เก็บหน้าปัจจุบันและ module mapping
        self.current_show_func = None
        import modules.students, modules.classrooms, modules.attendance
        import modules.health, modules.grades, modules.schedule, modules.reports
        self._module_map = {
            self.show_students: modules.students,
            self.show_classrooms: modules.classrooms,
            self.show_attendance: modules.attendance,
            self.show_health: modules.health,
            self.show_grades: modules.grades,
            self.show_schedule: modules.schedule,
            self.show_reports: modules.reports,
        }
        self.bind("<F5>", self.refresh_current_page)

        # แสดงหน้าแรก (จัดการนักเรียน)
        self.show_home()
        
        # เริ่ม auto-reload file watcher
        self._start_file_watcher()
    
    def _start_file_watcher(self):
        """เริ่มต้น file watcher สำหรับ auto-reload"""
        if not WATCHDOG_AVAILABLE:
            print("[Auto-reload] watchdog not installed, using poll method")
            self._poll_for_changes()
            return
        
        project_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = os.path.join(project_dir, "modules")
        
        self.observer = Observer()
        event_handler = FileWatcher(self, [modules_dir, project_dir])
        # Watch both modules folder AND main.py
        self.observer.schedule(event_handler, modules_dir, recursive=True)
        self.observer.schedule(event_handler, project_dir, recursive=False)
        self.observer.start()
        print(f"[Auto-reload] Watching: {project_dir}")
    
    def _poll_for_changes(self):
        """Poll method if watchdog not available"""
        import glob
        
        def check():
            project_dir = os.path.dirname(os.path.abspath(__file__))
            modules_dir = os.path.join(project_dir, "modules")
            
            # Check both modules and main.py
            py_files = glob.glob(os.path.join(modules_dir, "*.py"))
            main_py = os.path.join(project_dir, "main.py")
            if os.path.exists(main_py):
                py_files.append(main_py)
            
            if not hasattr(self, '_file_times'):
                self._file_times = {f: os.path.getmtime(f) for f in py_files}
            else:
                for f in py_files:
                    mtime = os.path.getmtime(f)
                    if f in self._file_times and mtime != self._file_times[f]:
                        self._file_times[f] = mtime
                        # Reload
                        if hasattr(self, 'current_show_func') and self.current_show_func:
                            for mod_name in ['modules.students', 'modules.classrooms', 'modules.attendance',
                                           'modules.health', 'modules.grades', 'modules.schedule', 'modules.reports']:
                                try:
                                    mod = importlib.import_module(mod_name)
                                    importlib.reload(mod)
                                except:
                                    pass
                            self.current_show_func()
                            print(f"[Auto-reload] Refreshed at {datetime.now().strftime('%H:%M:%S')}")
                            break
            self.after(1000, check)
        
        check()

    def center_window(self):
        """จัดหน้าต่างให้อยู่กึ่งกลางจอ"""
        self.update_idletasks()
        width = 1400
        height = 850
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def create_layout(self):
        """สร้าง Layout หลัก: sidebar 220px, header 60px, content padding 24px"""

        # Grid configuration
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar (ซ้าย) - กว้าง 220px
        self.sidebar_frame = ctk.CTkFrame(
            self, corner_radius=0, width=SIDEBAR_WIDTH,
            fg_color=self.SIDEBAR_BG
        )
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_rowconfigure(10, weight=1)
        
        # ซ่อน sidebar ไว้ก่อน (จะแสดงหลังเลือกห้อง)
        self.sidebar_hidden = True
        self.sidebar_frame.grid_remove()
        
        # สำหรับการปรับ content เมื่อซ่อน sidebar
        self.content_frame_padding = CONTENT_PADDING

        # Header (บน) - สูง 60px
        self.header_frame = ctk.CTkFrame(
            self, corner_radius=0, height=HEADER_HEIGHT,
            fg_color=self.HEADER_BG,
            border_width=1, border_color=TABLE_BORDER
        )
        self.header_frame.grid(row=0, column=1, sticky="ew")
        self.header_frame.grid_propagate(False)

        # Main content (กลาง) - padding 24px
        self.content_frame = ctk.CTkFrame(
            self, corner_radius=0, fg_color=BG_LIGHT
        )
        self.content_frame.grid(row=1, column=1, sticky="nsew")

    def create_sidebar(self):
        """สร้าง Sidebar Navigation - กว้าง 220px ตาม Design System"""

        # Logo / ชื่อระบบ - Modern gradient look
        logo_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=M, pady=(L, M), sticky="ew")
        
        # Icon + Title
        logo_icon = ctk.CTkLabel(
            logo_frame,
            text="🎓",
            font=ctk.CTkFont(size=32)
        )
        logo_icon.pack()
        
        logo_label = ctk.CTkLabel(
            logo_frame,
            text="ระบบโรงเรียน",
            font=("Kanit", 16, "bold"),
            text_color="#F8FAFC"
        )
        logo_label.pack(pady=(S, 0))

        version_label = ctk.CTkLabel(
            logo_frame,
            text="School Management v4.0",
            font=ctk.CTkFont(family="Kanit", size=11),
            text_color="#64748B"
        )
        version_label.pack(pady=(2, 0))

        # เส้นแบ่ง
        separator = ctk.CTkFrame(
            self.sidebar_frame, height=1,
            fg_color="#334155"
        )
        separator.grid(row=1, column=0, padx=M, pady=S, sticky="ew")

        # เมนูทั้งหมด
        self.menu_buttons = []

        menus = [
            ("จัดการนักเรียน", self.show_students, "users"),
            ("จัดการห้องเรียน", self.show_classrooms, "chalkboard"),
            ("เช็คชื่อ", self.show_attendance, "clipboard-check"),
            ("สุขภาพ", self.show_health, "heart-pulse"),
            ("บันทึกเกรด", self.show_grades, "graduation-cap"),
            ("ตารางเรียน", self.show_schedule, "calendar-days"),
            ("รายงาน", self.show_reports, "chart-bar"),
        ]

        for idx, (text, command, icon_name) in enumerate(menus, start=2):
            icon = IconManager.get_sidebar(icon_name, 18)
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=f"  {text}",
                font=("Kanit", 14),
                height=42,
                corner_radius=RADIUS_BUTTON,
                fg_color="transparent",
                text_color="#CBD5E1",  # Slate-300
                hover_color="#3B82F6",  # Blue hover
                border_width=0,
                anchor="w",
                command=command,
                image=icon,
                compound="left"
            )
            btn.grid(row=idx, column=0, padx=(M, S), pady=(4, 4), sticky="ew")
            self.menu_buttons.append(btn)

        # เส้นแบ่งด้านล่าง
        separator2 = ctk.CTkFrame(
            self.sidebar_frame, height=1,
            fg_color="#374151"
        )
        separator2.grid(row=10, column=0, padx=M, pady=S, sticky="ew")

        # ปุ่ม Dark/Light Mode
        mode_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        mode_frame.grid(row=11, column=0, padx=M, pady=S, sticky="ew")

        self.mode_switch = ctk.CTkSwitch(
            mode_frame,
            text="โหมดมืด",
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            text_color="#D1D5DB",
            command=self.toggle_mode,
            onvalue="dark",
            offvalue="light"
        )
        self.mode_switch.pack(anchor="w")

    def create_header(self):
        """สร้าง Header 60px ตาม Design System"""

        # ส่วนซ้าย: ชื่อหน้า (จะอัพเดทตาม module)
        self.header_title = ctk.CTkLabel(
            self.header_frame,
            text="จัดการนักเรียน",
            font=("Kanit", 24, "bold"),
            text_color=TEXT_H1
        )
        self.header_title.pack(side="left", padx=L, pady=M)

        # ปุ่ม refresh (F5) - Modern style
        refresh_btn = ctk.CTkButton(
            self.header_frame, 
            text="⟳",
            width=36, 
            height=36,
            font=ctk.CTkFont(size=18),
            fg_color="#F1F5F9",
            hover_color="#E2E8F0",
            text_color="#475569",
            corner_radius=8,
            command=self.refresh_current_page
        )
        refresh_btn.pack(side="left", padx=(0, M))

        # ส่วนขวา: วันที่และปีการศึกษา
        right_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        right_frame.pack(side="right", padx=L, pady=M)

        # วันที่
        today = datetime.now()
        thai_date = today.strftime("%d/%m/") + str(today.year + 543)
        thai_days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
        thai_day = thai_days[today.weekday()]

        date_label = ctk.CTkLabel(
            right_frame,
            text=f"{thai_day} {thai_date}",
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            text_color=TEXT_CAPTION
        )
        date_label.pack(side="left", padx=(0, M))

        # ปีการศึกษา
        year_label = ctk.CTkLabel(
            right_frame,
            text=f"ปีการศึกษา {self.current_academic_year}",
            font=("TH Sarabun New", 14, "bold"),
            text_color=TEXT_H3
        )
        year_label.pack(side="left", padx=(0, M))

        # ห้องเรียนที่เลือก (ใน header)
        self.header_classroom_var = ctk.StringVar(value="ทุกห้อง")
        classrooms = self.db.get_class_rooms()
        classroom_options = ["ทุกห้อง"] + classrooms
        
        self.header_classroom_dropdown = ctk.CTkOptionMenu(
            right_frame,
            variable=self.header_classroom_var,
            values=classroom_options,
            width=150,
            height=32,
            font=ctk.CTkFont(family="TH Sarabun New", size=13),
            corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY,
            button_color=PRIMARY,
            button_hover_color="#1D4ED8",
            text_color="#FFFFFF",
            dropdown_fg_color=SURFACE_LIGHT,
            dropdown_hover_color=TABLE_HOVER,
            dropdown_text_color=TEXT_H1,
            command=self.on_header_classroom_change
        )
        self.header_classroom_dropdown.pack(side="left")

    def create_main_content(self):
        """สร้างพื้นที่ Main Content
        ใช้ grid layout + sticky="nsew" เพื่อให้ module_frame ขยายเต็มพื้นที่
        แต่ละโมดูลจัดการ scroll เองภายในตัว (CTkScrollableFrame ในส่วนที่เนื้อหาเยอะ)
        """

        # ลบ widget เดิมทั้งหมด (try-except สำหรับ CTkOptionMenu dropdown cleanup)
        for widget in self.content_frame.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass

        # ใช้ grid layout เพื่อให้ module_frame ขยายเต็มพื้นที่ content_frame
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # พื้นที่สำหรับโมดูล - ใช้ grid + sticky="nsew" เพื่อให้ขยายเต็มพื้นที่
        self.module_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color=SURFACE_LIGHT,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=TABLE_BORDER
        )
        self.module_frame.grid(
            row=0, column=0,
            sticky="nsew",
            padx=CONTENT_PADDING, pady=CONTENT_PADDING
        )

    def show_toast(self, message, toast_type="success"):
        """
        แสดง Toast Notification ตาม UX Rules
        toast_type: 'success' (เขียว), 'error' (แดง), 'warning' (ส้ม), 'info' (น้ำเงิน)
        แสดง 3 วินาทีแล้วหายไป ตำแหน่งล่างขวา
        """
        # สีตาม type - Modern palette
        colors_map = {
            'success': '#10B981',  # Emerald
            'error': '#EF4444',    # Red
            'warning': '#F59E0B',  # Amber
            'info': '#3B82F6',    # Blue
        }
        bg_color = colors_map.get(toast_type, PRIMARY)
        icon_map = {
            'success': '✓',
            'error': '✕',
            'warning': '⚠',
            'info': 'ℹ'
        }
        icon = icon_map.get(toast_type, '•')

        # สร้าง Toast frame
        toast = ctk.CTkFrame(
            self,
            fg_color=bg_color,
            corner_radius=RADIUS_BUTTON,
            height=48,
            width=300
        )

        # Icon + ข้อความ
        toast_content = ctk.CTkFrame(toast, fg_color="transparent")
        toast_content.pack(fill="x", padx=M, pady=S)
        
        ctk.CTkLabel(
            toast_content,
            text=f"{icon}",
            font=("Kanit", 16, "bold"),
            text_color="#FFFFFF"
        ).pack(side="left", padx=(0, S))
        
        ctk.CTkLabel(
            toast_content,
            text=message,
            font=("Kanit", 13),
            text_color="#FFFFFF"
        ).pack(side="left", fill="x", expand=True)

        # วาง Toast ที่มุมล่างขวา
        toast.place(relx=1.0, rely=1.0, x=-L, y=-L, anchor="se")

        # ลบหลัง 3 วินาที
        self.after(3000, lambda: toast.place_forget() if toast.winfo_exists() else None)

    def update_status(self, message, status_type="info"):
        """
        อัพเดทสถานะ - แสดงเป็น Toast notification
        status_type: 'success', 'error', 'warning', 'info'
        """
        self.show_toast(message, status_type)

    def on_header_classroom_change(self, selection):
        """เมื่อเปลี่ยนห้องเรียนใน header"""
        if selection == "ทุกห้อง":
            self.selected_classroom = None
        else:
            self.selected_classroom = selection
        
        # รีโหลดหน้าปัจจุบัน
        if self.current_show_func:
            self.current_show_func()

    def highlight_menu(self, index):
        """ไฮไลท์เมนูที่เลือกด้วย PRIMARY color (#2563EB)"""
        for i, btn in enumerate(self.menu_buttons):
            if i == index:
                # Active: ใช้สี PRIMARY ตาม design system
                btn.configure(
                    fg_color=PRIMARY,
                    text_color="#FFFFFF"
                )
            else:
                # Inactive: โปร่งใส
                btn.configure(
                    fg_color="transparent",
                    text_color="#D1D5DB"
                )

    def toggle_mode(self):
        """สลับโหมด Dark/Light"""
        mode = self.mode_switch.get()
        ctk.set_appearance_mode(mode)

        if mode == "dark":
            self.is_dark_mode = True
            self.sidebar_frame.configure(fg_color="#111827")
            self.header_frame.configure(fg_color=SURFACE_DARK)
            self.content_frame.configure(fg_color=BG_DARK)
            self.header_title.configure(text_color="#F9FAFB")
            self.show_toast("โหมดมืด", "info")
        else:
            self.is_dark_mode = False
            self.sidebar_frame.configure(fg_color=self.SIDEBAR_BG)
            self.header_frame.configure(fg_color=SURFACE_LIGHT)
            self.content_frame.configure(fg_color=BG_LIGHT)
            self.header_title.configure(text_color=TEXT_H1)
            self.show_toast("โหมดสว่าง", "info")

    # ==================== NAVIGATION ====================

    def show_home(self):
        """แสดงหน้าแรก (เลือกห้องเรียน)"""
        self.current_show_func = self.show_home
        self.highlight_menu(-1)  # ไม่ไฮไลต์เมนูใด
        
        # ซ่อน sidebar และ header
        self.sidebar_frame.grid_remove()
        self.sidebar_hidden = True
        self.header_frame.grid_remove()
        
        self.create_main_content()
        
        # สร้าง UI เลือกห้องเรียน
        self.create_classroom_selector()

    def create_classroom_selector(self):
        """สร้าง UI เลือกห้องเรียนสำหรับหน้าแรก - สมดุลและสวยงาม"""
        
        # ใช้ ScrollableFrame เพื่อให้เลื่อนลงได้
        scroll_frame = ctk.CTkScrollableFrame(
            self.module_frame,
            fg_color="transparent",
            scrollbar_button_color="#CBD5E1",
            scrollbar_button_hover_color=PRIMARY
        )
        scroll_frame.pack(fill="both", expand=True)
        
        # กล่องหลัก -จัดกลาง
        main_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        main_container.pack(expand=True)
        
        # Title - Modern font
        title_label = ctk.CTkLabel(
            main_container,
            text="ยินดีต้อนรับสู่ระบบจัดการโรงเรียน 🎓",
            font=("Kanit", 28, "bold"),
            text_color=TEXT_H1
        )
        title_label.pack(pady=(60, S))
        
        subtitle_label = ctk.CTkLabel(
            main_container,
            text="กรุณาเลือกห้องเรียนเพื่อเริ่มใช้งาน",
            font=ctk.CTkFont(family="Kanit", size=14),
            text_color=TEXT_CAPTION
        )
        subtitle_label.pack(pady=(0, L))
        
        # ดึงรายชื่อห้องเรียน
        classrooms = self.db.get_class_rooms()
        
        # ปุ่มสร้างห้องเรียน (อยู่ด้านบน) - สวยขึ้น
        create_btn = ctk.CTkButton(
            main_container,
            text="➕ สร้างห้องเรียนใหม่",
            font=("Kanit", 14, "bold"),
            height=48,
            corner_radius=12,
            fg_color=PRIMARY,
            border_width=0,
            text_color="#FFFFFF",
            hover_color="#2563EB",
            command=self._create_classroom_from_home
        )
        create_btn.pack(pady=(L, S))
        
        if not classrooms:
            # ถ้าไม่มีห้องเรียน - Modern empty state
            empty_card = ctk.CTkFrame(
                main_container,
                fg_color="#FEF3C7",  # Amber-100
                corner_radius=RADIUS_CARD,
                border_width=1,
                border_color="#FCD34D"  # Amber-300
            )
            empty_card.pack(pady=L)
            
            ctk.CTkLabel(
                empty_card,
                text="ยังไม่มีห้องเรียน",
                font=("TH Sarabun New", 16, "bold"),
                text_color="#991B1B"
            ).pack(pady=(M, XS))
            
            ctk.CTkLabel(
                empty_card,
                text="กรุณาสร้างห้องเรียนก่อน",
                font=ctk.CTkFont(family="Kanit", size=14),
                text_color="#B91C1C"  # Red-700
            ).pack(pady=(0, M))
            return
        
        # แสดง cards ห้องเรียน - Click to enter
        cards_container = ctk.CTkFrame(main_container, fg_color="transparent")
        cards_container.pack(pady=M)
        
        # สร้าง card สำหรับแต่ละห้อง - สวยขึ้น
        def create_classroom_card(classroom_name, row, col):
            # Main card with shadow effect
            card = ctk.CTkFrame(
                cards_container,
                fg_color="#FFFFFF",
                corner_radius=16,
                border_width=0,
                width=200,
                height=140
            )
            card.grid(row=row, column=col, padx=12, pady=12)
            card.grid_propagate(False)
            
            # Store original color
            card._original_fg = "#FFFFFF"
            
            # Top color bar
            color_bar = ctk.CTkFrame(
                card, fg_color=PRIMARY, height=8,
                corner_radius=8
            )
            color_bar.pack(fill="x", padx=12, pady=(12, 0))
            color_bar.pack_propagate(False)
            
            # Content frame
            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=16, pady=12)
            
            # Icon
            icon_label = ctk.CTkLabel(
                content, text="🏫",
                font=("Kanit", 36)
            )
            icon_label.pack()
            
            # ชื่อห้อง
            name_label = ctk.CTkLabel(
                content, text=classroom_name,
                font=("Kanit", 16, "bold"),
                text_color=TEXT_H1
            )
            name_label.pack(pady=(8, 4))
            
            # จำนวนนักเรียน
            try:
                count = self.db.count_students_by_classroom(classroom_name)
                count_label = ctk.CTkLabel(
                    content, text=f"👥 {count} คน",
                    font=("Kanit", 13),
                    text_color=TEXT_CAPTION
                )
                count_label.pack()
            except:
                pass
            
            # Hover effect
            def on_enter(e):
                card.configure(cursor="hand2")
                content.configure(fg_color="#F0F9FF")
            def on_leave(e):
                card.configure(cursor="")
                content.configure(fg_color="transparent")
            
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)
            content.bind("<Enter>", on_enter)
            content.bind("<Leave>", on_leave)
            
            # Click to enter (bind to card and content)
            for widget in [card, content, icon_label, name_label]:
                widget.bind("<Button-1>", lambda e, name=classroom_name: self._enter_classroom(name))
                widget.configure(cursor="hand2")
            
            return card
        
        # วาง cards เป็น grid 3 คอลัมน์
        for i, classroom in enumerate(classrooms):
            row = i // 3
            col = i % 3
            create_classroom_card(classroom, row, col)

    def confirm_classroom_selection(self):
        """ยืนยันการเลือกห้องเรียน (legacy - ไม่ใช้แล้ว)"""
        pass  # ไม่ใช้แล้ว ใช้ _enter_classroom แทน

    def _enter_classroom(self, classroom_name):
        """เข้าห้องเรียน directly โดยกด card"""
        self.selected_classroom = classroom_name
        
        # แสดง sidebar และ header
        self.sidebar_frame.grid()
        self.sidebar_hidden = False
        self.header_frame.grid()
        
        # อัพเดท header dropdown
        if hasattr(self, 'header_classroom_var'):
            classrooms = self.db.get_class_rooms()
            self.header_classroom_dropdown.configure(values=["ทุกห้อง"] + classrooms)
            self.header_classroom_var.set(classroom_name)
        
        self.show_toast(f"เข้าสู่ห้อง {classroom_name} แล้ว", "success")
        
        # ไปหน้าจัดการนักเรียน
        self.show_students()

    def _create_classroom_from_home(self):
        """สร้างห้องเรียนจากหน้าแรก - เรียก ClassroomsModule dialog"""
        # สร้าง modal สำหรับสร้างห้อง
        dialog = ctk.CTkToplevel(self)
        dialog.title("สร้างห้องเรียนใหม่")
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (250 // 2)
        dialog.geometry(f'400x250+{x}+{y}')
        
        # Form
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=L, pady=L)
        
        ctk.CTkLabel(
            form_frame, text="ชื่อห้องเรียน",
            font=("Kanit", 14, "bold"), text_color=TEXT_H1
        ).pack(anchor="w", pady=(0, S))
        
        name_entry = ctk.CTkEntry(
            form_frame, placeholder_text="เช่น ม.1/1",
            font=("Kanit", 14), height=44,
            corner_radius=RADIUS_INPUT
        )
        name_entry.pack(fill="x", pady=(0, M))
        name_entry.focus()
        
        ctk.CTkLabel(
            form_frame, text="ระดับชั้น",
            font=("Kanit", 14, "bold"), text_color=TEXT_H1
        ).pack(anchor="w", pady=(0, S))
        
        level_var = ctk.StringVar(value="มัธยมศึกษาตอนต้น")
        level_combo = ctk.CTkOptionMenu(
            form_frame, variable=level_var,
            values=["ประถมศึกษา", "มัธยมศึกษาตอนต้น", "มัธยมศึกษาตอนปลาย"],
            font=("Kanit", 14), height=40,
            corner_radius=RADIUS_INPUT,
            fg_color="#F8FAFC", button_color=PRIMARY,
            text_color=TEXT_H1
        )
        level_combo.pack(fill="x", pady=(0, L))
        
        def save():
            name = name_entry.get().strip()
            if not name:
                self.show_toast("กรุณากรอกชื่อห้อง", "warning")
                return
            
            level = level_var.get()
            self.db.add_class_room(name, level)
            self.show_toast(f"สร้างห้อง {name} สำเร็จ", "success")
            dialog.destroy()
            
            # กลับไปหน้าแรกเพื่ออัพเดทรายชื่อห้อง
            self.show_home()
        
        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(
            btn_frame, text="ยกเลิก",
            font=("Kanit", 14), height=40,
            fg_color="#E2E8F0", text_color=TEXT_H3,
            command=dialog.destroy
        ).pack(side="left", fill="x", expand=True, padx=(0, S))
        
        ctk.CTkButton(
            btn_frame, text="สร้างห้อง",
            font=("Kanit", 14, "bold"), height=40,
            fg_color=SUCCESS, hover_color="#059669",
            command=save
        ).pack(side="right", fill="x", expand=True)
        
        # Enter key
        dialog.bind("<Return>", lambda e: save())

    def show_students(self):
        """แสดงโมดูลจัดการนักเรียน"""
        self.current_show_func = self.show_students
        self.highlight_menu(0)
        
        # แสดง sidebar ถ้าซ่อนอยู่
        if self.sidebar_hidden:
            self.sidebar_frame.grid()
            self.sidebar_hidden = False
        
        # header กลับไปใช้ปกติ
        self.header_frame.grid(columnspan=2)
        
        self.create_main_content()
        self.header_title.configure(text="จัดการนักเรียน")
        StudentsModule(self.module_frame, self.db, self.update_status)

    def show_classrooms(self):
        """แสดงโมดูลจัดการห้องเรียน"""
        self.current_show_func = self.show_classrooms
        self.highlight_menu(1)
        
        # แสดง sidebar ถ้าซ่อนอยู่
        if self.sidebar_hidden:
            self.sidebar_frame.grid()
            self.sidebar_hidden = False
        self.header_frame.grid(columnspan=2)
        
        self.create_main_content()
        self.header_title.configure(text="จัดการห้องเรียน")
        ClassroomsModule(self.module_frame, self.db, self.update_status)

    def show_attendance(self):
        """แสดงโมดูลเช็คชื่อ"""
        self.current_show_func = self.show_attendance
        self.highlight_menu(2)
        
        # แสดง sidebar ถ้าซ่อนอยู่
        if self.sidebar_hidden:
            self.sidebar_frame.grid()
            self.sidebar_hidden = False
        self.header_frame.grid(columnspan=2)
        
        self.create_main_content()
        self.header_title.configure(text="เช็คชื่อ")
        AttendanceModule(self.module_frame, self.db, self.update_status)

    def show_health(self):
        """แสดงโมดูลสุขภาพ"""
        self.current_show_func = self.show_health
        self.highlight_menu(3)
        
        # แสดง sidebar ถ้าซ่อนอยู่
        if self.sidebar_hidden:
            self.sidebar_frame.grid()
            self.sidebar_hidden = False
        self.header_frame.grid(columnspan=2)
        
        self.create_main_content()
        self.header_title.configure(text="สุขภาพ")
        HealthModule(self.module_frame, self.db, self.update_status)

    def show_grades(self):
        """แสดงโมดูลบันทึกเกรด"""
        self.current_show_func = self.show_grades
        self.highlight_menu(4)
        
        # แสดง sidebar ถ้าซ่อนอยู่
        if self.sidebar_hidden:
            self.sidebar_frame.grid()
            self.sidebar_hidden = False
        self.header_frame.grid(columnspan=2)
        
        self.create_main_content()
        self.header_title.configure(text="บันทึกเกรด")
        GradesModule(self.module_frame, self.db, self.update_status)

    def show_schedule(self):
        """แสดงโมดูลตารางเรียน"""
        self.current_show_func = self.show_schedule
        self.highlight_menu(5)
        
        # แสดง sidebar ถ้าซ่อนอยู่
        if self.sidebar_hidden:
            self.sidebar_frame.grid()
            self.sidebar_hidden = False
        self.header_frame.grid(columnspan=2)
        
        self.create_main_content()
        self.header_title.configure(text="ตารางเรียน")
        ScheduleModule(self.module_frame, self.db, self.update_status)

    def show_reports(self):
        """แสดงโมดูลรายงาน"""
        self.current_show_func = self.show_reports
        self.highlight_menu(6)
        
        # แสดง sidebar ถ้าซ่อนอยู่
        if self.sidebar_hidden:
            self.sidebar_frame.grid()
            self.sidebar_hidden = False
        self.header_frame.grid(columnspan=2)
        
        self.create_main_content()
        self.header_title.configure(text="รายงาน")
        ReportsModule(self.module_frame, self.db, self.update_status)

    def refresh_current_page(self, event=None):
        """Hot reload - reload module แล้วแสดงหน้าปัจจุบันใหม่ (กด F5 หรือกดปุ่ม ↻)"""
        if not self.current_show_func:
            return

        global StudentsModule, ClassroomsModule, AttendanceModule, HealthModule
        global GradesModule, ScheduleModule, ReportsModule

        mod = self._module_map.get(self.current_show_func)
        if mod:
            reloaded = importlib.reload(mod)
            # อัปเดต global class reference จาก module ที่ reload แล้ว
            if hasattr(reloaded, 'StudentsModule'): StudentsModule = reloaded.StudentsModule
            if hasattr(reloaded, 'ClassroomsModule'): ClassroomsModule = reloaded.ClassroomsModule
            if hasattr(reloaded, 'AttendanceModule'): AttendanceModule = reloaded.AttendanceModule
            if hasattr(reloaded, 'HealthModule'): HealthModule = reloaded.HealthModule
            if hasattr(reloaded, 'GradesModule'): GradesModule = reloaded.GradesModule
            if hasattr(reloaded, 'ScheduleModule'): ScheduleModule = reloaded.ScheduleModule
            if hasattr(reloaded, 'ReportsModule'): ReportsModule = reloaded.ReportsModule

        self.current_show_func()
        self.show_toast("รีโหลดหน้าเรียบร้อย", "info")

    def on_closing(self):
        """ปิดโปรแกรม"""
        # หยุด file watcher
        if hasattr(self, 'observer'):
            self.observer.stop()
            self.observer.join()
        self.db.close()
        self.destroy()


def main():
    """ฟังก์ชันหลักสำหรับรันโปรแกรม"""
    app = SchoolManagementApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
