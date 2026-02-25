"""
modules/health.py
โมดูลสุขภาพ - Design System v3.0
- BMI Cards: ต่ำกว่าเกณฑ์(DANGER), ปกติ(SUCCESS), เกิน(WARNING)
- BMI ตัวเลขใหญ่ 28px (H1)
- Chart matplotlib สีตาม design system
- Spacing 24px padding ใน card
- Empty state แสดงเมื่อไม่มีข้อมูล
"""

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from modules.icons import IconManager

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
RADIUS_INPUT = 8
INPUT_BORDER = "#CBD5E1"


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


class HealthModule:
    """โมดูลสุขภาพ - Design System v4.0"""

    def __init__(self, parent, db, update_status_callback):
        self.parent = parent
        self.db = db
        self.update_status = update_status_callback
        self.current_date = datetime.now()
        self.create_ui()

    def create_ui(self):
        """สร้าง UI
        ใช้ CTkScrollableFrame ครอบทั้งหมด เพื่อให้เลื่อนดูได้เมื่อเนื้อหาล้น
        """

        # CTkScrollableFrame ครอบเนื้อหาทั้งหมด - รองรับหน้าจอเล็ก
        self.content_frame = ctk.CTkScrollableFrame(
            self.parent,
            fg_color="transparent",
            scrollbar_button_color="#CBD5E1",
            scrollbar_button_hover_color=PRIMARY
        )
        self.content_frame.pack(fill="both", expand=True)

        self.tabview = ctk.CTkTabview(
            self.content_frame, corner_radius=RADIUS_CARD,
            fg_color="#FFFFFF", border_width=1, border_color="#E2E8F0",
            segmented_button_fg_color="#E2E8F0",
            segmented_button_selected_color=PRIMARY,
            segmented_button_unselected_color="#E2E8F0",
            segmented_button_selected_hover_color="#2563EB",
            segmented_button_unselected_hover_color="#CBD5E1",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Kanit", size=13, weight="500")
        )
        self.tabview.pack(fill="both", expand=True, padx=M, pady=M)

        self.tabview.add("🦷 แปรงฟัน/ดื่มนม")
        self.create_daily_health_tab()

        self.tabview.add("📏 น้ำหนัก-ส่วนสูง")
        self.create_weight_height_tab()

    def create_daily_health_tab(self):
        """Tab แปรงฟัน/ดื่มนม"""

        tab = self.tabview.tab("แปรงฟัน/ดื่มนม")

        # === Control Card (white) ===
        control_card = ctk.CTkFrame(
            tab, fg_color="#F8FAFC",
            corner_radius=RADIUS_CARD, border_width=1, border_color=TABLE_BORDER
        )
        control_card.pack(fill="x", padx=M, pady=(M, S))

        top_frame = ctk.CTkFrame(control_card, fg_color="transparent")
        top_frame.pack(fill="x", padx=M, pady=(M, S))

        ctk.CTkLabel(
            top_frame, text="วันที่:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            text_color=TEXT_H3
        ).pack(side="left", padx=(0, S))

        self.health_date_var = ctk.StringVar(value=self.current_date.strftime("%Y-%m-%d"))
        ctk.CTkEntry(
            top_frame, textvariable=self.health_date_var,
            width=140, height=36,
            corner_radius=RADIUS_BUTTON, border_width=1, border_color=INPUT_BORDER,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, M))

        ctk.CTkLabel(
            top_frame, text="ห้อง:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            text_color=TEXT_H3
        ).pack(side="left", padx=(0, S))

        self.health_class_var = ctk.StringVar(value="ทั้งหมด")
        class_options = ["ทั้งหมด"] + self.db.get_class_rooms()
        ctk.CTkOptionMenu(
            top_frame, variable=self.health_class_var,
            values=class_options,
            command=lambda x: self.load_daily_health(),
            width=140, height=36,
            fg_color="#EFF6FF", button_color="#EFF6FF", button_hover_color="#DBEAFE",
            text_color="#1E40AF", dropdown_fg_color="#F0F4FF",
            dropdown_hover_color="#DBEAFE", dropdown_text_color="#1E40AF",
            dropdown_font=ctk.CTkFont(family="TH Sarabun New", size=16),
            corner_radius=20,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, M))

        ctk.CTkButton(
            top_frame, text="โหลดข้อมูล",
            command=self.load_daily_health,
            image=IconManager.get_white("download", 14), compound="left",
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            width=120, height=36,
            corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8"
        ).pack(side="left")

        # ตาราง
        table_frame = ctk.CTkFrame(
            tab, fg_color="#FFFFFF",
            corner_radius=RADIUS_CARD,
            border_width=1, border_color=TABLE_BORDER
        )
        table_frame.pack(fill="both", expand=True, padx=M, pady=S)

        columns = ("student_id", "name", "class_room", "brushed_teeth", "drank_milk")
        self.health_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        self.health_tree.heading("student_id", text="รหัส")
        self.health_tree.heading("name", text="ชื่อ-นามสกุล")
        self.health_tree.heading("class_room", text="ห้อง")
        self.health_tree.heading("brushed_teeth", text="แปรงฟัน")
        self.health_tree.heading("drank_milk", text="ดื่มนม")

        self.health_tree.column("student_id", width=100, anchor="center")
        self.health_tree.column("name", width=250)
        self.health_tree.column("class_room", width=100, anchor="center")
        self.health_tree.column("brushed_teeth", width=100, anchor="center")
        self.health_tree.column("drank_milk", width=100, anchor="center")

        apply_treeview_style(self.health_tree, "Health.Treeview")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.health_tree.yview)
        self.health_tree.configure(yscrollcommand=scrollbar.set)
        self.health_tree.pack(side="left", fill="both", expand=True, padx=(S, 0), pady=S)
        scrollbar.pack(side="right", fill="y", pady=S, padx=(0, XS))

        self.health_tree.bind("<ButtonRelease-1>", self.on_health_tree_click)

        # ปุ่มด้านล่าง
        btn_frame = ctk.CTkFrame(control_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=M, pady=(0, M))

        # ปุ่ม PRIMARY 1 ปุ่ม: ทำทั้งหมด
        ctk.CTkButton(
            btn_frame, text="ทำทั้งหมด",
            command=self.mark_all_health,
            image=IconManager.get_white("check-double", 14), compound="left",
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            width=120, height=36,
            corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8"
        ).pack(side="left", padx=(0, S))

        # SECONDARY
        ctk.CTkButton(
            btn_frame, text="ติ๊กแปรงฟัน",
            command=lambda: self.toggle_health_status("brushed_teeth"),
            image=IconManager.get("tooth", 14, color=NEUTRAL, dark_color="#9CA3AF"), compound="left",
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120, height=36,
            corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=NEUTRAL, text_color=NEUTRAL,
            hover_color="#F3F4F6"
        ).pack(side="left", padx=(0, S))

        ctk.CTkButton(
            btn_frame, text="ติ๊กดื่มนม",
            command=lambda: self.toggle_health_status("drank_milk"),
            image=IconManager.get("mug-hot", 14, color=NEUTRAL, dark_color="#9CA3AF"), compound="left",
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120, height=36,
            corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=NEUTRAL, text_color=NEUTRAL,
            hover_color="#F3F4F6"
        ).pack(side="left")

        self.load_daily_health()

    def create_weight_height_tab(self):
        """Tab น้ำหนัก-ส่วนสูง"""

        tab = self.tabview.tab("น้ำหนัก-ส่วนสูง")

        # === Control Card (white) ===
        control_card = ctk.CTkFrame(
            tab, fg_color="#F8FAFC",
            corner_radius=RADIUS_CARD, border_width=1, border_color=TABLE_BORDER
        )
        control_card.pack(fill="x", padx=M, pady=(M, S))

        top_frame = ctk.CTkFrame(control_card, fg_color="transparent")
        top_frame.pack(fill="x", padx=M, pady=M)

        ctk.CTkLabel(
            top_frame, text="เลือกนักเรียน:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            text_color=TEXT_H3
        ).pack(side="left", padx=(0, S))

        self.weight_student_var = ctk.StringVar()
        self.weight_student_menu = ctk.CTkOptionMenu(
            top_frame, variable=self.weight_student_var,
            values=["เลือกนักเรียน"], width=280, height=36,
            fg_color="#EFF6FF", button_color="#EFF6FF", button_hover_color="#DBEAFE",
            text_color="#1E40AF", dropdown_fg_color="#F0F4FF",
            dropdown_hover_color="#DBEAFE", dropdown_text_color="#1E40AF",
            dropdown_font=ctk.CTkFont(family="TH Sarabun New", size=16),
            corner_radius=20,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            command=lambda x: self.load_weight_height_data()
        )
        self.weight_student_menu.pack(side="left", padx=(0, M))

        ctk.CTkButton(
            top_frame, text="บันทึกข้อมูล",
            command=self.add_weight_height,
            image=IconManager.get_white("plus", 14), compound="left",
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            width=130, height=36,
            corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8"
        ).pack(side="left")

        # BMI Card - radius 12px, padding 24px
        self.bmi_frame = ctk.CTkFrame(
            tab, fg_color="#FFFFFF",
            corner_radius=RADIUS_CARD,
            border_width=1, border_color=TABLE_BORDER
        )
        self.bmi_frame.pack(fill="x", padx=M, pady=S)

        self.bmi_info_label = ctk.CTkLabel(
            self.bmi_frame,
            text="เลือกนักเรียนเพื่อดูข้อมูล BMI",
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            text_color=TEXT_CAPTION
        )
        self.bmi_info_label.pack(pady=L)

        # ตารางประวัติ
        table_frame = ctk.CTkFrame(
            tab, fg_color="#FFFFFF",
            corner_radius=RADIUS_CARD,
            border_width=1, border_color=TABLE_BORDER
        )
        table_frame.pack(fill="both", expand=True, padx=M, pady=S)

        columns = ("record_date", "weight", "height", "bmi", "status")
        self.weight_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)

        self.weight_tree.heading("record_date", text="วันที่")
        self.weight_tree.heading("weight", text="น้ำหนัก (kg)")
        self.weight_tree.heading("height", text="ส่วนสูง (cm)")
        self.weight_tree.heading("bmi", text="BMI")
        self.weight_tree.heading("status", text="สถานะ")

        self.weight_tree.column("record_date", width=120, anchor="center")
        self.weight_tree.column("weight", width=120, anchor="center")
        self.weight_tree.column("height", width=120, anchor="center")
        self.weight_tree.column("bmi", width=100, anchor="center")
        self.weight_tree.column("status", width=150, anchor="center")

        apply_treeview_style(self.weight_tree, "Weight.Treeview")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.weight_tree.yview)
        self.weight_tree.configure(yscrollcommand=scrollbar.set)
        self.weight_tree.pack(side="left", fill="both", expand=True, padx=(S, 0), pady=S)
        scrollbar.pack(side="right", fill="y", pady=S, padx=(0, XS))

        self.load_student_list_for_weight()

    # ==================== FUNCTIONS ====================

    def on_health_tree_click(self, event):
        """คลิกที่คอลัมน์แปรงฟัน/ดื่มนม → toggle สถานะทันที"""
        region = self.health_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column = self.health_tree.identify_column(event.x)
        item = self.health_tree.identify_row(event.y)
        if not item:
            return

        self.health_tree.selection_set(item)

        # #4 = แปรงฟัน, #5 = ดื่มนม
        if column == "#4":
            self.toggle_health_status("brushed_teeth")
        elif column == "#5":
            self.toggle_health_status("drank_milk")

    def load_daily_health(self):
        """โหลดข้อมูลสุขภาพรายวัน"""
        for item in self.health_tree.get_children():
            self.health_tree.delete(item)

        date = self.health_date_var.get()
        class_room = None if self.health_class_var.get() == "ทั้งหมด" else self.health_class_var.get()

        students = self.db.get_all_students(class_room=class_room)
        health_records = self.db.get_health_by_date(date, class_room)
        health_dict = {rec['student_id']: rec for rec in health_records}

        for idx, student in enumerate(students):
            name = f"{student['title']}{student['first_name']} {student['last_name']}"
            health = health_dict.get(student['student_id'], {})
            brushed = "V" if health.get('brushed_teeth') else "-"
            drank = "V" if health.get('drank_milk') else "-"
            tag = "odd" if idx % 2 == 0 else "even"
            self.health_tree.insert("", "end", values=(
                student['student_id'], name, student['class_room'], brushed, drank
            ), tags=(tag,))

        self.update_status(f"โหลดข้อมูล {len(students)} คน", "success")

    def toggle_health_status(self, field=None):
        """สลับสถานะแปรงฟัน/ดื่มนม"""
        selected = self.health_tree.selection()
        if not selected:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกนักเรียน")
            return

        student_id = str(self.health_tree.item(selected[0])['values'][0])
        date = self.health_date_var.get()

        if not field:
            HealthDialog(self.parent, self.db, student_id, date,
                         self.load_daily_health, self.update_status)
        else:
            current = self.health_tree.item(selected[0])['values']
            brushed = 1 if current[3] == "V" else 0
            drank = 1 if current[4] == "V" else 0

            if field == "brushed_teeth":
                brushed = 1 - brushed
            else:
                drank = 1 - drank

            if self.db.update_health_daily(student_id, date, brushed, drank):
                self.load_daily_health()
                self.update_status("บันทึกข้อมูลสุขภาพเรียบร้อย", "success")

    def mark_all_health(self):
        """ทำเครื่องหมายทั้งหมด"""
        date = self.health_date_var.get()
        class_room = None if self.health_class_var.get() == "ทั้งหมด" else self.health_class_var.get()
        students = self.db.get_all_students(class_room=class_room)

        confirm = messagebox.askyesno(
            "ยืนยัน",
            f"ต้องการทำเครื่องหมายทั้งหมดให้นักเรียน {len(students)} คน หรือไม่?"
        )
        if not confirm:
            return

        success = 0
        for student in students:
            if self.db.update_health_daily(student['student_id'], date, 1, 1):
                success += 1

        self.load_daily_health()
        self.update_status(f"บันทึกข้อมูล {success} คน", "success")

    def load_student_list_for_weight(self):
        """โหลดรายชื่อสำหรับน้ำหนัก-ส่วนสูง"""
        students = self.db.get_all_students()
        options = [f"{s['student_id']} - {s['title']}{s['first_name']} {s['last_name']}" for s in students]
        if options:
            self.weight_student_menu.configure(values=options)
            self.weight_student_var.set(options[0])
            self.load_weight_height_data()

    def load_weight_height_data(self):
        """โหลดข้อมูลน้ำหนัก-ส่วนสูง พร้อม BMI card ตัวเลข 28px"""
        for item in self.weight_tree.get_children():
            self.weight_tree.delete(item)

        selected = self.weight_student_var.get()
        if not selected or selected == "เลือกนักเรียน":
            return

        student_id = selected.split(" - ")[0]
        records = self.db.get_health_records(student_id)
        weight_records = [r for r in records if r['weight_kg'] or r['height_cm']]

        for idx, record in enumerate(weight_records):
            bmi = record['bmi'] if record['bmi'] else "-"
            status = self.get_bmi_status(record['bmi']) if record['bmi'] else "-"
            tag = "odd" if idx % 2 == 0 else "even"
            self.weight_tree.insert("", "end", values=(
                record['record_date'],
                record['weight_kg'] or "-",
                record['height_cm'] or "-",
                f"{bmi:.2f}" if isinstance(bmi, (int, float)) else "-",
                status
            ), tags=(tag,))

        # BMI Card ล่าสุด - ตัวเลข H1 (28px)
        latest = self.db.get_latest_health(student_id)
        if latest and latest['bmi']:
            bmi = latest['bmi']
            status = self.get_bmi_status(bmi)
            color = self.get_bmi_color(bmi)

            for widget in self.bmi_frame.winfo_children():
                widget.destroy()

            # BMI Card - radius 12px, padding 24px
            bmi_inner = ctk.CTkFrame(self.bmi_frame, fg_color="transparent")
            bmi_inner.pack(pady=L, padx=L, fill="x")

            # Accent strip
            accent = ctk.CTkFrame(bmi_inner, fg_color=color, width=6, corner_radius=3)
            accent.pack(side="left", fill="y", padx=(0, M))

            info_col = ctk.CTkFrame(bmi_inner, fg_color="transparent")
            info_col.pack(side="left")

            # BMI ตัวเลข H1 (28px bold)
            ctk.CTkLabel(
                info_col, text=f"BMI: {bmi:.2f}",
                font=ctk.CTkFont(family="TH Sarabun New", size=28, weight="bold"),
                text_color=color
            ).pack(anchor="w")

            ctk.CTkLabel(
                info_col, text=f"สถานะ: {status}",
                font=ctk.CTkFont(family="TH Sarabun New", size=14),
                text_color=TEXT_CAPTION
            ).pack(anchor="w")

            ctk.CTkLabel(
                self.bmi_frame,
                text=f"น้ำหนัก: {latest['weight_kg']} kg  |  ส่วนสูง: {latest['height_cm']} cm",
                font=ctk.CTkFont(family="TH Sarabun New", size=14),
                text_color=TEXT_CAPTION
            ).pack(pady=(0, M))
        else:
            for widget in self.bmi_frame.winfo_children():
                widget.destroy()
            ctk.CTkLabel(
                self.bmi_frame,
                text="ยังไม่มีข้อมูล BMI",
                font=ctk.CTkFont(family="TH Sarabun New", size=16),
                text_color=TEXT_CAPTION
            ).pack(pady=L)

        self.update_status("โหลดข้อมูลเรียบร้อย", "success")

    def get_bmi_status(self, bmi):
        """สถานะ BMI"""
        if bmi < 18.5:
            return "น้ำหนักต่ำกว่าเกณฑ์"
        elif bmi < 23:
            return "น้ำหนักปกติ"
        elif bmi < 25:
            return "น้ำหนักเกิน"
        else:
            return "อ้วน"

    def get_bmi_color(self, bmi):
        """สี BMI ตาม design system"""
        if bmi < 18.5:
            return DANGER       # ต่ำกว่าเกณฑ์ -> แดง
        elif bmi < 23:
            return SUCCESS      # ปกติ -> เขียว
        else:
            return WARNING      # เกิน -> ส้ม

    def add_weight_height(self):
        """เพิ่มข้อมูลน้ำหนัก-ส่วนสูง"""
        selected = self.weight_student_var.get()
        if not selected or selected == "เลือกนักเรียน":
            messagebox.showwarning("คำเตือน", "กรุณาเลือกนักเรียน")
            return

        student_id = selected.split(" - ")[0]
        WeightHeightDialog(
            self.parent, self.db, student_id,
            self.load_weight_height_data, self.update_status
        )

