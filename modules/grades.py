"""
modules/grades.py
โมดูลบันทึกเกรด - Design System v3.0
- Grade colors: 4.0(SUCCESS), 3.5-3.0(เขียวอ่อน), 2.5-2.0(WARNING), 1.5-1.0(ส้มเข้ม), 0.0(DANGER)
- Table striped + hover
- GPA ใช้ H1 (28px bold)
- Modal transcript: 560px, radius 16px
- Empty state: "ยังไม่มีข้อมูลคะแนน"
"""

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from reportlab.lib.pagesizes import A4
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

# Grade Colors
GRADE_COLORS = {
    "4.0": SUCCESS,
    "3.5": "#22C55E",      # เขียวอ่อน
    "3.0": "#4ADE80",      # เขียวอ่อนกว่า
    "2.5": WARNING,
    "2.0": "#F59E0B",      # ส้มกลาง
    "1.5": "#EA580C",      # ส้มเข้ม
    "1.0": "#DC2626",      # แดงอ่อน
    "0.0": DANGER,
}


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


def get_grade_color(grade_str):
    """คืนค่าสีตามเกรด"""
    return GRADE_COLORS.get(grade_str, TEXT_CAPTION)


class GradesModule:
    """โมดูลบันทึกเกรด - Design System v3.0"""

    def __init__(self, parent, db, update_status_callback):
        self.parent = parent
        self.db = db
        self.update_status = update_status_callback

        self.subjects = [
            ("TH", "ภาษาไทย"), ("MATH", "คณิตศาสตร์"),
            ("SCI", "วิทยาศาสตร์"), ("SOC", "สังคมศึกษา"),
            ("HIST", "ประวัติศาสตร์"), ("PE", "สุขศึกษาและพละ"),
            ("ART", "ศิลปะ"), ("WORK", "การงานอาชีพ"),
            ("ENG", "ภาษาอังกฤษ"),
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
        self.tabview.pack(fill="both", expand=True, padx=L, pady=L)

        self.tabview.add("บันทึกเกรด")
        self.create_input_tab()

        self.tabview.add("Transcript")
        self.create_transcript_tab()

    def create_input_tab(self):
        """Tab บันทึกเกรด — Split panel: ซ้าย=รายชื่อนักเรียน, ขวา=ตารางเกรด"""

        tab = self.tabview.tab("บันทึกเกรด")
        self.selected_student_id = None
        self.student_cards = {}

        # === Main split container ===
        main_container = ctk.CTkFrame(tab, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=M, pady=M)
        main_container.columnconfigure(0, weight=1, minsize=240)
        main_container.columnconfigure(1, weight=2)
        main_container.rowconfigure(0, weight=1)

        # ==================== LEFT PANEL: Student List ====================
        left_panel = ctk.CTkFrame(
            main_container, fg_color="#FFFFFF",
            corner_radius=RADIUS_CARD, border_width=1, border_color=TABLE_BORDER
        )
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, S))

        # Room selector
        room_header = ctk.CTkFrame(left_panel, fg_color="#F8FAFC", corner_radius=0)
        room_header.pack(fill="x", padx=1, pady=(1, 0))

        room_row = ctk.CTkFrame(room_header, fg_color="transparent")
        room_row.pack(fill="x", padx=M, pady=M)

        ctk.CTkLabel(
            room_row, text="ห้อง:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            text_color=TEXT_H3
        ).pack(side="left", padx=(0, S))

        self.grade_room_var = ctk.StringVar()
        class_options = self.db.get_class_rooms()
        if class_options:
            self.grade_room_var.set(class_options[0])
        else:
            class_options = ["ยังไม่มีห้อง"]
            self.grade_room_var.set(class_options[0])

        ctk.CTkOptionMenu(
            room_row, variable=self.grade_room_var,
            values=class_options, width=140, height=34,
            fg_color="#EFF6FF", button_color="#EFF6FF", button_hover_color="#DBEAFE",
            text_color="#1E40AF", corner_radius=20,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            dropdown_fg_color="#F0F4FF", dropdown_hover_color="#DBEAFE",
            dropdown_text_color="#1E40AF",
            dropdown_font=ctk.CTkFont(family="TH Sarabun New", size=16),
            command=lambda x: self._load_students_for_room()
        ).pack(side="left", fill="x", expand=True)

        # Student list (scrollable)
        self.student_list_frame = ctk.CTkScrollableFrame(
            left_panel, fg_color="transparent",
            scrollbar_button_color="#D1D5DB", scrollbar_button_hover_color=PRIMARY
        )
        self.student_list_frame.pack(fill="both", expand=True, padx=XS, pady=(S, XS))

        # ==================== RIGHT PANEL: Grades ====================
        right_panel = ctk.CTkFrame(
            main_container, fg_color="#FFFFFF",
            corner_radius=RADIUS_CARD, border_width=1, border_color=TABLE_BORDER
        )
        right_panel.grid(row=0, column=1, sticky="nsew")

        # Right header: student name + year/semester
        right_header = ctk.CTkFrame(right_panel, fg_color="#F8FAFC", corner_radius=0)
        right_header.pack(fill="x", padx=1, pady=(1, 0))

        header_row = ctk.CTkFrame(right_header, fg_color="transparent")
        header_row.pack(fill="x", padx=M, pady=M)

        self.selected_student_label = ctk.CTkLabel(
            header_row, text="เลือกนักเรียนจากรายชื่อด้านซ้าย",
            font=ctk.CTkFont(family="TH Sarabun New", size=15, weight="bold"),
            text_color=TEXT_H2
        )
        self.selected_student_label.pack(side="left", padx=(0, M))

        ctk.CTkLabel(
            header_row, text="ปี:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            text_color=TEXT_BODY
        ).pack(side="left", padx=(0, XS))

        current_year = datetime.now().year + 543
        self.year_var = ctk.StringVar(value=str(current_year))
        ctk.CTkEntry(
            header_row, textvariable=self.year_var,
            width=70, height=34, corner_radius=RADIUS_BUTTON,
            border_width=1, border_color=INPUT_BORDER,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, S))

        ctk.CTkLabel(
            header_row, text="ภาค:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            text_color=TEXT_BODY
        ).pack(side="left", padx=(0, XS))

        self.semester_var = ctk.StringVar(value="1")
        ctk.CTkOptionMenu(
            header_row, variable=self.semester_var,
            values=["1", "2"], width=55, height=34,
            fg_color="#EFF6FF", button_color="#EFF6FF", button_hover_color="#DBEAFE",
            text_color="#1E40AF", dropdown_fg_color="#F0F4FF",
            dropdown_hover_color="#DBEAFE", dropdown_text_color="#1E40AF",
            dropdown_font=ctk.CTkFont(family="TH Sarabun New", size=16),
            corner_radius=20,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            command=lambda x: self.load_grades()
        ).pack(side="left", padx=(0, S))

        ctk.CTkButton(
            header_row, text="โหลด",
            command=self.load_grades,
            font=ctk.CTkFont(family="TH Sarabun New", size=13, weight="bold"),
            width=70, height=34,
            corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8",
            image=IconManager.get_white("download", 12), compound="left"
        ).pack(side="left")

        # Grade table
        table_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=S, pady=(S, 0))

        columns = ("subject_code", "subject_name", "score", "grade")
        self.grade_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)

        self.grade_tree.heading("subject_code", text="รหัสวิชา")
        self.grade_tree.heading("subject_name", text="ชื่อวิชา")
        self.grade_tree.heading("score", text="คะแนน")
        self.grade_tree.heading("grade", text="เกรด")

        self.grade_tree.column("subject_code", width=80, anchor="center")
        self.grade_tree.column("subject_name", width=180)
        self.grade_tree.column("score", width=80, anchor="center")
        self.grade_tree.column("grade", width=80, anchor="center")

        apply_treeview_style(self.grade_tree, "Grade.Treeview")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.grade_tree.yview)
        self.grade_tree.configure(yscrollcommand=scrollbar.set)
        self.grade_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.grade_tree.bind("<Double-1>", lambda e: self.edit_grade())

        # Buttons
        btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=M, pady=S)

        ctk.CTkButton(
            btn_frame, text="บันทึกคะแนน",
            command=self.add_grade,
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            width=130, height=34,
            corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8",
            image=IconManager.get_white("plus", 14), compound="left"
        ).pack(side="left", padx=(0, S))

        ctk.CTkButton(
            btn_frame, text="แก้ไข",
            command=self.edit_grade,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=80, height=34,
            corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=PRIMARY, text_color=PRIMARY,
            hover_color="#EFF6FF",
            image=IconManager.get("pen-to-square", 14, color=PRIMARY, dark_color=PRIMARY), compound="left"
        ).pack(side="left")

        # เกณฑ์เกรด
        ctk.CTkLabel(
            right_panel,
            text="เกณฑ์: 80+=4.0 | 75+=3.5 | 70+=3.0 | 65+=2.5 | 60+=2.0 | 55+=1.5 | 50+=1.0 | <50=0.0",
            font=ctk.CTkFont(family="TH Sarabun New", size=11),
            text_color=TEXT_CAPTION
        ).pack(pady=(0, S))

        # Load initial data
        self._load_students_for_room()

    def create_transcript_tab(self):
        """Tab Transcript"""

        tab = self.tabview.tab("Transcript")

        # === Control Card (white) ===
        control_card = ctk.CTkFrame(
            tab, fg_color="#F8FAFC",
            corner_radius=RADIUS_CARD, border_width=1, border_color=TABLE_BORDER
        )
        control_card.pack(fill="x", padx=M, pady=(M, S))

        top_frame = ctk.CTkFrame(control_card, fg_color="transparent")
        top_frame.pack(fill="x", padx=M, pady=(M, M))

        ctk.CTkLabel(
            top_frame, text="เลือกนักเรียน:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            text_color=TEXT_H3
        ).pack(side="left", padx=(0, S))

        self.transcript_student_var = ctk.StringVar()
        self.transcript_student_menu = ctk.CTkOptionMenu(
            top_frame, variable=self.transcript_student_var,
            values=["เลือกนักเรียน"], width=280, height=36,
            fg_color="#EFF6FF", button_color="#EFF6FF", button_hover_color="#DBEAFE",
            text_color="#1E40AF", dropdown_fg_color="#F0F4FF",
            dropdown_hover_color="#DBEAFE", dropdown_text_color="#1E40AF",
            dropdown_font=ctk.CTkFont(family="TH Sarabun New", size=16),
            corner_radius=20,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        self.transcript_student_menu.pack(side="left", padx=(0, M))

        ctk.CTkButton(
            top_frame, text="ดู Transcript",
            command=self.show_transcript,
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            width=130, height=36,
            corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8",
            image=IconManager.get_white("file-lines", 14), compound="left"
        ).pack(side="left", padx=(0, S))

        # SECONDARY
        ctk.CTkButton(
            top_frame, text="Export PDF",
            command=self.export_transcript_pdf,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=110, height=36,
            corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=NEUTRAL, text_color=NEUTRAL,
            hover_color="#F3F4F6",
            image=IconManager.get("file-pdf", 14, color=NEUTRAL, dark_color="#9CA3AF"), compound="left"
        ).pack(side="left")

        self.transcript_frame = ctk.CTkScrollableFrame(
            tab, fg_color="#F8FAFC",
            corner_radius=RADIUS_CARD, border_width=1, border_color=TABLE_BORDER,
            scrollbar_button_color="#D1D5DB", scrollbar_button_hover_color=PRIMARY
        )
        self.transcript_frame.pack(fill="both", expand=True, padx=M, pady=S)

        # Empty state
        ctk.CTkLabel(
            self.transcript_frame,
            text="ยังไม่มีข้อมูลคะแนน",
            font=ctk.CTkFont(family="TH Sarabun New", size=16),
            text_color=TEXT_CAPTION
        ).pack(pady=XXL)

        self.load_student_list_for_transcript()

    # ==================== FUNCTIONS ====================

    def _load_students_for_room(self):
        """โหลดรายชื่อนักเรียนตามห้อง"""
        # Clear existing cards
        for widget in self.student_list_frame.winfo_children():
            widget.destroy()
        self.student_cards = {}

        room = self.grade_room_var.get()
        if not room or room == "ยังไม่มีห้อง":
            return

        students = self.db.get_all_students(class_room=room)
        if not students:
            ctk.CTkLabel(
                self.student_list_frame,
                text="ไม่มีนักเรียนในห้องนี้",
                font=ctk.CTkFont(family="TH Sarabun New", size=14),
                text_color=TEXT_CAPTION
            ).pack(pady=L)
            return

        for student in students:
            sid = student['student_id']
            name = f"{student['title']}{student['first_name']} {student['last_name']}"

            card = ctk.CTkFrame(
                self.student_list_frame, fg_color="#FFFFFF",
                corner_radius=RADIUS_BUTTON, border_width=1, border_color=TABLE_BORDER,
                height=44, cursor="hand2"
            )
            card.pack(fill="x", pady=(0, XS))
            card.pack_propagate(False)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=S, pady=XS)

            id_label = ctk.CTkLabel(
                inner, text=sid,
                font=ctk.CTkFont(family="TH Sarabun New", size=12),
                text_color=TEXT_CAPTION, width=50
            )
            id_label.pack(side="left")

            name_label = ctk.CTkLabel(
                inner, text=name,
                font=ctk.CTkFont(family="TH Sarabun New", size=14),
                text_color=TEXT_BODY, anchor="w"
            )
            name_label.pack(side="left", fill="x", expand=True)

            self.student_cards[sid] = card

            # Bind click on card and all children
            for widget in [card, inner, id_label, name_label]:
                widget.bind("<Button-1>", lambda e, s=sid: self._select_student(s))

        # Auto-select first student
        first_id = students[0]['student_id']
        self._select_student(first_id)

    def _select_student(self, student_id):
        """เลือกนักเรียนจาก card — highlight + โหลดเกรด"""
        self.selected_student_id = student_id

        # Update card highlights
        for sid, card in self.student_cards.items():
            if sid == student_id:
                card.configure(fg_color="#EFF6FF", border_color=PRIMARY)
            else:
                card.configure(fg_color="#FFFFFF", border_color=TABLE_BORDER)

        # Update header label
        student = self.db.get_student_by_id(student_id)
        if student:
            name = f"{student['title']}{student['first_name']} {student['last_name']}"
            self.selected_student_label.configure(text=f"{student_id} - {name}")

        self.load_grades()

    def load_student_list_for_transcript(self):
        """โหลดรายชื่อ Transcript"""
        students = self.db.get_all_students()
        options = [f"{s['student_id']} - {s['title']}{s['first_name']} {s['last_name']}" for s in students]
        if options:
            self.transcript_student_menu.configure(values=options)
            self.transcript_student_var.set(options[0])

    def load_grades(self):
        """โหลดเกรด"""
        for item in self.grade_tree.get_children():
            self.grade_tree.delete(item)

        student_id = self.selected_student_id
        if not student_id:
            return

        year = self.year_var.get()
        semester = self.semester_var.get()

        grades = self.db.get_grades(student_id, year, semester)
        grade_dict = {g['subject_code']: g for g in grades}

        for idx, (code, name) in enumerate(self.subjects):
            if code in grade_dict:
                grade = grade_dict[code]
                score = grade['score'] if grade['score'] is not None else "-"
                grade_val = grade['grade'] if grade['grade'] else "-"
            else:
                score = "-"
                grade_val = "-"

            tag = "odd" if idx % 2 == 0 else "even"
            self.grade_tree.insert("", "end", values=(code, name, score, grade_val), tags=(tag,))

        self.update_status("โหลดข้อมูลเกรดเรียบร้อย", "success")

    def add_grade(self):
        """เพิ่มคะแนน"""
        if not self.selected_student_id:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกนักเรียน")
            return

        student_id = self.selected_student_id
        GradeDialog(
            self.parent, self.db, student_id,
            self.year_var.get(), self.semester_var.get(),
            self.subjects, None, self.load_grades, self.update_status
        )

    def edit_grade(self):
        """แก้ไขคะแนน"""
        selected_tree = self.grade_tree.selection()
        if not selected_tree:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกวิชาที่ต้องการแก้ไข")
            return

        if not self.selected_student_id:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกนักเรียน")
            return

        student_id = self.selected_student_id
        values = self.grade_tree.item(selected_tree[0])['values']
        subject_code = values[0]

        grades = self.db.get_grades(student_id, self.year_var.get(), self.semester_var.get())
        current_grade = next((g for g in grades if g['subject_code'] == subject_code), None)

        GradeDialog(
            self.parent, self.db, student_id,
            self.year_var.get(), self.semester_var.get(),
            self.subjects, current_grade, self.load_grades, self.update_status
        )

    def show_transcript(self):
        """แสดง Transcript - GPA H1 (28px bold)"""

        for widget in self.transcript_frame.winfo_children():
            widget.destroy()

        selected = self.transcript_student_var.get()
        if not selected or selected == "เลือกนักเรียน":
            messagebox.showwarning("คำเตือน", "กรุณาเลือกนักเรียน")
            return

        student_id = selected.split(" - ")[0]
        student = self.db.get_student_by_id(student_id)
        transcript_data = self.db.get_transcript(student_id)

        if not transcript_data:
            ctk.CTkLabel(
                self.transcript_frame,
                text="ยังไม่มีข้อมูลคะแนน",
                font=ctk.CTkFont(family="TH Sarabun New", size=16),
                text_color=TEXT_CAPTION
            ).pack(pady=XXL)
            return

        name = f"{student['title']}{student['first_name']} {student['last_name']}"

        # Header (H2)
        ctk.CTkLabel(
            self.transcript_frame,
            text=f"Transcript - {name}",
            font=ctk.CTkFont(family="TH Sarabun New", size=20, weight="bold"),
            text_color=TEXT_H2
        ).pack(pady=(M, XS))

        ctk.CTkLabel(
            self.transcript_frame,
            text=f"รหัส: {student_id} | ห้อง: {student['class_room']}",
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            text_color=TEXT_CAPTION
        ).pack(pady=(0, L))

        # จัดกลุ่ม
        grouped = {}
        for grade in transcript_data:
            key = f"{grade['academic_year']}/{grade['semester']}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(grade)

        for key, grades in sorted(grouped.items()):
            year, semester = key.split("/")

            semester_frame = ctk.CTkFrame(
                self.transcript_frame,
                corner_radius=RADIUS_CARD,
                border_width=1, border_color=TABLE_BORDER
            )
            semester_frame.pack(fill="x", pady=S, padx=L)

            ctk.CTkLabel(
                semester_frame,
                text=f"ปีการศึกษา {year} ภาคเรียนที่ {semester}",
                font=ctk.CTkFont(family="TH Sarabun New", size=16, weight="bold"),
                text_color=TEXT_H2
            ).pack(pady=M)

            # ตาราง
            table_frame = ctk.CTkFrame(semester_frame, fg_color="transparent")
            table_frame.pack(fill="x", padx=M, pady=(0, S))

            headers = ["รหัสวิชา", "ชื่อวิชา", "คะแนน", "เกรด"]
            for col, header in enumerate(headers):
                ctk.CTkLabel(
                    table_frame, text=header,
                    font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
                    fg_color=PRIMARY, text_color="#FFFFFF",
                    corner_radius=XS, width=150 if col == 1 else 100
                ).grid(row=0, column=col, padx=1, pady=1, sticky="ew")

            for row, grade in enumerate(grades, start=1):
                grade_str = grade['grade'] if grade['grade'] else "-"
                grade_color = get_grade_color(grade_str)

                data = [
                    grade['subject_code'],
                    grade['subject_name'],
                    str(grade['score']) if grade['score'] is not None else "-",
                    grade_str,
                ]
                row_bg = TABLE_STRIPE if row % 2 == 1 else "#FFFFFF"
                for col, value in enumerate(data):
                    text_c = grade_color if col == 3 and grade_str != "-" else TEXT_BODY
                    ctk.CTkLabel(
                        table_frame, text=value,
                        font=ctk.CTkFont(family="TH Sarabun New", size=14,
                                         weight="bold" if col == 3 else "normal"),
                        fg_color=row_bg, text_color=text_c,
                        corner_radius=XS, width=150 if col == 1 else 100
                    ).grid(row=row, column=col, padx=1, pady=1, sticky="ew")

            # GPA - H1 (28px bold)
            valid_grades = []
            for g in grades:
                try:
                    if g['grade'] and g['grade'] != '-':
                        valid_grades.append(float(g['grade']))
                except (ValueError, TypeError):
                    pass
            if valid_grades:
                gpa = sum(valid_grades) / len(valid_grades)
                gpa_color = get_grade_color(f"{gpa:.1f}")
                ctk.CTkLabel(
                    semester_frame,
                    text=f"GPA: {gpa:.2f}",
                    font=ctk.CTkFont(family="TH Sarabun New", size=28, weight="bold"),
                    text_color=gpa_color
                ).pack(pady=M)

        self.update_status("แสดง Transcript เรียบร้อย", "success")

    def export_transcript_pdf(self):
        """Export Transcript PDF"""

        selected = self.transcript_student_var.get()
        if not selected or selected == "เลือกนักเรียน":
            messagebox.showwarning("คำเตือน", "กรุณาเลือกนักเรียน")
            return

        student_id = selected.split(" - ")[0]
        student = self.db.get_student_by_id(student_id)
        transcript_data = self.db.get_transcript(student_id)

        if not transcript_data:
            messagebox.showwarning("คำเตือน", "ยังไม่มีข้อมูลคะแนน")
            return

        file_path = filedialog.asksaveasfilename(
            title="บันทึกไฟล์ PDF", defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Transcript_{student_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        if not file_path:
            return

        try:
            font_name = get_thai_font()

            doc = SimpleDocTemplate(file_path, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()

            name = f"{student['title']}{student['first_name']} {student['last_name']}"
            title = Paragraph(f"Transcript - {name}", ParagraphStyle(
                'Title', parent=styles['Heading1'],
                fontName=font_name, fontSize=18, alignment=1
            ))
            elements.append(title)
            elements.append(Spacer(1, 0.3 * cm))

            info = Paragraph(
                f"รหัส: {student_id} | ห้อง: {student['class_room']}",
                ParagraphStyle('Info', parent=styles['Normal'],
                               fontName=font_name, fontSize=12, alignment=1)
            )
            elements.append(info)
            elements.append(Spacer(1, 0.5 * cm))

            grouped = {}
            for grade in transcript_data:
                key = f"{grade['academic_year']}/{grade['semester']}"
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(grade)

            for key, grades in sorted(grouped.items()):
                year, semester = key.split("/")

                semester_title = Paragraph(
                    f"ปีการศึกษา {year} ภาคเรียนที่ {semester}",
                    ParagraphStyle('Sem', parent=styles['Heading2'],
                                   fontName=font_name, fontSize=14)
                )
                elements.append(semester_title)
                elements.append(Spacer(1, 0.3 * cm))

                data = [["รหัสวิชา", "ชื่อวิชา", "คะแนน", "เกรด"]]
                for grade in grades:
                    data.append([
                        grade['subject_code'], grade['subject_name'],
                        str(grade['score']) if grade['score'] is not None else "-",
                        grade['grade'] if grade['grade'] else "-",
                    ])

                table = Table(data, colWidths=[3 * cm, 8 * cm, 3 * cm, 3 * cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(PRIMARY)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), font_name),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor(TABLE_STRIPE)),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(TABLE_BORDER)),
                    ('FONTNAME', (0, 1), (-1, -1), font_name),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                ]))

                elements.append(table)

                valid_grades = []
            for g in grades:
                try:
                    if g['grade'] and g['grade'] != '-':
                        valid_grades.append(float(g['grade']))
                except (ValueError, TypeError):
                    pass
                if valid_grades:
                    gpa = sum(valid_grades) / len(valid_grades)
                    elements.append(Spacer(1, 0.2 * cm))
                    elements.append(Paragraph(
                        f"GPA: {gpa:.2f}",
                        ParagraphStyle('GPA', parent=styles['Normal'],
                                       fontName=font_name, fontSize=12, alignment=2)
                    ))
                elements.append(Spacer(1, 0.5 * cm))

            doc.build(elements)
            self.update_status("Export PDF สำเร็จ", "success")
            messagebox.showinfo("สำเร็จ", "Export Transcript PDF เรียบร้อย")

        except Exception as e:
            messagebox.showerror("ผิดพลาด", f"ไม่สามารถสร้าง PDF ได้\n{str(e)}")


