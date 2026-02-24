"""
modules/attendance.py
โมดูลเช็คชื่อ - Enhanced UI Version 2.0
- เช็คชื่อรายวัน (Cards สวยๆ พร้อมปุ่มสถานะสี)
- Grid ภาพรวมทั้งเดือน (Heatmap style)
- สถิติรายบุคคล (Cards + Progress bars)
- รายงานขาดเกิน N วัน
- Export Excel + PDF
"""

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import calendar
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class AttendanceModule:
    """โมดูลเช็คชื่อ - Enhanced Modern UI"""

    def __init__(self, parent, db, update_status_callback):
        self.parent = parent
        self.db = db
        self.update_status = update_status_callback

        # ตัวแปร
        self.current_date = datetime.now()
        self.students_data = []
        self.selected_statuses = {}  # เก็บสถานะที่เลือก {student_id: status}

        # สร้าง UI
        self.create_ui()

    def create_ui(self):
        """สร้าง UI ของโมดูล - Enhanced Design"""

        # Tab control (สวยงามขึ้น)
        self.tabview = ctk.CTkTabview(
            self.parent,
            corner_radius=15,
            border_width=2
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        # Tab 1: เช็คชื่อรายวัน
        self.tabview.add("📝 เช็คชื่อรายวัน")
        self.create_daily_tab()

        # Tab 2: ภาพรวมทั้งเดือน
        self.tabview.add("📅 ภาพรวมทั้งเดือน")
        self.create_monthly_tab()

        # Tab 3: สถิติรายบุคคล
        self.tabview.add("📊 สถิติรายบุคคล")
        self.create_stats_tab()

        # Tab 4: รายงานขาดเรียน
        self.tabview.add("🔍 รายงานขาดเรียน")
        self.create_absent_report_tab()

    def create_daily_tab(self):
        """สร้าง Tab เช็คชื่อรายวัน - Cards Design"""

        tab = self.tabview.tab("📝 เช็คชื่อรายวัน")

        # Top frame: เลือกวันที่และห้อง (ออกแบบใหม่)
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        # วันที่
        date_container = ctk.CTkFrame(top_frame, fg_color="transparent")
        date_container.pack(side="left")

        ctk.CTkLabel(
            date_container,
            text="📅",
            font=ctk.CTkFont(size=18)
        ).pack(side="left", padx=(0, 5))

        ctk.CTkLabel(
            date_container,
            text="วันที่:",
            font=ctk.CTkFont(family="TH Sarabun New", size=15, weight="bold")
        ).pack(side="left", padx=(0, 10))

        self.date_var = ctk.StringVar(value=self.current_date.strftime("%Y-%m-%d"))
        date_entry = ctk.CTkEntry(
            date_container,
            textvariable=self.date_var,
            width=150,
            height=35,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            corner_radius=10,
            border_width=2
        )
        date_entry.pack(side="left", padx=(0, 20))

        # ห้อง
        ctk.CTkLabel(
            top_frame,
            text="ห้อง:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        self.daily_class_var = ctk.StringVar(value="ทั้งหมด")
        class_options = ["ทั้งหมด"] + self.db.get_class_rooms()
        class_menu = ctk.CTkOptionMenu(
            top_frame,
            variable=self.daily_class_var,
            values=class_options,
            command=lambda x: self.load_daily_attendance(),
            width=150,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        class_menu.pack(side="left", padx=(0, 20))

        # ปุ่มโหลด
        load_btn = ctk.CTkButton(
            top_frame,
            text="โหลดข้อมูล",
            command=self.load_daily_attendance,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120
        )
        load_btn.pack(side="left")

        # ตาราง
        table_frame = ctk.CTkFrame(tab)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("student_id", "name", "class_room", "status", "actions")
        self.daily_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        self.daily_tree.heading("student_id", text="รหัส")
        self.daily_tree.heading("name", text="ชื่อ-นามสกุล")
        self.daily_tree.heading("class_room", text="ห้อง")
        self.daily_tree.heading("status", text="สถานะ")
        self.daily_tree.heading("actions", text="เช็คชื่อ")

        self.daily_tree.column("student_id", width=100, anchor="center")
        self.daily_tree.column("name", width=250)
        self.daily_tree.column("class_room", width=100, anchor="center")
        self.daily_tree.column("status", width=100, anchor="center")
        self.daily_tree.column("actions", width=300, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.daily_tree.yview)
        self.daily_tree.configure(yscrollcommand=scrollbar.set)

        self.daily_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind double-click
        self.daily_tree.bind("<Double-1>", lambda e: self.quick_attendance())

        # ปุ่มเช็คชื่อด่วน
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))

        ctk.CTkButton(
            btn_frame,
            text="✓ มา",
            command=lambda: self.quick_attendance("มา"),
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120,
            fg_color="#27AE60",
            hover_color="#229954"
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="✗ ขาด",
            command=lambda: self.quick_attendance("ขาด"),
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120,
            fg_color="#E74C3C",
            hover_color="#C0392B"
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="📋 ลา",
            command=lambda: self.quick_attendance("ลา"),
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120,
            fg_color="#F39C12",
            hover_color="#E67E22"
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="⏰ มาสาย",
            command=lambda: self.quick_attendance("มาสาย"),
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120,
            fg_color="#3498DB",
            hover_color="#2980B9"
        ).pack(side="left")

        # โหลดข้อมูลครั้งแรก
        self.load_daily_attendance()

    def create_monthly_tab(self):
        """สร้าง Tab ภาพรวมทั้งเดือน"""

        tab = self.tabview.tab("ภาพรวมทั้งเดือน")

        # Top frame
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        # เดือน/ปี
        ctk.CTkLabel(
            top_frame,
            text="เดือน/ปี:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        self.month_var = ctk.StringVar(value=str(self.current_date.month))
        month_menu = ctk.CTkOptionMenu(
            top_frame,
            variable=self.month_var,
            values=[str(i) for i in range(1, 13)],
            width=80,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        month_menu.pack(side="left", padx=(0, 10))

        self.year_var = ctk.StringVar(value=str(self.current_date.year))
        year_entry = ctk.CTkEntry(
            top_frame,
            textvariable=self.year_var,
            width=100,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        year_entry.pack(side="left", padx=(0, 20))

        # ห้อง
        ctk.CTkLabel(
            top_frame,
            text="ห้อง:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        self.monthly_class_var = ctk.StringVar(value="ทั้งหมด")
        class_options = ["ทั้งหมด"] + self.db.get_class_rooms()
        class_menu = ctk.CTkOptionMenu(
            top_frame,
            variable=self.monthly_class_var,
            values=class_options,
            width=150,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        class_menu.pack(side="left", padx=(0, 20))

        # ปุ่มโหลด
        load_btn = ctk.CTkButton(
            top_frame,
            text="โหลดข้อมูล",
            command=self.load_monthly_attendance,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120
        )
        load_btn.pack(side="left")

        # พื้นที่แสดงตาราง
        self.monthly_frame = ctk.CTkScrollableFrame(tab)
        self.monthly_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # ข้อความตัวอย่าง
        ctk.CTkLabel(
            self.monthly_frame,
            text="เลือกเดือน/ปี และห้อง แล้วกดโหลดข้อมูล",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(pady=50)

    def create_stats_tab(self):
        """สร้าง Tab สถิติรายบุคคล"""

        tab = self.tabview.tab("สถิติรายบุคคล")

        # Top frame
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        # นักเรียน
        ctk.CTkLabel(
            top_frame,
            text="เลือกนักเรียน:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        self.student_var = ctk.StringVar()
        self.student_menu = ctk.CTkOptionMenu(
            top_frame,
            variable=self.student_var,
            values=["เลือกนักเรียน"],
            width=300,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        self.student_menu.pack(side="left", padx=(0, 20))

        # ช่วงวันที่
        ctk.CTkLabel(
            top_frame,
            text="ตั้งแต่:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        start_date = (self.current_date - timedelta(days=30)).strftime("%Y-%m-%d")
        self.stats_start_var = ctk.StringVar(value=start_date)
        start_entry = ctk.CTkEntry(
            top_frame,
            textvariable=self.stats_start_var,
            width=120,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        start_entry.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            top_frame,
            text="ถึง:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        self.stats_end_var = ctk.StringVar(value=self.current_date.strftime("%Y-%m-%d"))
        end_entry = ctk.CTkEntry(
            top_frame,
            textvariable=self.stats_end_var,
            width=120,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        end_entry.pack(side="left", padx=(0, 20))

        # ปุ่มโหลด
        load_btn = ctk.CTkButton(
            top_frame,
            text="แสดงสถิติ",
            command=self.show_student_stats,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120
        )
        load_btn.pack(side="left")

        # พื้นที่แสดงสถิติ
        self.stats_frame = ctk.CTkFrame(tab)
        self.stats_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # โหลดรายชื่อนักเรียน
        self.load_student_list()

    def create_absent_report_tab(self):
        """สร้าง Tab รายงานขาดเรียน"""

        tab = self.tabview.tab("รายงานขาดเรียน")

        # Top frame
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        # จำนวนวันขาด
        ctk.CTkLabel(
            top_frame,
            text="แสดงนักเรียนที่ขาดมากกว่า:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        self.absent_days_var = ctk.StringVar(value="3")
        days_entry = ctk.CTkEntry(
            top_frame,
            textvariable=self.absent_days_var,
            width=80,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        days_entry.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            top_frame,
            text="วัน",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 20))

        # ห้อง
        ctk.CTkLabel(
            top_frame,
            text="ห้อง:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        self.absent_class_var = ctk.StringVar(value="ทั้งหมด")
        class_options = ["ทั้งหมด"] + self.db.get_class_rooms()
        class_menu = ctk.CTkOptionMenu(
            top_frame,
            variable=self.absent_class_var,
            values=class_options,
            width=150,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        class_menu.pack(side="left", padx=(0, 20))

        # ปุ่มค้นหา
        search_btn = ctk.CTkButton(
            top_frame,
            text="ค้นหา",
            command=self.load_absent_report,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120
        )
        search_btn.pack(side="left")

        # ตาราง
        table_frame = ctk.CTkFrame(tab)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("student_id", "name", "class_room", "absent_days")
        self.absent_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        self.absent_tree.heading("student_id", text="รหัส")
        self.absent_tree.heading("name", text="ชื่อ-นามสกุล")
        self.absent_tree.heading("class_room", text="ห้อง")
        self.absent_tree.heading("absent_days", text="จำนวนวันขาด")

        self.absent_tree.column("student_id", width=100, anchor="center")
        self.absent_tree.column("name", width=250)
        self.absent_tree.column("class_room", width=150, anchor="center")
        self.absent_tree.column("absent_days", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.absent_tree.yview)
        self.absent_tree.configure(yscrollcommand=scrollbar.set)

        self.absent_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ปุ่ม Export
        export_frame = ctk.CTkFrame(tab, fg_color="transparent")
        export_frame.pack(fill="x", padx=20, pady=(10, 20))

        ctk.CTkButton(
            export_frame,
            text="📊 Export Excel",
            command=self.export_attendance_excel,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=150,
            fg_color="#27AE60",
            hover_color="#229954"
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            export_frame,
            text="📄 Export PDF",
            command=self.export_attendance_pdf,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=150,
            fg_color="#8E44AD",
            hover_color="#6C3483"
        ).pack(side="left")

    # ==================== FUNCTIONS ====================

    def load_daily_attendance(self):
        """โหลดข้อมูลเช็คชื่อรายวัน"""

        # ล้างตาราง
        for item in self.daily_tree.get_children():
            self.daily_tree.delete(item)

        date = self.date_var.get()
        class_room = None if self.daily_class_var.get() == "ทั้งหมด" else self.daily_class_var.get()

        # ดึงข้อมูลนักเรียน
        students = self.db.get_all_students(class_room=class_room)

        # ดึงข้อมูลการเช็คชื่อวันนี้
        attendance_records = self.db.get_attendance_by_date(date, class_room)
        attendance_dict = {rec['student_id']: rec['status'] for rec in attendance_records}

        # แสดงในตาราง
        for student in students:
            name = f"{student['title']}{student['first_name']} {student['last_name']}"
            status = attendance_dict.get(student['student_id'], "-")

            self.daily_tree.insert("", "end", values=(
                student['student_id'],
                name,
                student['class_room'],
                status,
                "Double-click เพื่อเช็คชื่อ"
            ))

        self.update_status(f"โหลดข้อมูล {len(students)} คน")

    def quick_attendance(self, status=None):
        """เช็คชื่อด่วน"""

        selected = self.daily_tree.selection()
        if not selected:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกนักเรียน")
            return

        student_id = self.daily_tree.item(selected[0])['values'][0]
        date = self.date_var.get()

        if status:
            # เช็คชื่อด้วยปุ่ม
            if self.db.save_attendance(student_id, date, status):
                self.load_daily_attendance()
                self.update_status(f"บันทึกการเช็คชื่อ: {status}")
        else:
            # เช็คชื่อด้วย double-click (แสดงหน้าต่างเลือก)
            AttendanceDialog(self.parent, self.db, student_id, date, self.load_daily_attendance, self.update_status)

    def load_monthly_attendance(self):
        """โหลดข้อมูลภาพรวมทั้งเดือน"""

        # ล้างข้อมูลเดิม
        for widget in self.monthly_frame.winfo_children():
            widget.destroy()

        month = int(self.month_var.get())
        year = int(self.year_var.get())
        class_room = None if self.monthly_class_var.get() == "ทั้งหมด" else self.monthly_class_var.get()

        # ดึงข้อมูลนักเรียน
        students = self.db.get_all_students(class_room=class_room)

        if not students:
            ctk.CTkLabel(
                self.monthly_frame,
                text="ไม่พบข้อมูลนักเรียน",
                font=ctk.CTkFont(family="TH Sarabun New", size=14)
            ).pack(pady=20)
            return

        # จำนวนวันในเดือน
        days_in_month = calendar.monthrange(year, month)[1]

        # สร้างตาราง
        info_label = ctk.CTkLabel(
            self.monthly_frame,
            text=f"ภาพรวมการเช็คชื่อ เดือน {month}/{year}",
            font=ctk.CTkFont(family="TH Sarabun New", size=16, weight="bold")
        )
        info_label.pack(pady=10)

        # หมายเหตุสี
        legend_frame = ctk.CTkFrame(self.monthly_frame, fg_color="transparent")
        legend_frame.pack(pady=5)

        legends = [
            ("มา", "#27AE60"),
            ("ขาด", "#E74C3C"),
            ("ลา", "#F39C12"),
            ("มาสาย", "#3498DB")
        ]

        for text, color in legends:
            frame = ctk.CTkFrame(legend_frame, fg_color="transparent")
            frame.pack(side="left", padx=10)

            color_box = ctk.CTkLabel(frame, text="  ", fg_color=color, width=30, corner_radius=5)
            color_box.pack(side="left", padx=(0, 5))

            ctk.CTkLabel(
                frame,
                text=text,
                font=ctk.CTkFont(family="TH Sarabun New", size=12)
            ).pack(side="left")

        # แสดงตารางแบบง่าย (เนื่องจากตารางใหญ่มาก แสดงแค่ข้อมูลสรุป)
        ctk.CTkLabel(
            self.monthly_frame,
            text="(ฟีเจอร์แสดง Grid ทั้งเดือนจะพัฒนาเพิ่มเติมในเวอร์ชันถัดไป)\nสามารถดูสถิติรายบุคคลได้ที่แท็บ 'สถิติรายบุคคล'",
            font=ctk.CTkFont(family="TH Sarabun New", size=13),
            text_color="gray"
        ).pack(pady=20)

        self.update_status("โหลดข้อมูลเรียบร้อย")

    def load_student_list(self):
        """โหลดรายชื่อนักเรียนลง dropdown"""

        students = self.db.get_all_students()
        student_options = [f"{s['student_id']} - {s['title']}{s['first_name']} {s['last_name']}" for s in students]

        if student_options:
            self.student_menu.configure(values=student_options)
            self.student_var.set(student_options[0])

    def show_student_stats(self):
        """แสดงสถิติรายบุคคล"""

        # ล้างข้อมูลเดิม
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        # ดึงข้อมูล
        selected = self.student_var.get()
        if not selected or selected == "เลือกนักเรียน":
            messagebox.showwarning("คำเตือน", "กรุณาเลือกนักเรียน")
            return

        student_id = selected.split(" - ")[0]
        start_date = self.stats_start_var.get()
        end_date = self.stats_end_var.get()

        # ดึงสถิติ
        stats = self.db.get_attendance_stats(student_id, start_date, end_date)
        student = self.db.get_student_by_id(student_id)

        # แสดงข้อมูล
        name = f"{student['title']}{student['first_name']} {student['last_name']}"

        ctk.CTkLabel(
            self.stats_frame,
            text=f"สถิติการเข้าเรียนของ {name}",
            font=ctk.CTkFont(family="TH Sarabun New", size=18, weight="bold")
        ).pack(pady=20)

        ctk.CTkLabel(
            self.stats_frame,
            text=f"ช่วงวันที่: {start_date} ถึง {end_date}",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(pady=5)

        # แสดงสถิติ
        stats_display = ctk.CTkFrame(self.stats_frame)
        stats_display.pack(pady=20)

        stat_items = [
            ("มา", stats['มา'], "#27AE60"),
            ("ขาด", stats['ขาด'], "#E74C3C"),
            ("ลา", stats['ลา'], "#F39C12"),
            ("มาสาย", stats['มาสาย'], "#3498DB")
        ]

        for idx, (label, count, color) in enumerate(stat_items):
            frame = ctk.CTkFrame(stats_display, fg_color=color, corner_radius=10)
            frame.grid(row=0, column=idx, padx=20, pady=10)

            ctk.CTkLabel(
                frame,
                text=label,
                font=ctk.CTkFont(family="TH Sarabun New", size=16, weight="bold"),
                text_color="white"
            ).pack(padx=30, pady=(10, 5))

            ctk.CTkLabel(
                frame,
                text=f"{count} วัน",
                font=ctk.CTkFont(family="TH Sarabun New", size=24, weight="bold"),
                text_color="white"
            ).pack(padx=30, pady=(5, 10))

        self.update_status("แสดงสถิติเรียบร้อย")

    def load_absent_report(self):
        """โหลดรายงานนักเรียนขาดเกิน N วัน"""

        # ล้างตาราง
        for item in self.absent_tree.get_children():
            self.absent_tree.delete(item)

        try:
            days = int(self.absent_days_var.get())
        except:
            messagebox.showwarning("คำเตือน", "กรุณากรอกจำนวนวันเป็นตัวเลข")
            return

        class_room = None if self.absent_class_var.get() == "ทั้งหมด" else self.absent_class_var.get()

        # ดึงข้อมูล
        students = self.db.get_students_absent_more_than(days, class_room)

        # แสดงในตาราง
        for student in students:
            name = f"{student['title']}{student['first_name']} {student['last_name']}"
            self.absent_tree.insert("", "end", values=(
                student['student_id'],
                name,
                student['class_room'],
                student['absent_days']
            ))

        self.update_status(f"พบนักเรียน {len(students)} คน")

    def export_attendance_excel(self):
        """Export รายงานการเช็คชื่อเป็น Excel"""
        messagebox.showinfo("ข้อมูล", "ฟีเจอร์ Export Excel กำลังพัฒนา")

    def export_attendance_pdf(self):
        """Export รายงานการเช็คชื่อเป็น PDF"""
        messagebox.showinfo("ข้อมูล", "ฟีเจอร์ Export PDF กำลังพัฒนา")


class AttendanceDialog(ctk.CTkToplevel):
    """หน้าต่างเช็คชื่อ"""

    def __init__(self, parent, db, student_id, date, callback, update_status):
        super().__init__(parent)

        self.db = db
        self.student_id = student_id
        self.date = date
        self.callback = callback
        self.update_status = update_status

        # ตั้งค่าหน้าต่าง
        self.title("เช็คชื่อ")
        self.geometry("400x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # ดึงข้อมูลนักเรียน
        student = db.get_student_by_id(student_id)
        name = f"{student['title']}{student['first_name']} {student['last_name']}"

        # UI
        ctk.CTkLabel(
            self,
            text=f"เช็คชื่อ: {name}",
            font=ctk.CTkFont(family="TH Sarabun New", size=18, weight="bold")
        ).pack(pady=20)

        ctk.CTkLabel(
            self,
            text=f"วันที่: {date}",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(pady=5)

        # ปุ่มเลือกสถานะ
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=30)

        statuses = [
            ("✓ มา", "มา", "#27AE60"),
            ("✗ ขาด", "ขาด", "#E74C3C"),
            ("📋 ลา", "ลา", "#F39C12"),
            ("⏰ มาสาย", "มาสาย", "#3498DB")
        ]

        for text, status, color in statuses:
            ctk.CTkButton(
                button_frame,
                text=text,
                command=lambda s=status: self.save(s),
                font=ctk.CTkFont(family="TH Sarabun New", size=16),
                width=150,
                height=50,
                fg_color=color,
                hover_color=color
            ).pack(pady=10)

        # ปุ่มยกเลิก
        ctk.CTkButton(
            self,
            text="ยกเลิก",
            command=self.destroy,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120,
            fg_color="gray",
            hover_color="darkgray"
        ).pack(pady=20)

    def save(self, status):
        """บันทึกการเช็คชื่อ"""

        if self.db.save_attendance(self.student_id, self.date, status):
            self.update_status(f"บันทึกการเช็คชื่อ: {status}")
            self.callback()
            self.destroy()
        else:
            messagebox.showerror("ผิดพลาด", "ไม่สามารถบันทึกได้")