class HealthDialog(ctk.CTkToplevel):
    """หน้าต่างบันทึกสุขภาพ - radius 16px"""

    def __init__(self, parent, db, student_id, date, callback, update_status):
        super().__init__(parent)

        self.db = db
        self.student_id = student_id
        self.date = date
        self.callback = callback
        self.update_status = update_status

        self.title("บันทึกสุขภาพ")
        self.geometry("380x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        student = db.get_student_by_id(student_id)
        name = f"{student['title']}{student['first_name']} {student['last_name']}"

        main_frame = ctk.CTkFrame(self, corner_radius=RADIUS_MODAL, border_width=1, border_color=TABLE_BORDER)
        main_frame.pack(fill="both", expand=True, padx=M, pady=M)

        header = ctk.CTkFrame(main_frame, fg_color=PRIMARY, corner_radius=RADIUS_CARD)
        header.pack(fill="x", padx=M, pady=(M, L))

        ctk.CTkLabel(
            header, text="บันทึกสุขภาพ",
            font=ctk.CTkFont(family="TH Sarabun New", size=16, weight="bold"),
            text_color="white"
        ).pack(pady=(S, XS))

        ctk.CTkLabel(
            header, text=name,
            font=ctk.CTkFont(family="TH Sarabun New", size=12),
            text_color="#BFDBFE"
        ).pack(pady=(0, S))

        body = ctk.CTkFrame(main_frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=L, pady=M)

        self.brushed_var = ctk.IntVar()
        ctk.CTkCheckBox(
            body, text="แปรงฟัน", variable=self.brushed_var,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            text_color=TEXT_BODY, fg_color=PRIMARY, hover_color="#1D4ED8"
        ).pack(pady=S, anchor="w")

        self.drank_var = ctk.IntVar()
        ctk.CTkCheckBox(
            body, text="ดื่มนม", variable=self.drank_var,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            text_color=TEXT_BODY, fg_color=PRIMARY, hover_color="#1D4ED8"
        ).pack(pady=S, anchor="w")

        btn_frame = ctk.CTkFrame(body, fg_color="transparent")
        btn_frame.pack(pady=M)

        ctk.CTkButton(
            btn_frame, text="บันทึก", command=self.save,
            image=IconManager.get_white("floppy-disk", 14), compound="left",
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            width=100, height=36, corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8"
        ).pack(side="left", padx=S)

        ctk.CTkButton(
            btn_frame, text="ยกเลิก", command=self.destroy,
            image=IconManager.get("xmark", 14, color=NEUTRAL, dark_color="#9CA3AF"), compound="left",
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=100, height=36, corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=NEUTRAL, text_color=NEUTRAL, hover_color="#F3F4F6"
        ).pack(side="left", padx=S)

    def save(self):
        """บันทึก"""
        if self.db.update_health_daily(self.student_id, self.date,
                                       self.brushed_var.get(), self.drank_var.get()):
            self.update_status("บันทึกข้อมูลสุขภาพเรียบร้อย", "success")
            self.callback()
            self.destroy()
        else:
            messagebox.showerror("ผิดพลาด", "ไม่สามารถบันทึกได้")


class WeightHeightDialog(ctk.CTkToplevel):
    """หน้าต่างบันทึกน้ำหนัก-ส่วนสูง - radius 16px, max 560px"""

    def __init__(self, parent, db, student_id, callback, update_status):
        super().__init__(parent)

        self.db = db
        self.student_id = student_id
        self.callback = callback
        self.update_status = update_status

        self.title("บันทึกน้ำหนัก-ส่วนสูง")
        self.geometry("440x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        student = db.get_student_by_id(student_id)
        name = f"{student['title']}{student['first_name']} {student['last_name']}"

        main_frame = ctk.CTkFrame(self, corner_radius=RADIUS_MODAL, border_width=1, border_color=TABLE_BORDER)
        main_frame.pack(fill="both", expand=True, padx=M, pady=M)

        header = ctk.CTkFrame(main_frame, fg_color=PRIMARY, corner_radius=RADIUS_CARD)
        header.pack(fill="x", padx=M, pady=(M, L))

        ctk.CTkLabel(
            header, text="บันทึกน้ำหนัก-ส่วนสูง",
            font=ctk.CTkFont(family="TH Sarabun New", size=16, weight="bold"),
            text_color="white"
        ).pack(pady=(S, XS))

        ctk.CTkLabel(
            header, text=name,
            font=ctk.CTkFont(family="TH Sarabun New", size=12),
            text_color="#BFDBFE"
        ).pack(pady=(0, S))

        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(pady=M, padx=L)

        for row_idx, (label, var_name) in enumerate([
            ("วันที่:", "date"), ("น้ำหนัก (kg):", "weight"), ("ส่วนสูง (cm):", "height")
        ]):
            ctk.CTkLabel(
                form_frame, text=label,
                font=ctk.CTkFont(family="TH Sarabun New", size=14),
                text_color=TEXT_H3
            ).grid(row=row_idx, column=0, sticky="w", pady=S, padx=(0, M))

            var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d") if var_name == "date" else "")
            setattr(self, f"{var_name}_var", var)

            ctk.CTkEntry(
                form_frame, textvariable=var,
                width=220, height=36,
                corner_radius=RADIUS_BUTTON, border_width=1, border_color=INPUT_BORDER,
                font=ctk.CTkFont(family="TH Sarabun New", size=14)
            ).grid(row=row_idx, column=1, pady=S)

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=L)

        ctk.CTkButton(
            btn_frame, text="บันทึก", command=self.save,
            image=IconManager.get_white("floppy-disk", 14), compound="left",
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            width=100, height=36, corner_radius=RADIUS_BUTTON,
            fg_color=PRIMARY, hover_color="#1D4ED8"
        ).pack(side="left", padx=S)

        ctk.CTkButton(
            btn_frame, text="ยกเลิก", command=self.destroy,
            image=IconManager.get("xmark", 14, color=NEUTRAL, dark_color="#9CA3AF"), compound="left",
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=100, height=36, corner_radius=RADIUS_BUTTON,
            fg_color="transparent", border_width=1,
            border_color=NEUTRAL, text_color=NEUTRAL, hover_color="#F3F4F6"
        ).pack(side="left", padx=S)

    def save(self):
        """บันทึก"""
        try:
            weight = float(self.weight_var.get())
            height = float(self.height_var.get())
        except ValueError:
            messagebox.showwarning("คำเตือน", "กรุณากรอกตัวเลขที่ถูกต้อง")
            return

        bmi = weight / ((height / 100) ** 2)

        health_data = {
            'student_id': self.student_id,
            'record_date': self.date_var.get(),
            'brushed_teeth': 0, 'drank_milk': 0,
            'weight_kg': weight, 'height_cm': height,
            'bmi': round(bmi, 2),
        }

        if self.db.save_health_record(health_data):
            self.update_status("บันทึกน้ำหนัก-ส่วนสูงเรียบร้อย", "success")
            self.callback()
            self.destroy()
        else:
            messagebox.showerror("ผิดพลาด", "ไม่สามารถบันทึกได้")
