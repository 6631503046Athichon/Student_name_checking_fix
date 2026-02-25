"""
modules/schedule.py
โมดูลตารางเรียน - Design System v3.0
- Grid cells: radius 8px, padding 8px
- ครูซ้ำ: DANGER + border หนา
- Pastel colors สำหรับวิชา
- Conflict modal: radius 16px, header สีแดง
- Typography: ชื่อวิชา BODY, ชื่อครู CAPTION
- Empty state: "ยังไม่มีตารางเรียน"
"""

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from modules.icons import IconManager
from modules.pdf_utils import get_thai_font

# ==================== Design System v4.0 ====================
PRIMARY = "#3B82F6"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
NEUTRAL = "#64748B"

TEXT_H1 = "#0F172A"
TEXT_H2 = "#1E293B"
TEXT_H3 = "#334155"
TEXT_BODY = "#475569"
TEXT_CAPTION = "#94A3B8"

TABLE_HEADER_BG = "#F1F5F9"
TABLE_STRIPE = "#F8FAFC"
TABLE_BORDER = "#E2E8F0"

XS, S, M, L, XL, XXL = 4, 8, 16, 24, 32, 48
RADIUS_BUTTON = 8
RADIUS_CARD = 12
RADIUS_MODAL = 16
INPUT_BORDER = "#D1D5DB"

# Pastel colors สำหรับวิชาต่างๆ
SUBJECT_PASTELS = [
    "#DBEAFE",  # น้ำเงินอ่อน
    "#DCFCE7",  # เขียวอ่อน
    "#FEF3C7",  # เหลืองอ่อน
    "#FCE7F3",  # ชมพูอ่อน
    "#F3E8FF",  # ม่วงอ่อน
    "#E0F2FE",  # ฟ้าอ่อน
    "#FEE2E2",  # แดงอ่อน
    "#ECFDF5",  # เขียวมิ้นท์
    "#FEF9C3",  # เหลืองครีม
]

PERIOD_LABEL_BG = "#1F2937"
CELL_EMPTY_BG = "#F9FAFB"


def apply_treeview_style(tree, style_name="Custom.Treeview"):
    """สไตล์ตารางตาม Design System"""
    style = ttk.Style()
    style.theme_use("default")
    style.configure(style_name,
                    background="#FFFFFF", foreground=TEXT_BODY,
                    rowheight=40, fieldbackground="#FFFFFF",
                    borderwidth=0, font=("TH Sarabun New", 14))
    style.configure(f"{style_name}.Heading",
                    background=PRIMARY, foreground="#FFFFFF",
                    relief="flat", font=("TH Sarabun New", 14, "bold"),
                    padding=(0, 8))
    style.map(style_name,
              background=[("selected", "#DBEAFE")],
              foreground=[("selected", "#1E40AF")])
    style.map(f"{style_name}.Heading",
              background=[("active", "#1D4ED8")])
    tree.configure(style=style_name)
    tree.tag_configure("odd", background="#F8FAFC")
    tree.tag_configure("even", background="#FFFFFF")


def get_pastel_for_subject(subject_name):
    """คืนค่า pastel color ตามชื่อวิชา (hash-based)"""
    idx = hash(subject_name) % len(SUBJECT_PASTELS)
    return SUBJECT_PASTELS[idx]


