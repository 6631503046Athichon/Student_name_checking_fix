"""
modules/schedule.py
โมดูลตารางเรียน
- Grid จ-ศ × คาบ 1-8
- มุมมองครู + มุมมองห้อง
- ตรวจจับความขัดแย้ง (teacher_id+day+period ซ้ำ)
- แสดงภาระงานครู
- Export PDF
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


class ScheduleModule:
    """โมดูลตารางเรียน"""

    def __init__(self, parent, db, update_status_callback):
        self.parent = parent
        self.db = db
        self.update_status = update_status_callback

        # ตัวแปร
        self.days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์"]
        self.periods = list(range(1, 9))  # คาบ 1-8
        self.period_times = [
            ("08:00", "09:00"),
            ("09:00", "10:00"),
            ("10:00", "11:00"),
            ("11:00", "12:00"),
            ("13:00", "14:00"),
            ("14:00", "15:00"),
            ("15:00", "16:00"),
            ("16:00", "17:00")
        ]

        # สร้าง UI
        self.create_ui()

    def create_ui(self):
        """สร้าง UI ของโมดูล"""

        # Tab control
        self.tabview = ctk.CTkTabview(self.parent)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        # Tab 1: มุมมองห้องเรียน
        self.tabview.add("มุมมองห้องเรียน")
        self.create_class_view_tab()

        # Tab 2: มุมมองครู
        self.tabview.add("มุมมองครู")
        self.create_teacher_view_tab()

        # Tab 3: จัดการครู
        self.tabview.add("จัดการครู")
        self.create_teacher_management_tab()

        # Tab 4: ภาระงานครู
        self.tabview.add("ภาระงานครู")
        self.create_workload_tab()

    def create_class_view_tab(self):
        """สร้าง Tab มุมมองห้องเรียน"""

        tab = self.tabview.tab("มุมมองห้องเรียน")

        # Top frame
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        # เลือกห้อง
        ctk.CTkLabel(
            top_frame,
            text="เลือกห้อง:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        self.class_var = ctk.StringVar()
        class_options = self.db.get_class_rooms()
        if class_options:
            self.class_var.set(class_options[0])

        class_menu = ctk.CTkOptionMenu(
            top_frame,
            variable=self.class_var,
            values=class_options if class_options else ["ไม่มีห้อง"],
            width=150,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            command=lambda x: self.load_class_schedule()
        )
        class_menu.pack(side="left", padx=(0, 20))

        # ปุ่ม
        ctk.CTkButton(
            top_frame,
            text="โหลดข้อมูล",
            command=self.load_class_schedule,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            top_frame,
            text="➕ เพิ่มคาบเรียน",
            command=self.add_schedule,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=140
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            top_frame,
            text="📄 Export PDF",
            command=self.export_class_schedule_pdf,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=140,
            fg_color="#8E44AD",
            hover_color="#6C3483"
        ).pack(side="left")

        # ตาราง
        table_frame = ctk.CTkScrollableFrame(tab)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.class_schedule_frame = table_frame

        # โหลดข้อมูลครั้งแรก
        if class_options:
            self.load_class_schedule()

    def create_teacher_view_tab(self):
        """สร้าง Tab มุมมองครู"""

        tab = self.tabview.tab("มุมมองครู")

        # Top frame
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        # เลือกครู
        ctk.CTkLabel(
            top_frame,
            text="เลือกครู:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        self.teacher_var = ctk.StringVar()
        self.teacher_menu = ctk.CTkOptionMenu(
            top_frame,
            variable=self.teacher_var,
            values=["เลือกครู"],
            width=300,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            command=lambda x: self.load_teacher_schedule()
        )
        self.teacher_menu.pack(side="left", padx=(0, 20))

        # ปุ่ม
        ctk.CTkButton(
            top_frame,
            text="โหลดข้อมูล",
            command=self.load_teacher_schedule,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            top_frame,
            text="📄 Export PDF",
            command=self.export_teacher_schedule_pdf,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=140,
            fg_color="#8E44AD",
            hover_color="#6C3483"
        ).pack(side="left")

        # ตาราง
        table_frame = ctk.CTkScrollableFrame(tab)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.teacher_schedule_frame = table_frame

        # โหลดรายชื่อครู
        self.load_teacher_list()

    def create_teacher_management_tab(self):
        """สร้าง Tab จัดการครู"""

        tab = self.tabview.tab("จัดการครู")

        # Top frame
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkButton(
            top_frame,
            text="➕ เพิ่มครู",
            command=self.add_teacher,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=140
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            top_frame,
            text="🔄 รีเฟรช",
            command=self.load_teachers,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120
        ).pack(side="left")

        # ตาราง
        table_frame = ctk.CTkFrame(tab)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("teacher_id", "name", "phone")
        self.teacher_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        self.teacher_tree.heading("teacher_id", text="รหัสครู")
        self.teacher_tree.heading("name", text="ชื่อ-นามสกุล")
        self.teacher_tree.heading("phone", text="เบอร์ติดต่อ")

        self.teacher_tree.column("teacher_id", width=100, anchor="center")
        self.teacher_tree.column("name", width=300)
        self.teacher_tree.column("phone", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.teacher_tree.yview)
        self.teacher_tree.configure(yscrollcommand=scrollbar.set)

        self.teacher_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind
        self.teacher_tree.bind("<Double-1>", lambda e: self.edit_teacher())

        # ปุ่มด้านล่าง
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))

        ctk.CTkButton(
            btn_frame,
            text="✏️ แก้ไข",
            command=self.edit_teacher,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120,
            fg_color="#F39C12",
            hover_color="#E67E22"
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="🗑️ ลบ",
            command=self.delete_teacher,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=100,
            fg_color="#E74C3C",
            hover_color="#C0392B"
        ).pack(side="left")

        # โหลดข้อมูลครั้งแรก
        self.load_teachers()

    def create_workload_tab(self):
        """สร้าง Tab ภาระงานครู"""

        tab = self.tabview.tab("ภาระงานครู")

        # Top frame
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkButton(
            top_frame,
            text="🔄 รีเฟรช",
            command=self.load_workload,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120
        ).pack(side="left")

        # ตาราง
        table_frame = ctk.CTkFrame(tab)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("teacher_id", "name", "periods")
        self.workload_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        self.workload_tree.heading("teacher_id", text="รหัสครู")
        self.workload_tree.heading("name", text="ชื่อ-นามสกุล")
        self.workload_tree.heading("periods", text="จำนวนคาบ/สัปดาห์")

        self.workload_tree.column("teacher_id", width=150, anchor="center")
        self.workload_tree.column("name", width=350)
        self.workload_tree.column("periods", width=200, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.workload_tree.yview)
        self.workload_tree.configure(yscrollcommand=scrollbar.set)

        self.workload_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # โหลดข้อมูลครั้งแรก
        self.load_workload()

    # ==================== FUNCTIONS ====================

    def load_class_schedule(self):
        """โหลดตารางเรียนของห้อง"""

        # ล้างข้อมูลเดิม
        for widget in self.class_schedule_frame.winfo_children():
            widget.destroy()

        class_room = self.class_var.get()
        if not class_room:
            return

        # ดึงข้อมูล
        schedules = self.db.get_schedule_by_class(class_room)

        # สร้างตารางแบบ Grid
        # หัวตาราง
        ctk.CTkLabel(
            self.class_schedule_frame,
            text=f"ตารางเรียนห้อง {class_room}",
            font=ctk.CTkFont(family="TH Sarabun New", size=18, weight="bold")
        ).grid(row=0, column=0, columnspan=6, pady=20)

        # หัวคอลัมน์
        ctk.CTkLabel(
            self.class_schedule_frame,
            text="คาบ/วัน",
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            fg_color="#1F4E78",
            text_color="white",
            corner_radius=5,
            width=100
        ).grid(row=1, column=0, padx=2, pady=2, sticky="ew")

        for col, day in enumerate(self.days, start=1):
            ctk.CTkLabel(
                self.class_schedule_frame,
                text=day,
                font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
                fg_color="#1F4E78",
                text_color="white",
                corner_radius=5,
                width=150
            ).grid(row=1, column=col, padx=2, pady=2, sticky="ew")

        # สร้าง dict สำหรับค้นหา
        schedule_dict = {}
        for s in schedules:
            key = (s['day_of_week'], s['period_no'])
            schedule_dict[key] = s

        # แสดงข้อมูล
        for row, period in enumerate(self.periods, start=2):
            # คาบที่
            start_time, end_time = self.period_times[period - 1]
            ctk.CTkLabel(
                self.class_schedule_frame,
                text=f"คาบ {period}\n{start_time}-{end_time}",
                font=ctk.CTkFont(family="TH Sarabun New", size=12),
                fg_color="#34495E",
                text_color="white",
                corner_radius=5
            ).grid(row=row, column=0, padx=2, pady=2, sticky="nsew")

            # แต่ละวัน
            for col, day in enumerate(self.days, start=1):
                key = (day, period)
                if key in schedule_dict:
                    s = schedule_dict[key]
                    teacher_name = f"{s['title']}{s['first_name']} {s['last_name']}"
                    text = f"{s['subject_name']}\n{teacher_name}"
                    fg_color = "#27AE60"
                else:
                    text = "ว่าง"
                    fg_color = "#ECF0F1"

                label = ctk.CTkLabel(
                    self.class_schedule_frame,
                    text=text,
                    font=ctk.CTkFont(family="TH Sarabun New", size=11),
                    fg_color=fg_color,
                    text_color="white" if key in schedule_dict else "black",
                    corner_radius=5,
                    wraplength=140
                )
                label.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

                # Bind click event
                if key in schedule_dict:
                    schedule_id = s['id']
                    label.bind("<Button-1>", lambda e, sid=schedule_id: self.edit_schedule_entry(sid))

        self.update_status(f"โหลดตารางห้อง {class_room} เรียบร้อย")

    def load_teacher_list(self):
        """โหลดรายชื่อครู"""

        teachers = self.db.get_all_teachers()
        teacher_options = [f"{t['teacher_id']} - {t['title']}{t['first_name']} {t['last_name']}" for t in teachers]

        if teacher_options:
            self.teacher_menu.configure(values=teacher_options)
            self.teacher_var.set(teacher_options[0])
            self.load_teacher_schedule()

    def load_teacher_schedule(self):
        """โหลดตารางสอนของครู"""

        # ล้างข้อมูลเดิม
        for widget in self.teacher_schedule_frame.winfo_children():
            widget.destroy()

        selected = self.teacher_var.get()
        if not selected or selected == "เลือกครู":
            return

        teacher_id = selected.split(" - ")[0]
        teacher = self.db.get_teacher_by_id(teacher_id)
        teacher_name = f"{teacher['title']}{teacher['first_name']} {teacher['last_name']}"

        # ดึงข้อมูล
        schedules = self.db.get_schedule_by_teacher(teacher_id)

        # หัวข้อ
        ctk.CTkLabel(
            self.teacher_schedule_frame,
            text=f"ตารางสอนของครู {teacher_name}",
            font=ctk.CTkFont(family="TH Sarabun New", size=18, weight="bold")
        ).grid(row=0, column=0, columnspan=6, pady=20)

        # หัวคอลัมน์
        ctk.CTkLabel(
            self.teacher_schedule_frame,
            text="คาบ/วัน",
            font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
            fg_color="#1F4E78",
            text_color="white",
            corner_radius=5,
            width=100
        ).grid(row=1, column=0, padx=2, pady=2, sticky="ew")

        for col, day in enumerate(self.days, start=1):
            ctk.CTkLabel(
                self.teacher_schedule_frame,
                text=day,
                font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
                fg_color="#1F4E78",
                text_color="white",
                corner_radius=5,
                width=150
            ).grid(row=1, column=col, padx=2, pady=2, sticky="ew")

        # สร้าง dict
        schedule_dict = {}
        for s in schedules:
            key = (s['day_of_week'], s['period_no'])
            schedule_dict[key] = s

        # แสดงข้อมูล
        for row, period in enumerate(self.periods, start=2):
            start_time, end_time = self.period_times[period - 1]
            ctk.CTkLabel(
                self.teacher_schedule_frame,
                text=f"คาบ {period}\n{start_time}-{end_time}",
                font=ctk.CTkFont(family="TH Sarabun New", size=12),
                fg_color="#34495E",
                text_color="white",
                corner_radius=5
            ).grid(row=row, column=0, padx=2, pady=2, sticky="nsew")

            for col, day in enumerate(self.days, start=1):
                key = (day, period)
                if key in schedule_dict:
                    s = schedule_dict[key]
                    text = f"{s['subject_name']}\nห้อง {s['class_room']}"
                    fg_color = "#3498DB"
                else:
                    text = "ว่าง"
                    fg_color = "#ECF0F1"

                ctk.CTkLabel(
                    self.teacher_schedule_frame,
                    text=text,
                    font=ctk.CTkFont(family="TH Sarabun New", size=11),
                    fg_color=fg_color,
                    text_color="white" if key in schedule_dict else "black",
                    corner_radius=5,
                    wraplength=140
                ).grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

        self.update_status(f"โหลดตารางสอนของครู {teacher_name} เรียบร้อย")

    def load_teachers(self):
        """โหลดข้อมูลครู"""

        # ล้างตาราง
        for item in self.teacher_tree.get_children():
            self.teacher_tree.delete(item)

        teachers = self.db.get_all_teachers()

        for teacher in teachers:
            name = f"{teacher['title']}{teacher['first_name']} {teacher['last_name']}"
            self.teacher_tree.insert("", "end", values=(
                teacher['teacher_id'],
                name,
                teacher['phone'] or "-"
            ))

        self.update_status(f"โหลดข้อมูลครู {len(teachers)} คน")

    def load_workload(self):
        """โหลดภาระงานครู"""

        # ล้างตาราง
        for item in self.workload_tree.get_children():
            self.workload_tree.delete(item)

        workloads = self.db.get_teacher_workload()

        for w in workloads:
            self.workload_tree.insert("", "end", values=(
                w['teacher_id'],
                w['name'],
                f"{w['periods_per_week']} คาบ"
            ))

        self.update_status("โหลดภาระงานครูเรียบร้อย")

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
        """ลบครู"""

        selected = self.teacher_tree.selection()
        if not selected:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกครูที่ต้องการลบ")
            return

        teacher_id = self.teacher_tree.item(selected[0])['values'][0]
        name = self.teacher_tree.item(selected[0])['values'][1]

        confirm = messagebox.askyesno("ยืนยันการลบ", f"ต้องการลบครู {name} หรือไม่?")

        if confirm:
            if self.db.delete_teacher(teacher_id):
                self.load_teachers()
                self.update_status(f"ลบครู {name} เรียบร้อย")
                messagebox.showinfo("สำเร็จ", "ลบครูเรียบร้อย")
            else:
                messagebox.showerror("ผิดพลาด", "ไม่สามารถลบครูได้")

    def add_schedule(self):
        """เพิ่มคาบเรียน"""

        class_room = self.class_var.get()
        if not class_room:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกห้องเรียน")
            return

        ScheduleDialog(
            self.parent,
            self.db,
            class_room,
            None,
            self.load_class_schedule,
            self.update_status
        )

    def edit_schedule_entry(self, schedule_id):
        """แก้ไขคาบเรียน"""

        # ดึงข้อมูล schedule
        schedules = self.db.get_all_schedules()
        schedule = next((s for s in schedules if s['id'] == schedule_id), None)

        if schedule:
            ScheduleDialog(
                self.parent,
                self.db,
                schedule['class_room'],
                schedule,
                self.load_class_schedule,
                self.update_status
            )

    def export_class_schedule_pdf(self):
        """Export ตารางเรียนเป็น PDF"""
        messagebox.showinfo("ข้อมูล", "ฟีเจอร์ Export PDF กำลังพัฒนา")

    def export_teacher_schedule_pdf(self):
        """Export ตารางสอนเป็น PDF"""
        messagebox.showinfo("ข้อมูล", "ฟีเจอร์ Export PDF กำลังพัฒนา")


class TeacherDialog(ctk.CTkToplevel):
    """หน้าต่างเพิ่ม/แก้ไขครู"""

    def __init__(self, parent, db, teacher, callback, update_status):
        super().__init__(parent)

        self.db = db
        self.teacher = teacher
        self.callback = callback
        self.update_status = update_status

        self.title("แก้ไขครู" if teacher else "เพิ่มครู")
        self.geometry("500x450")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.create_form()

        if teacher:
            self.fill_data()

    def create_form(self):
        """สร้างฟอร์ม"""

        # Title
        ctk.CTkLabel(
            self,
            text="แก้ไขข้อมูลครู" if self.teacher else "เพิ่มครูใหม่",
            font=ctk.CTkFont(family="TH Sarabun New", size=18, weight="bold")
        ).pack(pady=20)

        # Form
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(pady=10)

        # รหัสครู
        ctk.CTkLabel(
            form_frame,
            text="รหัสครู:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=0, column=0, sticky="w", pady=10, padx=(0, 10))

        self.teacher_id_var = ctk.StringVar()
        ctk.CTkEntry(
            form_frame,
            textvariable=self.teacher_id_var,
            width=250,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=0, column=1, pady=10)

        # คำนำหน้า
        ctk.CTkLabel(
            form_frame,
            text="คำนำหน้า:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=1, column=0, sticky="w", pady=10, padx=(0, 10))

        self.title_var = ctk.StringVar(value="นาย")
        ctk.CTkOptionMenu(
            form_frame,
            variable=self.title_var,
            values=["นาย", "นาง", "นางสาว"],
            width=250,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=1, column=1, pady=10)

        # ชื่อ
        ctk.CTkLabel(
            form_frame,
            text="ชื่อ:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=2, column=0, sticky="w", pady=10, padx=(0, 10))

        self.first_name_var = ctk.StringVar()
        ctk.CTkEntry(
            form_frame,
            textvariable=self.first_name_var,
            width=250,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=2, column=1, pady=10)

        # นามสกุล
        ctk.CTkLabel(
            form_frame,
            text="นามสกุล:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=3, column=0, sticky="w", pady=10, padx=(0, 10))

        self.last_name_var = ctk.StringVar()
        ctk.CTkEntry(
            form_frame,
            textvariable=self.last_name_var,
            width=250,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=3, column=1, pady=10)

        # เบอร์ติดต่อ
        ctk.CTkLabel(
            form_frame,
            text="เบอร์ติดต่อ:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=4, column=0, sticky="w", pady=10, padx=(0, 10))

        self.phone_var = ctk.StringVar()
        ctk.CTkEntry(
            form_frame,
            textvariable=self.phone_var,
            width=250,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=4, column=1, pady=10)

        # ปุ่ม
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=30)

        ctk.CTkButton(
            btn_frame,
            text="บันทึก",
            command=self.save,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=100
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="ยกเลิก",
            command=self.destroy,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=100,
            fg_color="gray",
            hover_color="darkgray"
        ).pack(side="left", padx=10)

    def fill_data(self):
        """ใส่ข้อมูลเดิม"""

        self.teacher_id_var.set(self.teacher['teacher_id'])
        self.title_var.set(self.teacher['title'])
        self.first_name_var.set(self.teacher['first_name'])
        self.last_name_var.set(self.teacher['last_name'])
        self.phone_var.set(self.teacher['phone'] or "")

    def save(self):
        """บันทึก"""

        # ตรวจสอบข้อมูล
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
            'phone': self.phone_var.get().strip() or None
        }

        if self.teacher:
            success = self.db.update_teacher(self.teacher['teacher_id'], teacher_data)
            message = "แก้ไขข้อมูลครูเรียบร้อย"
        else:
            success = self.db.add_teacher(teacher_data)
            message = "เพิ่มครูเรียบร้อย"

        if success:
            self.update_status(message)
            self.callback()
            messagebox.showinfo("สำเร็จ", message)
            self.destroy()
        else:
            messagebox.showerror("ผิดพลาด", "ไม่สามารถบันทึกได้")


class ScheduleDialog(ctk.CTkToplevel):
    """หน้าต่างเพิ่ม/แก้ไขตารางเรียน"""

    def __init__(self, parent, db, class_room, schedule, callback, update_status):
        super().__init__(parent)

        self.db = db
        self.class_room = class_room
        self.schedule = schedule
        self.callback = callback
        self.update_status = update_status

        self.title("แก้ไขคาบเรียน" if schedule else "เพิ่มคาบเรียน")
        self.geometry("500x550")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.create_form()

        if schedule:
            self.fill_data()

    def create_form(self):
        """สร้างฟอร์ม"""

        # Title
        ctk.CTkLabel(
            self,
            text=f"{'แก้ไข' if self.schedule else 'เพิ่ม'}คาบเรียน - ห้อง {self.class_room}",
            font=ctk.CTkFont(family="TH Sarabun New", size=18, weight="bold")
        ).pack(pady=20)

        # Form
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(pady=10)

        # วัน
        ctk.CTkLabel(
            form_frame,
            text="วัน:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=0, column=0, sticky="w", pady=10, padx=(0, 10))

        self.day_var = ctk.StringVar(value="จันทร์")
        ctk.CTkOptionMenu(
            form_frame,
            variable=self.day_var,
            values=["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์"],
            width=250,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=0, column=1, pady=10)

        # คาบที่
        ctk.CTkLabel(
            form_frame,
            text="คาบที่:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=1, column=0, sticky="w", pady=10, padx=(0, 10))

        self.period_var = ctk.StringVar(value="1")
        ctk.CTkOptionMenu(
            form_frame,
            variable=self.period_var,
            values=[str(i) for i in range(1, 9)],
            width=250,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=1, column=1, pady=10)

        # วิชา
        ctk.CTkLabel(
            form_frame,
            text="วิชา:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=2, column=0, sticky="w", pady=10, padx=(0, 10))

        self.subject_var = ctk.StringVar()
        ctk.CTkEntry(
            form_frame,
            textvariable=self.subject_var,
            width=250,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=2, column=1, pady=10)

        # ครูผู้สอน
        ctk.CTkLabel(
            form_frame,
            text="ครูผู้สอน:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=3, column=0, sticky="w", pady=10, padx=(0, 10))

        teachers = self.db.get_all_teachers()
        teacher_options = [f"{t['teacher_id']} - {t['title']}{t['first_name']} {t['last_name']}" for t in teachers]

        self.teacher_var = ctk.StringVar()
        if teacher_options:
            self.teacher_var.set(teacher_options[0])

        ctk.CTkOptionMenu(
            form_frame,
            variable=self.teacher_var,
            values=teacher_options if teacher_options else ["ไม่มีครู"],
            width=250,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=3, column=1, pady=10)

        # ห้องเรียน (room_no)
        ctk.CTkLabel(
            form_frame,
            text="ห้องเรียน:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=4, column=0, sticky="w", pady=10, padx=(0, 10))

        self.room_var = ctk.StringVar()
        ctk.CTkEntry(
            form_frame,
            textvariable=self.room_var,
            width=250,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            placeholder_text="เช่น 301, Lab1"
        ).grid(row=4, column=1, pady=10)

        # ปุ่ม
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=30)

        ctk.CTkButton(
            btn_frame,
            text="บันทึก",
            command=self.save,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=100
        ).pack(side="left", padx=10)

        if self.schedule:
            ctk.CTkButton(
                btn_frame,
                text="ลบ",
                command=self.delete,
                font=ctk.CTkFont(family="TH Sarabun New", size=14),
                width=100,
                fg_color="#E74C3C",
                hover_color="#C0392B"
            ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="ยกเลิก",
            command=self.destroy,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=100,
            fg_color="gray",
            hover_color="darkgray"
        ).pack(side="left", padx=10)

    def fill_data(self):
        """ใส่ข้อมูลเดิม"""

        self.day_var.set(self.schedule['day_of_week'])
        self.period_var.set(str(self.schedule['period_no']))
        self.subject_var.set(self.schedule['subject_name'])

        # หาครู
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

        # หาเวลา
        start_time, end_time = [
            ("08:00", "09:00"), ("09:00", "10:00"), ("10:00", "11:00"), ("11:00", "12:00"),
            ("13:00", "14:00"), ("14:00", "15:00"), ("15:00", "16:00"), ("16:00", "17:00")
        ][period - 1]

        schedule_data = {
            'class_room': self.class_room,
            'day_of_week': self.day_var.get(),
            'period_no': period,
            'start_time': start_time,
            'end_time': end_time,
            'subject_name': self.subject_var.get().strip(),
            'teacher_id': teacher_id,
            'room_no': self.room_var.get().strip() or None
        }

        if self.schedule:
            result = self.db.update_schedule(self.schedule['id'], schedule_data)
        else:
            result = self.db.add_schedule(schedule_data)

        # ตรวจสอบผลลัพธ์
        if result == True:
            message = "บันทึกตารางเรียนเรียบร้อย"
            self.update_status(message)
            self.callback()
            messagebox.showinfo("สำเร็จ", message)
            self.destroy()
        elif isinstance(result, str):
            # มี error message จากการตรวจสอบความขัดแย้ง
            messagebox.showerror("ความขัดแย้ง", result)
        else:
            messagebox.showerror("ผิดพลาด", "ไม่สามารถบันทึกได้")

    def delete(self):
        """ลบคาบเรียน"""

        confirm = messagebox.askyesno("ยืนยันการลบ", "ต้องการลบคาบเรียนนี้หรือไม่?")

        if confirm:
            if self.db.delete_schedule(self.schedule['id']):
                self.update_status("ลบคาบเรียนเรียบร้อย")
                self.callback()
                messagebox.showinfo("สำเร็จ", "ลบคาบเรียนเรียบร้อย")
                self.destroy()
            else:
                messagebox.showerror("ผิดพลาด", "ไม่สามารถลบได้")
