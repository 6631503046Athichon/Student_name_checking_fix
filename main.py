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


# ==================== DESIGN SYSTEM ====================
# 60% Background
BG_LIGHT = "#F5F7FA"
BG_DARK = "#1A1D23"

# 30% Surface/Component
SURFACE_LIGHT = "#FFFFFF"
SURFACE_DARK = "#242830"

# 10% Accent
PRIMARY = "#2563EB"
SUCCESS = "#16A34A"
WARNING = "#D97706"
DANGER = "#DC2626"
NEUTRAL = "#6B7280"

# Typography Colors
TEXT_H1 = "#111827"
TEXT_H2 = "#1F2937"
TEXT_H3 = "#374151"
TEXT_BODY = "#374151"
TEXT_CAPTION = "#6B7280"

# Table
TABLE_HEADER_BG_LIGHT = "#F9FAFB"
TABLE_HEADER_BG_DARK = "#2D3139"
TABLE_HOVER = "#EFF6FF"
TABLE_STRIPE = "#F9FAFB"
TABLE_BORDER = "#E5E7EB"

# Spacing (8px Grid)
XS = 4
S = 8
M = 16
L = 24
XL = 32
XXL = 48

# Border Radius
RADIUS_BUTTON = 8
RADIUS_CARD = 12
RADIUS_MODAL = 16

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
        self.minsize(1200, 700)

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

        # Sidebar
        self.SIDEBAR_BG = "#1F2937"
        self.SIDEBAR_HOVER = "#374151"
        self.SIDEBAR_ACTIVE = PRIMARY

        # Header
        self.HEADER_BG = SURFACE_LIGHT

        # Text
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

        # Logo / ชื่อระบบ
        logo_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=M, pady=(L, M), sticky="ew")

        logo_label = ctk.CTkLabel(
            logo_frame,
            text="ระบบจัดการโรงเรียน",
            font=ctk.CTkFont(family="TH Sarabun New", size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        logo_label.pack(pady=(S, 0))

        version_label = ctk.CTkLabel(
            logo_frame,
            text="v3.0",
            font=ctk.CTkFont(family="TH Sarabun New", size=12),
            text_color="#9CA3AF"
        )
        version_label.pack(pady=(XS, 0))

        # เส้นแบ่ง
        separator = ctk.CTkFrame(
            self.sidebar_frame, height=1,
            fg_color="#374151"
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
                text=text,
                font=ctk.CTkFont(family="TH Sarabun New", size=16, weight="bold"),
                height=40,
                corner_radius=RADIUS_BUTTON,
                fg_color="transparent",
                text_color="#D1D5DB",
                hover_color=self.SIDEBAR_HOVER,
                border_width=0,
                anchor="w",
                command=command,
                image=icon,
                compound="left"
            )
            btn.grid(row=idx, column=0, padx=S, pady=XS, sticky="ew")
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
            font=ctk.CTkFont(family="TH Sarabun New", size=28, weight="bold"),
            text_color=TEXT_H1
        )
        self.header_title.pack(side="left", padx=L, pady=M)

        # ปุ่ม refresh (F5)
        refresh_btn = ctk.CTkButton(
            self.header_frame, text="↻", width=32, height=32,
            font=ctk.CTkFont(size=16),
            fg_color="transparent", hover_color=TABLE_BORDER,
            text_color=TEXT_CAPTION,
            command=self.refresh_current_page
        )
        refresh_btn.pack(side="left")

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
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            text_color=TEXT_H3
        )
        year_label.pack(side="left")

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
        # สีตาม type
        colors_map = {
            'success': SUCCESS,
            'error': DANGER,
            'warning': WARNING,
            'info': PRIMARY,
        }
        bg_color = colors_map.get(toast_type, PRIMARY)

        # สร้าง Toast frame
        toast = ctk.CTkFrame(
            self,
            fg_color=bg_color,
            corner_radius=RADIUS_BUTTON,
            height=44
        )

        # ข้อความ
        ctk.CTkLabel(
            toast,
            text=message,
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            text_color="#FFFFFF"
        ).pack(padx=M, pady=S)

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
            self.show_toast("เปลี่ยนเป็นโหมดมืด", "info")
        else:
            self.is_dark_mode = False
            self.sidebar_frame.configure(fg_color=self.SIDEBAR_BG)
            self.header_frame.configure(fg_color=SURFACE_LIGHT)
            self.content_frame.configure(fg_color=BG_LIGHT)
            self.header_title.configure(text_color=TEXT_H1)
            self.show_toast("เปลี่ยนเป็นโหมดสว่าง", "info")

    # ==================== NAVIGATION ====================

    def show_home(self):
        """แสดงหน้าแรก (จัดการนักเรียน)"""
        self.show_students()

    def show_students(self):
        """แสดงโมดูลจัดการนักเรียน"""
        self.current_show_func = self.show_students
        self.highlight_menu(0)
        self.create_main_content()
        self.header_title.configure(text="จัดการนักเรียน")
        StudentsModule(self.module_frame, self.db, self.update_status)

    def show_classrooms(self):
        """แสดงโมดูลจัดการห้องเรียน"""
        self.current_show_func = self.show_classrooms
        self.highlight_menu(1)
        self.create_main_content()
        self.header_title.configure(text="จัดการห้องเรียน")
        ClassroomsModule(self.module_frame, self.db, self.update_status)

    def show_attendance(self):
        """แสดงโมดูลเช็คชื่อ"""
        self.current_show_func = self.show_attendance
        self.highlight_menu(2)
        self.create_main_content()
        self.header_title.configure(text="เช็คชื่อ")
        AttendanceModule(self.module_frame, self.db, self.update_status)

    def show_health(self):
        """แสดงโมดูลสุขภาพ"""
        self.current_show_func = self.show_health
        self.highlight_menu(3)
        self.create_main_content()
        self.header_title.configure(text="สุขภาพ")
        HealthModule(self.module_frame, self.db, self.update_status)

    def show_grades(self):
        """แสดงโมดูลบันทึกเกรด"""
        self.current_show_func = self.show_grades
        self.highlight_menu(4)
        self.create_main_content()
        self.header_title.configure(text="บันทึกเกรด")
        GradesModule(self.module_frame, self.db, self.update_status)

    def show_schedule(self):
        """แสดงโมดูลตารางเรียน"""
        self.current_show_func = self.show_schedule
        self.highlight_menu(5)
        self.create_main_content()
        self.header_title.configure(text="ตารางเรียน")
        ScheduleModule(self.module_frame, self.db, self.update_status)

    def show_reports(self):
        """แสดงโมดูลรายงาน"""
        self.current_show_func = self.show_reports
        self.highlight_menu(6)
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
        self.db.close()
        self.destroy()


def main():
    """ฟังก์ชันหลักสำหรับรันโปรแกรม"""
    app = SchoolManagementApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