class ScheduleModule:
    """โมดูลตารางเรียน - Design System v3.0"""

    def __init__(self, parent, db, update_status_callback):
        self.parent = parent
        self.db = db
        self.update_status = update_status_callback

        self.days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์"]
        self.periods = list(range(1, 9))
        self.period_times = [
            ("08:00", "09:00"), ("09:00", "10:00"),
            ("10:00", "11:00"), ("11:00", "12:00"),
            ("13:00", "14:00"), ("14:00", "15:00"),
            ("15:00", "16:00"), ("16:00", "17:00"),
        ]

        self.create_ui()

    def create_ui(self):
        """สร้าง UI
        ใช้ CTkScrollableFrame ครอบทั้งหมด เพื่อให้เลื่อนดูได้เมื่อเนื้อหาล้น
        """

        # CTkScrollableFrame ครอบเนื้อหาทั้งหมด - รองรับหน้าจอเล็ก
        self.content_frame = ctk.CTkScrollableFrame(
            self.parent,
            fg_color="transparent",
            scrollbar_button_color=NEUTRAL,
            scrollbar_button_hover_color=PRIMARY
        )
        self.content_frame.pack(fill="both", expand=True)

        self.tabview = ctk.CTkTabview(
            self.content_frame, corner_radius=RADIUS_CARD,
            fg_color="#FFFFFF", border_width=1, border_color=TABLE_BORDER,
            segmented_button_fg_color="#93C5FD",
            segmented_button_selected_color=PRIMARY,
            segmented_button_unselected_color="#93C5FD",
            segmented_button_selected_hover_color="#1D4ED8",
            segmented_button_unselected_hover_color="#60A5FA",
            text_color="#FFFFFF"
        )
        self.tabview.pack(fill="both", expand=True, padx=M, pady=M)

        self.tabview.add("มุมมองห้องเรียน")
        self.create_class_view_tab()

        self.tabview.add("มุมมองครู")
        self.create_teacher_view_tab()

        self.tabview.add("จัดการครู")
        self.create_teacher_management_tab()

        self.tabview.add("ภาระงานครู")
        self.create_workload_tab()

    def create_class_view_tab(self):
        """Tab มุมมองห้องเรียน"""

        tab = self.tabview.tab("มุมมองห้องเรียน")

        # การ์ดควบคุม: ปุ่ม action + ปุ่มเลือกห้อง
        control_card = ctk.CTkFrame(
            tab, fg_color="#F8FAFC", corner_radius=RADIUS_CARD,
            border_width=1, border_color="#E5E7EB"
        )
        control_card.pack(fill="x", padx=M, pady=(M, S))

        # แถวที่ 1: ปุ่ม action
        top_frame = ctk.CTkFrame(control_card, fg_color="transparent")
        top_frame.pack(fill="x", padx=M, pady=(M, S))

        ctk.CTkButton(
            top_frame, text="โหลดข้อมูล",
            command=self.load_class_schedule,
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            width=110, height=36,
            corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8",
            image=IconManager.get_white("download", 14), compound="left"
        ).pack(side="left", padx=(0, S))

        ctk.CTkButton(
            top_frame, text="เพิ่มคาบเรียน",
            command=self.add_schedule,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=130, height=36,
            corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=SUCCESS, text_color=SUCCESS,
            hover_color="#F0FDF4",
            image=IconManager.get("plus", 14, color=SUCCESS, dark_color=SUCCESS), compound="left"
        ).pack(side="left", padx=(0, S))

        ctk.CTkButton(
            top_frame, text="Export PDF",
            command=self.export_class_schedule_pdf,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=100, height=36,
            corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=NEUTRAL, text_color=NEUTRAL,
            hover_color="#F3F4F6",
            image=IconManager.get("file-pdf", 14, color=NEUTRAL, dark_color="#9CA3AF"), compound="left"
        ).pack(side="left")

        # แถวที่ 2: เลือกห้อง (Dropdown)
        room_frame = ctk.CTkFrame(control_card, fg_color="transparent")
        room_frame.pack(fill="x", padx=M, pady=(0, M))

        ctk.CTkLabel(
            room_frame, text="เลือกห้อง:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            text_color=TEXT_H3
        ).pack(side="left", padx=(0, S))

        self.class_var = ctk.StringVar()
        class_options = self.db.get_class_rooms()
        if class_options:
            self.class_var.set(class_options[0])
        else:
            class_options = ["ยังไม่มีห้องเรียน"]
            self.class_var.set(class_options[0])

        self.class_room_menu = ctk.CTkOptionMenu(
            room_frame, variable=self.class_var,
            values=class_options, width=160, height=36,
            fg_color="#EFF6FF", button_color="#EFF6FF", button_hover_color="#DBEAFE",
            text_color="#1E40AF", corner_radius=20,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            dropdown_fg_color="#F0F4FF", dropdown_hover_color="#DBEAFE",
            dropdown_text_color="#1E40AF",
            dropdown_font=ctk.CTkFont(family="TH Sarabun New", size=16),
            command=lambda x: self.load_class_schedule()
        )
        self.class_room_menu.pack(side="left")

        # ตาราง
        table_frame = ctk.CTkScrollableFrame(
            tab, fg_color="#F8FAFC", corner_radius=RADIUS_CARD,
            border_width=1, border_color="#E5E7EB",
            scrollbar_button_color="#D1D5DB", scrollbar_button_hover_color="#2563EB"
        )
        table_frame.pack(fill="both", expand=True, padx=M, pady=S)
        self.class_schedule_frame = table_frame

        if class_options:
            self.load_class_schedule()

    def create_teacher_view_tab(self):
        """Tab มุมมองครู"""

        tab = self.tabview.tab("มุมมองครู")

        # การ์ดควบคุม: ตัวเลือกครู + ปุ่ม action
        control_card = ctk.CTkFrame(
            tab, fg_color="#F8FAFC", corner_radius=RADIUS_CARD,
            border_width=1, border_color="#E5E7EB"
        )
        control_card.pack(fill="x", padx=M, pady=(M, S))

        top_frame = ctk.CTkFrame(control_card, fg_color="transparent")
        top_frame.pack(fill="x", padx=M, pady=M)

        ctk.CTkLabel(
            top_frame, text="เลือกครู:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            text_color=TEXT_H3
        ).pack(side="left", padx=(0, S))

        self.teacher_var = ctk.StringVar()
        self.teacher_menu = ctk.CTkOptionMenu(
            top_frame, variable=self.teacher_var,
            values=["เลือกครู"], width=280, height=36,
            fg_color="#EFF6FF", button_color="#EFF6FF", button_hover_color="#DBEAFE",
            text_color="#1E40AF", dropdown_fg_color="#F0F4FF",
            dropdown_hover_color="#DBEAFE", dropdown_text_color="#1E40AF",
            dropdown_font=ctk.CTkFont(family="TH Sarabun New", size=16),
            corner_radius=20,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            command=lambda x: self.load_teacher_schedule()
        )
        self.teacher_menu.pack(side="left", padx=(0, M))

        ctk.CTkButton(
            top_frame, text="โหลดข้อมูล",
            command=self.load_teacher_schedule,
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            width=110, height=36,
            corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8",
            image=IconManager.get_white("download", 14), compound="left"
        ).pack(side="left", padx=(0, S))

        ctk.CTkButton(
            top_frame, text="Export PDF",
            command=self.export_teacher_schedule_pdf,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=100, height=36,
            corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=NEUTRAL, text_color=NEUTRAL,
            hover_color="#F3F4F6",
            image=IconManager.get("file-pdf", 14, color=NEUTRAL, dark_color="#9CA3AF"), compound="left"
        ).pack(side="left")

        table_frame = ctk.CTkScrollableFrame(
            tab, fg_color="#F8FAFC", corner_radius=RADIUS_CARD,
            border_width=1, border_color="#E5E7EB",
            scrollbar_button_color="#D1D5DB", scrollbar_button_hover_color="#2563EB"
        )
        table_frame.pack(fill="both", expand=True, padx=M, pady=S)
        self.teacher_schedule_frame = table_frame

        self.load_teacher_list()

    def create_teacher_management_tab(self):
        """Tab จัดการครู"""

        tab = self.tabview.tab("จัดการครู")

        # การ์ดควบคุม: ปุ่ม action
        control_card = ctk.CTkFrame(
            tab, fg_color="#F8FAFC", corner_radius=RADIUS_CARD,
            border_width=1, border_color="#E5E7EB"
        )
        control_card.pack(fill="x", padx=M, pady=(M, S))

        top_frame = ctk.CTkFrame(control_card, fg_color="transparent")
        top_frame.pack(fill="x", padx=M, pady=M)

        ctk.CTkButton(
            top_frame, text="เพิ่มครู",
            command=self.add_teacher,
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            width=110, height=36,
            corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8",
            image=IconManager.get_white("user-plus", 14), compound="left"
        ).pack(side="left", padx=(0, S))

        ctk.CTkButton(
            top_frame, text="รีเฟรช",
            command=self.load_teachers,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=90, height=36,
            corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=NEUTRAL, text_color=NEUTRAL,
            hover_color="#F3F4F6",
            image=IconManager.get("rotate", 14, color=NEUTRAL, dark_color="#9CA3AF"), compound="left"
        ).pack(side="left")

        table_frame = ctk.CTkFrame(
            tab, fg_color="#FFFFFF", corner_radius=RADIUS_CARD,
            border_width=1, border_color=TABLE_BORDER
        )
        table_frame.pack(fill="both", expand=True, padx=M, pady=S)

        columns = ("teacher_id", "name", "phone")
        self.teacher_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        self.teacher_tree.heading("teacher_id", text="รหัสครู")
        self.teacher_tree.heading("name", text="ชื่อ-นามสกุล")
        self.teacher_tree.heading("phone", text="เบอร์ติดต่อ")

        self.teacher_tree.column("teacher_id", width=100, anchor="center")
        self.teacher_tree.column("name", width=300)
        self.teacher_tree.column("phone", width=150, anchor="center")

        apply_treeview_style(self.teacher_tree, "Teacher.Treeview")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.teacher_tree.yview)
        self.teacher_tree.configure(yscrollcommand=scrollbar.set)
        self.teacher_tree.pack(side="left", fill="both", expand=True, padx=(S, 0), pady=S)
        scrollbar.pack(side="right", fill="y", pady=S, padx=(0, XS))

        self.teacher_tree.bind("<Double-1>", lambda e: self.edit_teacher())

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=M, pady=(S, M))

        ctk.CTkButton(
            btn_frame, text="แก้ไข", command=self.edit_teacher,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=90, height=36, corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=PRIMARY, text_color=PRIMARY, hover_color="#EFF6FF",
            image=IconManager.get("pen-to-square", 14, color=PRIMARY, dark_color=PRIMARY), compound="left"
        ).pack(side="left", padx=(0, S))

        ctk.CTkButton(
            btn_frame, text="ลบ", command=self.delete_teacher,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=80, height=36, corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=DANGER, text_color=DANGER, hover_color="#FEF2F2",
            image=IconManager.get("trash", 14, color=DANGER, dark_color=DANGER), compound="left"
        ).pack(side="left")

        self.load_teachers()

    def create_workload_tab(self):
        """Tab ภาระงานครู"""

        tab = self.tabview.tab("ภาระงานครู")

        # การ์ดควบคุม: ปุ่ม action
        control_card = ctk.CTkFrame(
            tab, fg_color="#F8FAFC", corner_radius=RADIUS_CARD,
            border_width=1, border_color="#E5E7EB"
        )
        control_card.pack(fill="x", padx=M, pady=(M, S))

        top_frame = ctk.CTkFrame(control_card, fg_color="transparent")
        top_frame.pack(fill="x", padx=M, pady=M)

        ctk.CTkButton(
            top_frame, text="รีเฟรช",
            command=self.load_workload,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=90, height=36, corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=NEUTRAL, text_color=NEUTRAL, hover_color="#F3F4F6",
            image=IconManager.get("rotate", 14, color=NEUTRAL, dark_color="#9CA3AF"), compound="left"
        ).pack(side="left")

        table_frame = ctk.CTkFrame(
            tab, fg_color="#FFFFFF", corner_radius=RADIUS_CARD,
            border_width=1, border_color=TABLE_BORDER
        )
        table_frame.pack(fill="both", expand=True, padx=M, pady=S)

        columns = ("teacher_id", "name", "periods")
        self.workload_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        self.workload_tree.heading("teacher_id", text="รหัสครู")
        self.workload_tree.heading("name", text="ชื่อ-นามสกุล")
        self.workload_tree.heading("periods", text="จำนวนคาบ/สัปดาห์")

        self.workload_tree.column("teacher_id", width=150, anchor="center")
        self.workload_tree.column("name", width=350)
        self.workload_tree.column("periods", width=200, anchor="center")

        apply_treeview_style(self.workload_tree, "Workload.Treeview")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.workload_tree.yview)
        self.workload_tree.configure(yscrollcommand=scrollbar.set)
        self.workload_tree.pack(side="left", fill="both", expand=True, padx=(S, 0), pady=S)
        scrollbar.pack(side="right", fill="y", pady=S, padx=(0, XS))

        self.load_workload()

    # ==================== FUNCTIONS ====================

    def load_class_schedule(self):
        """โหลดตารางเรียน - Pastel cells, radius 8px, min height 60px"""

        for widget in self.class_schedule_frame.winfo_children():
            widget.destroy()

        class_room = self.class_var.get()
        if not class_room:
            ctk.CTkLabel(
                self.class_schedule_frame,
                text="กรุณาเลือกห้องเรียน",
                font=ctk.CTkFont(family="TH Sarabun New", size=16),
                text_color=TEXT_CAPTION
            ).pack(pady=XXL)
            return

        schedules = self.db.get_schedule_by_class(class_room)

        # หัวข้อ (H2)
        ctk.CTkLabel(
            self.class_schedule_frame,
            text=f"ตารางเรียนห้อง {class_room}",
            font=ctk.CTkFont(family="TH Sarabun New", size=20, weight="bold"),
            text_color=TEXT_H2
        ).grid(row=0, column=0, columnspan=6, pady=(M, S))

        # หัวคอลัมน์
        ctk.CTkLabel(
            self.class_schedule_frame, text="คาบ/วัน",
            font=ctk.CTkFont(family="TH Sarabun New", size=13, weight="bold"),
            fg_color=PERIOD_LABEL_BG, text_color="white",
            corner_radius=RADIUS_BUTTON, width=90, height=40
        ).grid(row=1, column=0, padx=2, pady=2, sticky="nsew")

        for col, day in enumerate(self.days, start=1):
            ctk.CTkLabel(
                self.class_schedule_frame, text=day,
                font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
                fg_color=PRIMARY, text_color="#FFFFFF",
                corner_radius=RADIUS_BUTTON, height=40
            ).grid(row=1, column=col, padx=2, pady=2, sticky="nsew")
            self.class_schedule_frame.grid_columnconfigure(col, weight=1)

        schedule_dict = {}
        for s in schedules:
            key = (s['day_of_week'], s['period_no'])
            schedule_dict[key] = s

        if not schedules:
            ctk.CTkLabel(
                self.class_schedule_frame,
                text="ยังไม่มีตารางเรียน กด '+ เพิ่มคาบเรียน' เพื่อเริ่มต้น",
                font=ctk.CTkFont(family="TH Sarabun New", size=16),
                text_color=TEXT_CAPTION
            ).grid(row=2, column=0, columnspan=6, pady=XXL)
            return

        for row, period in enumerate(self.periods, start=2):
            start_time, end_time = self.period_times[period - 1]
            ctk.CTkLabel(
                self.class_schedule_frame,
                text=f"คาบ {period}\n{start_time}-{end_time}",
                font=ctk.CTkFont(family="TH Sarabun New", size=12, weight="bold"),
                fg_color=PERIOD_LABEL_BG, text_color="white",
                corner_radius=RADIUS_BUTTON, height=60
            ).grid(row=row, column=0, padx=2, pady=2, sticky="nsew")

            for col, day in enumerate(self.days, start=1):
                key = (day, period)
                if key in schedule_dict:
                    s = schedule_dict[key]
                    teacher_name = f"{s['title']}{s['first_name']} {s['last_name']}"
                    fg_color = get_pastel_for_subject(s['subject_name'])

                    cell = ctk.CTkFrame(
                        self.class_schedule_frame,
                        fg_color=fg_color, corner_radius=RADIUS_BUTTON,
                        height=60
                    )
                    cell.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
                    cell.grid_propagate(False)
                    cell.pack_propagate(False)

                    ctk.CTkLabel(
                        cell, text=s['subject_name'],
                        font=ctk.CTkFont(family="TH Sarabun New", size=13, weight="bold"),
                        text_color=TEXT_H2, fg_color="transparent"
                    ).pack(anchor="w", padx=S, pady=(S, 0))

                    ctk.CTkLabel(
                        cell, text=teacher_name,
                        font=ctk.CTkFont(family="TH Sarabun New", size=11),
                        text_color=TEXT_CAPTION, fg_color="transparent"
                    ).pack(anchor="w", padx=S, pady=(0, S))

                    schedule_id = s['id']
                    cell.bind("<Button-1>", lambda e, sid=schedule_id: self.edit_schedule_entry(sid))
                    for child in cell.winfo_children():
                        child.bind("<Button-1>", lambda e, sid=schedule_id: self.edit_schedule_entry(sid))
                else:
                    ctk.CTkLabel(
                        self.class_schedule_frame, text="-",
                        font=ctk.CTkFont(family="TH Sarabun New", size=13),
                        fg_color=CELL_EMPTY_BG, text_color="#D1D5DB",
                        corner_radius=RADIUS_BUTTON, height=60
                    ).grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

        self.update_status(f"โหลดตารางห้อง {class_room} เรียบร้อย", "success")

    def load_teacher_list(self):
        """โหลดรายชื่อครู"""
        teachers = self.db.get_all_teachers()
        options = [f"{t['teacher_id']} - {t['title']}{t['first_name']} {t['last_name']}" for t in teachers]
        if options:
            self.teacher_menu.configure(values=options)
            self.teacher_var.set(options[0])
            self.load_teacher_schedule()

    def load_teacher_schedule(self):
        """โหลดตารางสอน - Pastel cells, radius 8px, min height 60px"""

        for widget in self.teacher_schedule_frame.winfo_children():
            widget.destroy()

        selected = self.teacher_var.get()
        if not selected or selected == "เลือกครู":
            return

        teacher_id = selected.split(" - ")[0]
        teacher = self.db.get_teacher_by_id(teacher_id)
        teacher_name = f"{teacher['title']}{teacher['first_name']} {teacher['last_name']}"

        schedules = self.db.get_schedule_by_teacher(teacher_id)

        ctk.CTkLabel(
            self.teacher_schedule_frame,
            text=f"ตารางสอนของครู {teacher_name}",
            font=ctk.CTkFont(family="TH Sarabun New", size=20, weight="bold"),
            text_color=TEXT_H2
        ).grid(row=0, column=0, columnspan=6, pady=(M, S))

        ctk.CTkLabel(
            self.teacher_schedule_frame, text="คาบ/วัน",
            font=ctk.CTkFont(family="TH Sarabun New", size=13, weight="bold"),
            fg_color=PERIOD_LABEL_BG, text_color="white",
            corner_radius=RADIUS_BUTTON, width=90, height=40
        ).grid(row=1, column=0, padx=2, pady=2, sticky="nsew")

        for col, day in enumerate(self.days, start=1):
            ctk.CTkLabel(
                self.teacher_schedule_frame, text=day,
                font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
                fg_color=PRIMARY, text_color="#FFFFFF",
                corner_radius=RADIUS_BUTTON, height=40
            ).grid(row=1, column=col, padx=2, pady=2, sticky="nsew")
            self.teacher_schedule_frame.grid_columnconfigure(col, weight=1)

        schedule_dict = {}
        for s in schedules:
            key = (s['day_of_week'], s['period_no'])
            schedule_dict[key] = s

        for row, period in enumerate(self.periods, start=2):
            start_time, end_time = self.period_times[period - 1]
            ctk.CTkLabel(
                self.teacher_schedule_frame,
                text=f"คาบ {period}\n{start_time}-{end_time}",
                font=ctk.CTkFont(family="TH Sarabun New", size=12, weight="bold"),
                fg_color=PERIOD_LABEL_BG, text_color="white",
                corner_radius=RADIUS_BUTTON, height=60
            ).grid(row=row, column=0, padx=2, pady=2, sticky="nsew")

            for col, day in enumerate(self.days, start=1):
                key = (day, period)
                if key in schedule_dict:
                    s = schedule_dict[key]
                    fg_color = get_pastel_for_subject(s['subject_name'])

                    cell = ctk.CTkFrame(
                        self.teacher_schedule_frame,
                        fg_color=fg_color, corner_radius=RADIUS_BUTTON,
                        height=60
                    )
                    cell.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
                    cell.grid_propagate(False)
                    cell.pack_propagate(False)

                    ctk.CTkLabel(
                        cell, text=s['subject_name'],
                        font=ctk.CTkFont(family="TH Sarabun New", size=13, weight="bold"),
                        text_color=TEXT_H2, fg_color="transparent"
                    ).pack(anchor="w", padx=S, pady=(S, 0))

                    ctk.CTkLabel(
                        cell, text=f"ห้อง {s['class_room']}",
                        font=ctk.CTkFont(family="TH Sarabun New", size=11),
                        text_color=TEXT_CAPTION, fg_color="transparent"
                    ).pack(anchor="w", padx=S, pady=(0, S))
                else:
                    ctk.CTkLabel(
                        self.teacher_schedule_frame, text="-",
                        font=ctk.CTkFont(family="TH Sarabun New", size=13),
                        fg_color=CELL_EMPTY_BG, text_color="#D1D5DB",
                        corner_radius=RADIUS_BUTTON, height=60
                    ).grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

        self.update_status(f"โหลดตารางสอน {teacher_name} เรียบร้อย", "success")

    def load_teachers(self):
        """โหลดข้อมูลครู"""
        for item in self.teacher_tree.get_children():
            self.teacher_tree.delete(item)

        teachers = self.db.get_all_teachers()
        for idx, teacher in enumerate(teachers):
            name = f"{teacher['title']}{teacher['first_name']} {teacher['last_name']}"
            tag = "odd" if idx % 2 == 0 else "even"
            self.teacher_tree.insert("", "end", values=(
                teacher['teacher_id'], name, teacher['phone'] or "-"
            ), tags=(tag,))

        self.update_status(f"โหลดข้อมูลครู {len(teachers)} คน", "success")

    def load_workload(self):
        """โหลดภาระงานครู"""
        for item in self.workload_tree.get_children():
            self.workload_tree.delete(item)

        workloads = self.db.get_teacher_workload()
        for idx, w in enumerate(workloads):
            tag = "odd" if idx % 2 == 0 else "even"
            self.workload_tree.insert("", "end", values=(
                w['teacher_id'], w['name'], f"{w['periods_per_week']} คาบ"
            ), tags=(tag,))

        self.update_status("โหลดภาระงานครูเรียบร้อย", "success")

    def add_teacher(self):
        """เพิ่มครู"""
        TeacherDialog(self.parent, self.db, None, self.load_teachers, self.update_status)

    def edit_teacher(self):
        """แก้ไขครู"""
        selected = self.teacher_tree.selection()
        if not selected:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกครูที่ต้องการแก้ไข")
            return

        teacher_id = self.teacher_tree.item(selected[0])['values'][0]
        teacher = self.db.get_teacher_by_id(teacher_id)
        if teacher:
            TeacherDialog(self.parent, self.db, teacher, self.load_teachers, self.update_status)

    def delete_teacher(self):
        """ลบครู - confirmation พร้อมชื่อ"""
        selected = self.teacher_tree.selection()
        if not selected:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกครูที่ต้องการลบ")
            return

        teacher_id = self.teacher_tree.item(selected[0])['values'][0]
        name = self.teacher_tree.item(selected[0])['values'][1]

        confirm = messagebox.askyesno("ยืนยันการลบ", f"ต้องการลบครู \"{name}\" หรือไม่?")
        if confirm:
            if self.db.delete_teacher(teacher_id):
                self.load_teachers()
                self.update_status(f"ลบครู {name} เรียบร้อย", "success")
            else:
                messagebox.showerror("ผิดพลาด", "ไม่สามารถลบครูได้")

    def add_schedule(self):
        """เพิ่มคาบเรียน"""
        class_room = self.class_var.get()
        if not class_room:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกห้องเรียน")
            return
        ScheduleDialog(
            self.parent, self.db, class_room, None,
            self.load_class_schedule, self.update_status
        )

    def edit_schedule_entry(self, schedule_id):
        """แก้ไขคาบเรียน"""
        schedules = self.db.get_all_schedules()
        schedule = next((s for s in schedules if s['id'] == schedule_id), None)
        if schedule:
            ScheduleDialog(
                self.parent, self.db, schedule['class_room'], schedule,
                self.load_class_schedule, self.update_status
            )

    def export_class_schedule_pdf(self):
        """Export ตารางเรียนห้องเรียนเป็น PDF"""

        class_room = self.class_var.get()
        if not class_room or class_room == "ยังไม่มีห้องเรียน":
            messagebox.showwarning("คำเตือน", "กรุณาเลือกห้องเรียน")
            return

        schedules = self.db.get_schedule_by_class(class_room)
        if not schedules:
            messagebox.showwarning("คำเตือน", f"ไม่มีตารางเรียนของห้อง {class_room}")
            return

        file_path = filedialog.asksaveasfilename(
            title="บันทึกไฟล์ PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"ตารางเรียน_{class_room}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        if not file_path:
            return

        try:
            font_name = get_thai_font()

            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
            elements = []
            styles = getSampleStyleSheet()

            title = Paragraph(f"ตารางเรียน ห้อง {class_room}", ParagraphStyle(
                'Title', parent=styles['Heading1'],
                fontName=font_name, fontSize=18, alignment=1
            ))
            elements.append(title)
            elements.append(Spacer(1, 0.5 * cm))

            # Build grid: days x periods
            days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์"]
            periods = list(range(1, 9))

            # Header row
            header = ["วัน/คาบ"] + [f"คาบ {p}" for p in periods]
            data = [header]

            for day in days:
                row = [day]
                for period in periods:
                    entry = next(
                        (s for s in schedules if s['day_of_week'] == day and s['period_no'] == period),
                        None
                    )
                    if entry:
                        teacher_name = f"{entry['title']}{entry['first_name']}"
                        cell_text = f"{entry['subject_name']}\n{teacher_name}"
                    else:
                        cell_text = "-"
                    row.append(cell_text)
                data.append(row)

            col_widths = [2.5 * cm] + [3 * cm] * 8
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('BACKGROUND', (0, 1), (0, -1), colors.HexColor("#EFF6FF")),
                ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor("#1E40AF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ]))

            elements.append(table)
            doc.build(elements)

            self.update_status(f"Export ตารางเรียนห้อง {class_room} สำเร็จ", "success")
            messagebox.showinfo("สำเร็จ", f"Export ตารางเรียนห้อง {class_room} เรียบร้อย")

        except Exception as e:
            self.update_status("ไม่สามารถ Export PDF ได้", "error")
            messagebox.showerror("ผิดพลาด", f"ไม่สามารถ Export PDF ได้\n{str(e)}")

    def export_teacher_schedule_pdf(self):
        """Export ตารางสอนครูเป็น PDF"""

        teacher_name = self.teacher_var.get()
        if not teacher_name or teacher_name == "เลือกครู":
            messagebox.showwarning("คำเตือน", "กรุณาเลือกครู")
            return

        # Find teacher_id from name
        teachers = self.db.get_all_teachers()
        teacher = next(
            (t for t in teachers
             if f"{t['title']}{t['first_name']} {t['last_name']}" == teacher_name),
            None
        )
        if not teacher:
            messagebox.showwarning("คำเตือน", "ไม่พบข้อมูลครู")
            return

        schedules = self.db.get_schedule_by_teacher(teacher['teacher_id'])
        if not schedules:
            messagebox.showwarning("คำเตือน", f"ไม่มีตารางสอนของ {teacher_name}")
            return

        file_path = filedialog.asksaveasfilename(
            title="บันทึกไฟล์ PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"ตารางสอน_{teacher_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        if not file_path:
            return

        try:
            font_name = get_thai_font()

            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
            elements = []
            styles = getSampleStyleSheet()

            title = Paragraph(f"ตารางสอน {teacher_name}", ParagraphStyle(
                'Title', parent=styles['Heading1'],
                fontName=font_name, fontSize=18, alignment=1
            ))
            elements.append(title)
            elements.append(Spacer(1, 0.5 * cm))

            # Build grid
            days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์"]
            periods = list(range(1, 9))

            header = ["วัน/คาบ"] + [f"คาบ {p}" for p in periods]
            data = [header]

            for day in days:
                row = [day]
                for period in periods:
                    entry = next(
                        (s for s in schedules if s['day_of_week'] == day and s['period_no'] == period),
                        None
                    )
                    if entry:
                        cell_text = f"{entry['subject_name']}\n{entry['class_room']}"
                    else:
                        cell_text = "-"
                    row.append(cell_text)
                data.append(row)

            col_widths = [2.5 * cm] + [3 * cm] * 8
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('BACKGROUND', (0, 1), (0, -1), colors.HexColor("#EFF6FF")),
                ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor("#1E40AF")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ]))

            elements.append(table)
            doc.build(elements)

            self.update_status(f"Export ตารางสอน {teacher_name} สำเร็จ", "success")
            messagebox.showinfo("สำเร็จ", f"Export ตารางสอน {teacher_name} เรียบร้อย")

        except Exception as e:
            self.update_status("ไม่สามารถ Export PDF ได้", "error")
            messagebox.showerror("ผิดพลาด", f"ไม่สามารถ Export PDF ได้\n{str(e)}")


class TeacherDialog(ctk.CTkToplevel):
    """หน้าต่างเพิ่ม/แก้ไขครู - radius 16px"""

    def __init__(self, parent, db, teacher, callback, update_status):
        super().__init__(parent)

        self.db = db
        self.teacher = teacher
        self.callback = callback
        self.update_status = update_status

        self.title("แก้ไขครู" if teacher else "เพิ่มครู")
        self.geometry("500x460")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.create_form()
        if teacher:
            self.fill_data()

    def create_form(self):
        """สร้างฟอร์ม"""

        main_frame = ctk.CTkFrame(self, corner_radius=RADIUS_MODAL,
                                  border_width=1, border_color=TABLE_BORDER)
        main_frame.pack(fill="both", expand=True, padx=M, pady=M)

        header = ctk.CTkFrame(main_frame, fg_color=PRIMARY, corner_radius=RADIUS_CARD)
        header.pack(fill="x", padx=M, pady=(M, L))

        ctk.CTkLabel(
            header,
            text="แก้ไขข้อมูลครู" if self.teacher else "เพิ่มครูใหม่",
            font=ctk.CTkFont(family="TH Sarabun New", size=16, weight="bold"),
            text_color="white"
        ).pack(pady=M)

        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(pady=M, padx=L)

        fields = [
            ("รหัสครู:", "teacher_id"),
            ("คำนำหน้า:", "title"),
            ("ชื่อ:", "first_name"),
            ("นามสกุล:", "last_name"),
            ("เบอร์ติดต่อ:", "phone"),
        ]

        for row_idx, (label, var_name) in enumerate(fields):
            ctk.CTkLabel(
                form_frame, text=label,
                font=ctk.CTkFont(family="TH Sarabun New", size=14),
                text_color=TEXT_H3
            ).grid(row=row_idx, column=0, sticky="w", pady=S, padx=(0, M))

            if var_name == "title":
                var = ctk.StringVar(value="นาย")
                setattr(self, f"{var_name}_var", var)
                ctk.CTkOptionMenu(
                    form_frame, variable=var,
                    values=["นาย", "นาง", "นางสาว"], width=250, height=36,
                    fg_color="#EFF6FF", button_color="#EFF6FF", button_hover_color="#DBEAFE",
                    text_color="#1E40AF", dropdown_fg_color="#F0F4FF",
                    dropdown_hover_color="#DBEAFE", dropdown_text_color="#1E40AF",
                    dropdown_font=ctk.CTkFont(family="TH Sarabun New", size=16),
                    corner_radius=RADIUS_BUTTON,
                    font=ctk.CTkFont(family="TH Sarabun New", size=14)
                ).grid(row=row_idx, column=1, pady=S)
            else:
                var = ctk.StringVar()
                setattr(self, f"{var_name}_var", var)
                ctk.CTkEntry(
                    form_frame, textvariable=var,
                    width=250, height=36,
                    corner_radius=RADIUS_BUTTON, border_width=1, border_color=INPUT_BORDER,
                    font=ctk.CTkFont(family="TH Sarabun New", size=14)
                ).grid(row=row_idx, column=1, pady=S)

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=L)

        ctk.CTkButton(
            btn_frame, text="บันทึก", command=self.save,
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            width=100, height=36, corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8",
            image=IconManager.get_white("floppy-disk", 14), compound="left"
        ).pack(side="left", padx=S)

        ctk.CTkButton(
            btn_frame, text="ยกเลิก", command=self.destroy,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=100, height=36, corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=NEUTRAL, text_color=NEUTRAL, hover_color="#F3F4F6",
            image=IconManager.get("xmark", 14, color=NEUTRAL, dark_color="#9CA3AF"), compound="left"
        ).pack(side="left", padx=S)

    def fill_data(self):
        """ใส่ข้อมูลเดิม"""
        self.teacher_id_var.set(self.teacher['teacher_id'])
        self.title_var.set(self.teacher['title'])
        self.first_name_var.set(self.teacher['first_name'])
        self.last_name_var.set(self.teacher['last_name'])
        self.phone_var.set(self.teacher['phone'] or "")

    def save(self):
        """บันทึก"""
        if not self.teacher_id_var.get().strip():
            messagebox.showwarning("คำเตือน", "กรุณากรอกรหัสครู")
            return
        if not self.first_name_var.get().strip():
            messagebox.showwarning("คำเตือน", "กรุณากรอกชื่อ")
            return
        if not self.last_name_var.get().strip():
            messagebox.showwarning("คำเตือน", "กรุณากรอกนามสกุล")
            return

        teacher_data = {
            'teacher_id': self.teacher_id_var.get().strip(),
            'title': self.title_var.get(),
            'first_name': self.first_name_var.get().strip(),
            'last_name': self.last_name_var.get().strip(),
            'phone': self.phone_var.get().strip() or None,
        }

        if self.teacher:
            success = self.db.update_teacher(self.teacher['teacher_id'], teacher_data)
            message = "แก้ไขข้อมูลครูเรียบร้อย"
        else:
            success = self.db.add_teacher(teacher_data)
            message = "เพิ่มครูเรียบร้อย"

        if success:
            self.update_status(message, "success")
            self.callback()
            self.destroy()
        else:
            messagebox.showerror("ผิดพลาด", "ไม่สามารถบันทึกได้")


