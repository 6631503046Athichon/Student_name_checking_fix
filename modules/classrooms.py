"""
modules/classrooms.py
โมดูลจัดการห้องเรียน - Design System v3.0
- เพิ่ม/ลบห้องเรียน
- แสดงจำนวนนักเรียนต่อห้อง
- กดดูรายชื่อนักเรียนของห้องนั้น
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from modules.icons import IconManager
from modules.students import StudentForm

# ==================== Design System ====================
PRIMARY = "#2563EB"
SUCCESS = "#16A34A"
WARNING = "#D97706"
DANGER = "#DC2626"
NEUTRAL = "#6B7280"

TEXT_H1 = "#111827"
TEXT_H2 = "#1F2937"
TEXT_H3 = "#374151"
TEXT_BODY = "#374151"
TEXT_CAPTION = "#6B7280"

SURFACE = "#FFFFFF"
TABLE_HEADER_BG = "#F9FAFB"
TABLE_HOVER = "#EFF6FF"
TABLE_STRIPE = "#F9FAFB"
TABLE_BORDER = "#E5E7EB"

XS, S, M, L, XL, XXL = 4, 8, 16, 24, 32, 48
RADIUS_BUTTON = 8
RADIUS_CARD = 12
RADIUS_MODAL = 16
INPUT_BORDER = "#D1D5DB"


class ClassroomsModule:
    """โมดูลจัดการห้องเรียน"""

    def __init__(self, parent, db, update_status_callback):
        self.parent = parent
        self.db = db
        self.update_status = update_status_callback
        self.selected_classroom = None

        self.create_ui()
        self.load_classrooms()

    def create_ui(self):
        """สร้าง UI"""
        self.content_frame = ctk.CTkScrollableFrame(
            self.parent, fg_color="transparent",
            scrollbar_button_color=NEUTRAL,
            scrollbar_button_hover_color=PRIMARY
        )
        self.content_frame.pack(fill="both", expand=True)

        # Header + ปุ่มเพิ่ม
        top_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        top_frame.pack(fill="x", padx=L, pady=(L, M))

        ctk.CTkLabel(
            top_frame, text="ห้องเรียนทั้งหมด",
            font=ctk.CTkFont(family="TH Sarabun New", size=20, weight="bold"),
            text_color=TEXT_H1
        ).pack(side="left")

        ctk.CTkButton(
            top_frame, text="เพิ่มห้องเรียน",
            command=self.add_classroom,
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            width=140, height=36,
            corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8",
            image=IconManager.get_white("plus", 14), compound="left"
        ).pack(side="right")

        # Cards container
        self.cards_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=L, pady=(0, M))

        # Empty state
        self.empty_label = ctk.CTkLabel(
            self.cards_frame,
            text="ยังไม่มีห้องเรียน กดปุ่ม \"เพิ่มห้องเรียน\" เพื่อเริ่มต้น",
            font=ctk.CTkFont(family="TH Sarabun New", size=16),
            text_color=TEXT_CAPTION
        )

        # ตารางนักเรียน (ซ่อนไว้ก่อน จะแสดงเมื่อกดดู)
        self.detail_frame = ctk.CTkFrame(
            self.content_frame, fg_color=SURFACE,
            corner_radius=RADIUS_CARD, border_width=1, border_color=TABLE_BORDER
        )

        detail_top = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        detail_top.pack(fill="x", padx=L, pady=(M, S))

        self.detail_header = ctk.CTkLabel(
            detail_top, text="",
            font=ctk.CTkFont(family="TH Sarabun New", size=16, weight="bold"),
            text_color=TEXT_H2
        )
        self.detail_header.pack(side="left")

        self.add_student_btn = ctk.CTkButton(
            detail_top, text="เพิ่มนักเรียน",
            command=self._add_student_to_room,
            font=ctk.CTkFont(family="TH Sarabun New", size=13, weight="bold"),
            width=110, height=30, corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8",
            image=IconManager.get_white("plus", 12), compound="left"
        )
        self.add_student_btn.pack(side="right")

        # Treeview
        tree_container = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        tree_container.pack(fill="x", padx=L, pady=(0, M))

        columns = ("student_id", "title", "first_name", "last_name", "parent_phone")
        self.tree = ttk.Treeview(
            tree_container, columns=columns, show="headings", height=8
        )

        headers = {
            "student_id": ("รหัส", 100),
            "title": ("คำนำหน้า", 80),
            "first_name": ("ชื่อ", 120),
            "last_name": ("นามสกุล", 120),
            "parent_phone": ("เบอร์ผู้ปกครอง", 120),
        }
        for col, (text, width) in headers.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, minwidth=60)

        self.tree.pack(fill="x")

        style = ttk.Style()
        style.configure("Treeview",
                        font=("TH Sarabun New", 14),
                        rowheight=32,
                        background=SURFACE,
                        fieldbackground=SURFACE)
        style.configure("Treeview.Heading",
                        font=("TH Sarabun New", 14, "bold"),
                        background=TABLE_HEADER_BG)
        self.tree.tag_configure('evenrow', background=SURFACE)
        self.tree.tag_configure('oddrow', background=TABLE_STRIPE)

    def load_classrooms(self):
        """โหลดห้องเรียนทั้งหมดแสดงเป็น cards"""
        # ลบ cards เก่า
        for widget in self.cards_frame.winfo_children():
            if widget != self.empty_label:
                widget.destroy()

        classrooms = self.db.get_all_classrooms()

        if not classrooms:
            self.empty_label.pack(pady=XL)
            return
        else:
            self.empty_label.pack_forget()

        # สร้าง grid 3 คอลัมน์
        cols = 3
        for idx, cr in enumerate(classrooms):
            row = idx // cols
            col = idx % cols

            # ตรวจว่า row frame มีอยู่หรือยัง
            if col == 0:
                row_frame = ctk.CTkFrame(self.cards_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=(0, S))
                for c in range(cols):
                    row_frame.columnconfigure(c, weight=1)

            card = self._create_classroom_card(row_frame, cr)
            card.grid(row=0, column=col, padx=(0 if col == 0 else S, 0), sticky="nsew")

    def _create_classroom_card(self, parent, classroom):
        """สร้าง card สำหรับห้องเรียน 1 ห้อง"""
        card = ctk.CTkFrame(
            parent, fg_color=SURFACE,
            corner_radius=RADIUS_CARD,
            border_width=1, border_color=TABLE_BORDER
        )

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=M, pady=M)

        # ชื่อห้อง
        ctk.CTkLabel(
            inner, text=classroom['name'],
            font=ctk.CTkFont(family="TH Sarabun New", size=18, weight="bold"),
            text_color=PRIMARY, anchor="w"
        ).pack(fill="x")

        # จำนวนนักเรียน
        count = classroom['student_count']
        ctk.CTkLabel(
            inner, text=f"{count} คน",
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            text_color=TEXT_CAPTION, anchor="w"
        ).pack(fill="x", pady=(XS, S))

        # ปุ่ม
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(
            btn_frame, text="ดูรายชื่อ",
            command=lambda name=classroom['name']: self.show_students(name),
            font=ctk.CTkFont(family="TH Sarabun New", size=13),
            width=80, height=30, corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8"
        ).pack(side="left", padx=(0, S))

        ctk.CTkButton(
            btn_frame, text="ลบ",
            command=lambda cid=classroom['id'], name=classroom['name']: self.delete_classroom(cid, name),
            font=ctk.CTkFont(family="TH Sarabun New", size=13),
            width=60, height=30, corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=DANGER, text_color=DANGER,
            hover_color="#FEF2F2"
        ).pack(side="left")

        return card

    def add_classroom(self):
        """เปิด dialog เพิ่มห้องเรียน — เลือกระดับชั้น + ชั้นปี + ห้อง"""
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("เพิ่มห้องเรียน")
        dialog.geometry("380x280")
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()

        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 190
        y = (dialog.winfo_screenheight() // 2) - 140
        dialog.geometry(f"380x280+{x}+{y}")

        frame = ctk.CTkFrame(dialog, fg_color=SURFACE, corner_radius=0)
        frame.pack(fill="both", expand=True)

        # Header
        header = ctk.CTkFrame(frame, fg_color=PRIMARY, corner_radius=0, height=40)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="เพิ่มห้องเรียนใหม่",
            font=ctk.CTkFont(family="TH Sarabun New", size=16, weight="bold"),
            text_color="white"
        ).pack(expand=True)

        # Preview label
        preview_var = ctk.StringVar(value="ป.1/1")
        preview_label = ctk.CTkLabel(
            frame, textvariable=preview_var,
            font=ctk.CTkFont(family="TH Sarabun New", size=24, weight="bold"),
            text_color=PRIMARY
        )
        preview_label.pack(pady=(M, S))

        # Dropdowns row
        select_frame = ctk.CTkFrame(frame, fg_color="transparent")
        select_frame.pack(fill="x", padx=L)
        select_frame.columnconfigure(0, weight=1)
        select_frame.columnconfigure(1, weight=1)
        select_frame.columnconfigure(2, weight=1)

        font_label = ctk.CTkFont(family="TH Sarabun New", size=13, weight="bold")
        font_dd = ctk.CTkFont(family="TH Sarabun New", size=14)

        # ระดับชั้น
        col0 = ctk.CTkFrame(select_frame, fg_color="transparent")
        col0.grid(row=0, column=0, sticky="nsew", padx=(0, S))
        ctk.CTkLabel(col0, text="ระดับชั้น", font=font_label, text_color=TEXT_H3, anchor="w").pack(fill="x")
        level_var = ctk.StringVar(value="ป.")
        level_menu = ctk.CTkOptionMenu(
            col0, variable=level_var, values=["ป.", "ม."],
            font=font_dd, height=34, corner_radius=RADIUS_BUTTON,
            fg_color="#F9FAFB", button_color=PRIMARY,
            button_hover_color="#1D4ED8", text_color=TEXT_H2
        )
        level_menu.pack(fill="x", pady=(XS, 0))

        # ชั้นปี
        col1 = ctk.CTkFrame(select_frame, fg_color="transparent")
        col1.grid(row=0, column=1, sticky="nsew", padx=(0, S))
        ctk.CTkLabel(col1, text="ชั้นปี", font=font_label, text_color=TEXT_H3, anchor="w").pack(fill="x")
        grade_var = ctk.StringVar(value="1")
        grade_menu = ctk.CTkOptionMenu(
            col1, variable=grade_var, values=["1", "2", "3", "4", "5", "6"],
            font=font_dd, height=34, corner_radius=RADIUS_BUTTON,
            fg_color="#F9FAFB", button_color=PRIMARY,
            button_hover_color="#1D4ED8", text_color=TEXT_H2
        )
        grade_menu.pack(fill="x", pady=(XS, 0))

        # ห้อง
        col2 = ctk.CTkFrame(select_frame, fg_color="transparent")
        col2.grid(row=0, column=2, sticky="nsew")
        ctk.CTkLabel(col2, text="ห้อง", font=font_label, text_color=TEXT_H3, anchor="w").pack(fill="x")
        section_var = ctk.StringVar(value="1")
        section_menu = ctk.CTkOptionMenu(
            col2, variable=section_var, values=["1", "2", "3", "4", "5", "6", "7", "8"],
            font=font_dd, height=34, corner_radius=RADIUS_BUTTON,
            fg_color="#F9FAFB", button_color=PRIMARY,
            button_hover_color="#1D4ED8", text_color=TEXT_H2
        )
        section_menu.pack(fill="x", pady=(XS, 0))

        # อัปเดต preview เมื่อเปลี่ยน dropdown
        def update_preview(*_):
            preview_var.set(f"{level_var.get()}{grade_var.get()}/{section_var.get()}")

        level_var.trace_add("write", update_preview)
        grade_var.trace_add("write", update_preview)
        section_var.trace_add("write", update_preview)

        # ปุ่ม
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=L, pady=M)

        def save():
            name = preview_var.get()
            if self.db.add_classroom(name):
                self.update_status(f"เพิ่มห้องเรียน {name} เรียบร้อย", "success")
                dialog.destroy()
                self.load_classrooms()
            else:
                messagebox.showwarning("คำเตือน", f"ห้องเรียน \"{name}\" มีอยู่แล้ว", parent=dialog)

        ctk.CTkButton(
            btn_frame, text="ยกเลิก", command=dialog.destroy,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=80, height=34, corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=NEUTRAL, text_color=NEUTRAL, hover_color="#F3F4F6"
        ).pack(side="right", padx=(S, 0))

        ctk.CTkButton(
            btn_frame, text="บันทึก", command=save,
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            width=80, height=34, corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8"
        ).pack(side="right")

    def delete_classroom(self, classroom_id, name):
        """ลบห้องเรียน"""
        confirm = messagebox.askyesno(
            "ยืนยันการลบ",
            f"ต้องการลบห้องเรียน \"{name}\" หรือไม่?\n(ข้อมูลนักเรียนในห้องจะไม่ถูกลบ)",
            parent=self.parent
        )
        if confirm:
            if self.db.delete_classroom(classroom_id):
                self.update_status(f"ลบห้องเรียน {name} เรียบร้อย", "success")
                self.load_classrooms()
                # ซ่อนตารางถ้ากำลังดูห้องที่ลบ
                if self.selected_classroom == name:
                    self.detail_frame.pack_forget()
                    self.selected_classroom = None

    def _add_student_to_room(self):
        """เปิดฟอร์มเพิ่มนักเรียนพร้อมเติมห้องให้อัตโนมัติ"""
        if self.selected_classroom:
            def on_saved():
                self.show_students(self.selected_classroom)
                self.load_classrooms()
            StudentForm(self.parent, self.db, on_saved, self.update_status,
                        default_class_room=self.selected_classroom)

    def show_students(self, class_room):
        """แสดงรายชื่อนักเรียนของห้องที่เลือก"""
        self.selected_classroom = class_room
        self.detail_header.configure(text=f"รายชื่อนักเรียน — {class_room}")

        # แสดง detail frame
        self.detail_frame.pack(fill="x", padx=L, pady=(0, L))

        # ล้างตาราง
        for item in self.tree.get_children():
            self.tree.delete(item)

        students = self.db.get_all_students(class_room=class_room)

        if not students:
            self.tree.insert("", "end", values=("", "", "ไม่มีนักเรียนในห้องนี้", "", ""))
            return

        for idx, s in enumerate(students):
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            self.tree.insert("", "end", values=(
                s['student_id'], s['title'],
                s['first_name'], s['last_name'],
                s['parent_phone'] or "-"
            ), tags=(tag,))