class GradeDialog(ctk.CTkToplevel):
    """หน้าต่างบันทึกคะแนน - radius 16px"""

    def __init__(self, parent, db, student_id, year, semester, subjects,
                 current_grade, callback, update_status):
        super().__init__(parent)

        self.db = db
        self.student_id = student_id
        self.year = year
        self.semester = semester
        self.subjects = subjects
        self.current_grade = current_grade
        self.callback = callback
        self.update_status = update_status

        self.title("บันทึกคะแนน")
        self.geometry("480x380")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.create_form()
        if current_grade:
            self.fill_data()

    def create_form(self):
        """สร้างฟอร์ม"""

        main_frame = ctk.CTkFrame(self, corner_radius=RADIUS_MODAL,
                                  border_width=1, border_color=TABLE_BORDER)
        main_frame.pack(fill="both", expand=True, padx=M, pady=M)

        header = ctk.CTkFrame(main_frame, fg_color=PRIMARY, corner_radius=RADIUS_CARD)
        header.pack(fill="x", padx=M, pady=(M, L))

        ctk.CTkLabel(
            header, text="บันทึกคะแนน",
            font=ctk.CTkFont(family="TH Sarabun New", size=16, weight="bold"),
            text_color="white"
        ).pack(pady=M)

        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(pady=M, padx=L)

        # วิชา
        ctk.CTkLabel(
            form_frame, text="เลือกวิชา:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            text_color=TEXT_H3
        ).grid(row=0, column=0, sticky="w", pady=S, padx=(0, M))

        self.subject_var = ctk.StringVar()
        subject_options = [f"{code} - {name}" for code, name in self.subjects]
        ctk.CTkOptionMenu(
            form_frame, variable=self.subject_var,
            values=subject_options, width=250, height=36,
            fg_color="#EFF6FF", button_color="#EFF6FF", button_hover_color="#DBEAFE",
            text_color="#1E40AF", dropdown_fg_color="#F0F4FF",
            dropdown_hover_color="#DBEAFE", dropdown_text_color="#1E40AF",
            dropdown_font=ctk.CTkFont(family="TH Sarabun New", size=16),
            corner_radius=20,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=0, column=1, pady=S)

        # คะแนน
        ctk.CTkLabel(
            form_frame, text="คะแนน:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            text_color=TEXT_H3
        ).grid(row=1, column=0, sticky="w", pady=S, padx=(0, M))

        self.score_var = ctk.StringVar()
        ctk.CTkEntry(
            form_frame, textvariable=self.score_var,
            width=250, height=36, corner_radius=RADIUS_BUTTON,
            border_width=1, border_color=INPUT_BORDER,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=1, column=1, pady=S)

        # เกรดอัตโนมัติ
        ctk.CTkLabel(
            form_frame, text="เกรด:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            text_color=TEXT_H3
        ).grid(row=2, column=0, sticky="w", pady=S, padx=(0, M))

        self.grade_label = ctk.CTkLabel(
            form_frame, text="-",
            font=ctk.CTkFont(family="TH Sarabun New", size=20, weight="bold"),
            text_color=PRIMARY
        )
        self.grade_label.grid(row=2, column=1, pady=S, sticky="w")

        self.score_var.trace("w", lambda *args: self.calculate_grade())

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
        subject_text = f"{self.current_grade['subject_code']} - {self.current_grade['subject_name']}"
        self.subject_var.set(subject_text)
        self.score_var.set(str(self.current_grade['score']) if self.current_grade['score'] is not None else "")

    def calculate_grade(self):
        """คำนวณเกรด + แสดงสีตาม grade"""
        try:
            score = float(self.score_var.get())
            grade = self.db.calculate_grade(score)
            color = get_grade_color(grade)
            self.grade_label.configure(text=grade, text_color=color)
        except (ValueError, TypeError):
            self.grade_label.configure(text="-", text_color=TEXT_CAPTION)

    def save(self):
        """บันทึก"""
        subject_text = self.subject_var.get()
        if not subject_text:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกวิชา")
            return

        try:
            score = float(self.score_var.get())
        except (ValueError, TypeError):
            messagebox.showwarning("คำเตือน", "กรุณากรอกคะแนนที่ถูกต้อง")
            return

        subject_code = subject_text.split(" - ")[0]
        subject_name = subject_text.split(" - ")[1]
        grade = self.db.calculate_grade(score)

        grade_data = {
            'student_id': self.student_id,
            'academic_year': self.year,
            'semester': self.semester,
            'subject_code': subject_code,
            'subject_name': subject_name,
            'full_score': 100,
            'score': score,
            'grade': grade,
        }

        if self.db.save_grade(grade_data):
            self.update_status("บันทึกคะแนนเรียบร้อย", "success")
            self.callback()
            self.destroy()
        else:
            messagebox.showerror("ผิดพลาด", "ไม่สามารถบันทึกได้")