class ScheduleDialog(ctk.CTkToplevel):
    """หน้าต่างเพิ่ม/แก้ไขตารางเรียน
    Conflict modal: radius 16px, header สีแดง (DANGER)"""

    def __init__(self, parent, db, class_room, schedule, callback, update_status):
        super().__init__(parent)

        self.db = db
        self.class_room = class_room
        self.schedule = schedule
        self.callback = callback
        self.update_status = update_status

        self.title("แก้ไขคาบเรียน" if schedule else "เพิ่มคาบเรียน")
        self.geometry("520x560")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.create_form()
        if schedule:
            self.fill_data()

    def create_form(self):
        """สร้างฟอร์ม"""

        main_frame = ctk.CTkFrame(self, corner_radius=RADIUS_MODAL,
                                  border_width=1, border_color=TABLE_BORDER)
        main_frame.pack(fill="both", expand=True, padx=M, pady=M)

        header = ctk.CTkFrame(main_frame, fg_color=PRIMARY, corner_radius=RADIUS_CARD)
        header.pack(fill="x", padx=M, pady=(M, L))

        ctk.CTkLabel(
            header,
            text=f"{'แก้ไข' if self.schedule else 'เพิ่ม'}คาบเรียน - ห้อง {self.class_room}",
            font=ctk.CTkFont(family="TH Sarabun New", size=16, weight="bold"),
            text_color="white"
        ).pack(pady=M)

        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(pady=M, padx=L)

        # วัน
        ctk.CTkLabel(form_frame, text="วัน:",
                     font=ctk.CTkFont(family="TH Sarabun New", size=14),
                     text_color=TEXT_H3).grid(row=0, column=0, sticky="w", pady=S, padx=(0, M))
        self.day_var = ctk.StringVar(value="จันทร์")
        ctk.CTkOptionMenu(
            form_frame, variable=self.day_var,
            values=["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์"],
            width=250, height=36,
            fg_color="#EFF6FF", button_color="#EFF6FF", button_hover_color="#DBEAFE",
            text_color="#1E40AF", dropdown_fg_color="#F0F4FF",
            dropdown_hover_color="#DBEAFE", dropdown_text_color="#1E40AF",
            dropdown_font=ctk.CTkFont(family="TH Sarabun New", size=16),
            corner_radius=20,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=0, column=1, pady=S)

        # คาบ
        ctk.CTkLabel(form_frame, text="คาบที่:",
                     font=ctk.CTkFont(family="TH Sarabun New", size=14),
                     text_color=TEXT_H3).grid(row=1, column=0, sticky="w", pady=S, padx=(0, M))
        self.period_var = ctk.StringVar(value="1")
        ctk.CTkOptionMenu(
            form_frame, variable=self.period_var,
            values=[str(i) for i in range(1, 9)],
            width=250, height=36,
            fg_color="#EFF6FF", button_color="#EFF6FF", button_hover_color="#DBEAFE",
            text_color="#1E40AF", dropdown_fg_color="#F0F4FF",
            dropdown_hover_color="#DBEAFE", dropdown_text_color="#1E40AF",
            dropdown_font=ctk.CTkFont(family="TH Sarabun New", size=16),
            corner_radius=20,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=1, column=1, pady=S)

        # วิชา
        ctk.CTkLabel(form_frame, text="วิชา:",
                     font=ctk.CTkFont(family="TH Sarabun New", size=14),
                     text_color=TEXT_H3).grid(row=2, column=0, sticky="w", pady=S, padx=(0, M))
        self.subject_var = ctk.StringVar()
        ctk.CTkEntry(
            form_frame, textvariable=self.subject_var,
            width=250, height=36, corner_radius=RADIUS_BUTTON,
            border_width=1, border_color=INPUT_BORDER,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=2, column=1, pady=S)

        # ครู
        ctk.CTkLabel(form_frame, text="ครูผู้สอน:",
                     font=ctk.CTkFont(family="TH Sarabun New", size=14),
                     text_color=TEXT_H3).grid(row=3, column=0, sticky="w", pady=S, padx=(0, M))
        teachers = self.db.get_all_teachers()
        teacher_options = [f"{t['teacher_id']} - {t['title']}{t['first_name']} {t['last_name']}" for t in teachers]
        self.teacher_var = ctk.StringVar()
        if teacher_options:
            self.teacher_var.set(teacher_options[0])
        ctk.CTkOptionMenu(
            form_frame, variable=self.teacher_var,
            values=teacher_options if teacher_options else ["ไม่มีครู"],
            width=250, height=36,
            fg_color="#EFF6FF", button_color="#EFF6FF", button_hover_color="#DBEAFE",
            text_color="#1E40AF", dropdown_fg_color="#F0F4FF",
            dropdown_hover_color="#DBEAFE", dropdown_text_color="#1E40AF",
            dropdown_font=ctk.CTkFont(family="TH Sarabun New", size=16),
            corner_radius=20,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=3, column=1, pady=S)

        # ห้องเรียน
        ctk.CTkLabel(form_frame, text="ห้องเรียน:",
                     font=ctk.CTkFont(family="TH Sarabun New", size=14),
                     text_color=TEXT_H3).grid(row=4, column=0, sticky="w", pady=S, padx=(0, M))
        self.room_var = ctk.StringVar()
        ctk.CTkEntry(
            form_frame, textvariable=self.room_var,
            width=250, height=36, corner_radius=RADIUS_BUTTON,
            border_width=1, border_color=INPUT_BORDER,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            placeholder_text="เช่น 301, Lab1"
        ).grid(row=4, column=1, pady=S)

        # ปุ่ม
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=L)

        ctk.CTkButton(
            btn_frame, text="บันทึก", command=self.save,
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            width=100, height=36, corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8",
            image=IconManager.get_white("floppy-disk", 14), compound="left"
        ).pack(side="left", padx=S)

        if self.schedule:
            ctk.CTkButton(
                btn_frame, text="ลบ", command=self.delete,
                font=ctk.CTkFont(family="TH Sarabun New", size=14),
                width=80, height=36, corner_radius=RADIUS_BUTTON,
                fg_color="transparent", border_width=1,
                border_color=DANGER, text_color=DANGER, hover_color="#FEF2F2",
                image=IconManager.get("trash", 14, color=DANGER, dark_color=DANGER), compound="left"
            ).pack(side="left", padx=S)

        ctk.CTkButton(
            btn_frame, text="ยกเลิก", command=self.destroy,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=100, height=36, corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=NEUTRAL, text_color=NEUTRAL, hover_color="#F3F4F6",
            image=IconManager.get("xmark", 14, color=NEUTRAL, dark_color="#9CA3AF"), compound="left"
        ).pack(side="left", padx=S)

    def fill_data(self):
        """ใส่ข้อมูลเดิม"""
        self.day_var.set(self.schedule['day_of_week'])
        self.period_var.set(str(self.schedule['period_no']))
        self.subject_var.set(self.schedule['subject_name'])
        teacher_text = f"{self.schedule['teacher_id']} - {self.schedule['title']}{self.schedule['first_name']} {self.schedule['last_name']}"
        self.teacher_var.set(teacher_text)
        self.room_var.set(self.schedule['room_no'] or "")

    def save(self):
        """บันทึก"""
        if not self.subject_var.get().strip():
            messagebox.showwarning("คำเตือน", "กรุณากรอกชื่อวิชา")
            return

        teacher_text = self.teacher_var.get()
        if not teacher_text or teacher_text == "ไม่มีครู":
            messagebox.showwarning("คำเตือน", "กรุณาเลือกครูผู้สอน")
            return

        teacher_id = teacher_text.split(" - ")[0]
        period = int(self.period_var.get())
        start_time, end_time = [
            ("08:00", "09:00"), ("09:00", "10:00"), ("10:00", "11:00"), ("11:00", "12:00"),
            ("13:00", "14:00"), ("14:00", "15:00"), ("15:00", "16:00"), ("16:00", "17:00"),
        ][period - 1]

        schedule_data = {
            'class_room': self.class_room,
            'day_of_week': self.day_var.get(),
            'period_no': period,
            'start_time': start_time, 'end_time': end_time,
            'subject_name': self.subject_var.get().strip(),
            'teacher_id': teacher_id,
            'room_no': self.room_var.get().strip() or None,
        }

        if self.schedule:
            result = self.db.update_schedule(self.schedule['id'], schedule_data)
        else:
            result = self.db.add_schedule(schedule_data)

        if result is True:
            self.update_status("บันทึกตารางเรียนเรียบร้อย", "success")
            self.callback()
            self.destroy()
        elif isinstance(result, str):
            # Conflict - แสดง error ด้วยสีแดง (DANGER)
            messagebox.showerror("ความขัดแย้ง", result)
        else:
            messagebox.showerror("ผิดพลาด", "ไม่สามารถบันทึกได้")

    def delete(self):
        """ลบคาบเรียน"""
        confirm = messagebox.askyesno("ยืนยันการลบ", "ต้องการลบคาบเรียนนี้หรือไม่?")
        if confirm:
            if self.db.delete_schedule(self.schedule['id']):
                self.update_status("ลบคาบเรียนเรียบร้อย", "success")
                self.callback()
                self.destroy()
            else:
                messagebox.showerror("ผิดพลาด", "ไม่สามารถลบได้")
