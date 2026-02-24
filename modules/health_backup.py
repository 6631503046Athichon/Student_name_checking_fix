"""
modules/health.py
โมดูลสุขภาพ
- Checkbox แปรงฟัน/ดื่มนม แบบ bulk
- บันทึก น้ำหนัก-ส่วนสูง คำนวณ BMI
- แสดงสถานะ BMI สีแดง/เขียว/ส้ม
- กราฟพัฒนาการ (matplotlib)
- Export Excel + PDF
"""

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('TkAgg')


class HealthModule:
    """โมดูลสุขภาพ"""

    def __init__(self, parent, db, update_status_callback):
        self.parent = parent
        self.db = db
        self.update_status = update_status_callback

        self.current_date = datetime.now()

        # สร้าง UI
        self.create_ui()

    def create_ui(self):
        """สร้าง UI ของโมดูล"""

        # Tab control
        self.tabview = ctk.CTkTabview(self.parent)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        # Tab 1: แปรงฟัน/ดื่มนม
        self.tabview.add("แปรงฟัน/ดื่มนม")
        self.create_daily_health_tab()

        # Tab 2: น้ำหนัก-ส่วนสูง
        self.tabview.add("น้ำหนัก-ส่วนสูง")
        self.create_weight_height_tab()

        # Tab 3: กราฟพัฒนาการ
        self.tabview.add("กราฟพัฒนาการ")
        self.create_growth_chart_tab()

    def create_daily_health_tab(self):
        """สร้าง Tab แปรงฟัน/ดื่มนม"""

        tab = self.tabview.tab("แปรงฟัน/ดื่มนม")

        # Top frame
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        # วันที่
        ctk.CTkLabel(
            top_frame,
            text="วันที่:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        self.health_date_var = ctk.StringVar(value=self.current_date.strftime("%Y-%m-%d"))
        date_entry = ctk.CTkEntry(
            top_frame,
            textvariable=self.health_date_var,
            width=150,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        date_entry.pack(side="left", padx=(0, 20))

        # ห้อง
        ctk.CTkLabel(
            top_frame,
            text="ห้อง:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        self.health_class_var = ctk.StringVar(value="ทั้งหมด")
        class_options = ["ทั้งหมด"] + self.db.get_class_rooms()
        class_menu = ctk.CTkOptionMenu(
            top_frame,
            variable=self.health_class_var,
            values=class_options,
            command=lambda x: self.load_daily_health(),
            width=150,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        class_menu.pack(side="left", padx=(0, 20))

        # ปุ่มโหลด
        load_btn = ctk.CTkButton(
            top_frame,
            text="โหลดข้อมูล",
            command=self.load_daily_health,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120
        )
        load_btn.pack(side="left")

        # ตาราง
        table_frame = ctk.CTkFrame(tab)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

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

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.health_tree.yview)
        self.health_tree.configure(yscrollcommand=scrollbar.set)

        self.health_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind
        self.health_tree.bind("<Double-1>", lambda e: self.toggle_health_status())

        # ปุ่มด้านล่าง
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))

        ctk.CTkButton(
            btn_frame,
            text="🦷 ติ๊กแปรงฟัน",
            command=lambda: self.toggle_health_status("brushed_teeth"),
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=140,
            fg_color="#3498DB",
            hover_color="#2980B9"
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="🥛 ติ๊กดื่มนม",
            command=lambda: self.toggle_health_status("drank_milk"),
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=140,
            fg_color="#F39C12",
            hover_color="#E67E22"
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="✓ ทำทั้งหมด",
            command=self.mark_all_health,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=140,
            fg_color="#27AE60",
            hover_color="#229954"
        ).pack(side="left")

        # โหลดข้อมูลครั้งแรก
        self.load_daily_health()

    def create_weight_height_tab(self):
        """สร้าง Tab น้ำหนัก-ส่วนสูง"""

        tab = self.tabview.tab("น้ำหนัก-ส่วนสูง")

        # Top frame
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        # เลือกนักเรียน
        ctk.CTkLabel(
            top_frame,
            text="เลือกนักเรียน:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        self.weight_student_var = ctk.StringVar()
        self.weight_student_menu = ctk.CTkOptionMenu(
            top_frame,
            variable=self.weight_student_var,
            values=["เลือกนักเรียน"],
            width=300,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            command=lambda x: self.load_weight_height_data()
        )
        self.weight_student_menu.pack(side="left", padx=(0, 20))

        # ปุ่มเพิ่มข้อมูล
        add_btn = ctk.CTkButton(
            top_frame,
            text="➕ บันทึกข้อมูล",
            command=self.add_weight_height,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=140
        )
        add_btn.pack(side="left")

        # แสดงข้อมูล BMI ล่าสุด
        self.bmi_frame = ctk.CTkFrame(tab)
        self.bmi_frame.pack(fill="x", padx=20, pady=10)

        self.bmi_info_label = ctk.CTkLabel(
            self.bmi_frame,
            text="เลือกนักเรียนเพื่อดูข้อมูล BMI",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        self.bmi_info_label.pack(pady=20)

        # ตารางประวัติ
        table_frame = ctk.CTkFrame(tab)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

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

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.weight_tree.yview)
        self.weight_tree.configure(yscrollcommand=scrollbar.set)

        self.weight_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # โหลดรายชื่อนักเรียน
        self.load_student_list_for_weight()

    def create_growth_chart_tab(self):
        """สร้าง Tab กราฟพัฒนาการ"""

        tab = self.tabview.tab("กราฟพัฒนาการ")

        # Top frame
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        # เลือกนักเรียน
        ctk.CTkLabel(
            top_frame,
            text="เลือกนักเรียน:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        self.chart_student_var = ctk.StringVar()
        self.chart_student_menu = ctk.CTkOptionMenu(
            top_frame,
            variable=self.chart_student_var,
            values=["เลือกนักเรียน"],
            width=300,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        self.chart_student_menu.pack(side="left", padx=(0, 20))

        # ปุ่มแสดงกราฟ
        show_btn = ctk.CTkButton(
            top_frame,
            text="📊 แสดงกราฟ",
            command=self.show_growth_chart,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=140
        )
        show_btn.pack(side="left")

        # พื้นที่แสดงกราฟ
        self.chart_frame = ctk.CTkFrame(tab)
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # โหลดรายชื่อนักเรียน
        self.load_student_list_for_chart()

    # ==================== FUNCTIONS ====================

    def load_daily_health(self):
        """โหลดข้อมูลสุขภาพรายวัน"""

        # ล้างตาราง
        for item in self.health_tree.get_children():
            self.health_tree.delete(item)

        date = self.health_date_var.get()
        class_room = None if self.health_class_var.get() == "ทั้งหมด" else self.health_class_var.get()

        # ดึงข้อมูลนักเรียน
        students = self.db.get_all_students(class_room=class_room)

        # ดึงข้อมูลสุขภาพวันนี้
        health_records = self.db.get_health_by_date(date, class_room)
        health_dict = {rec['student_id']: rec for rec in health_records}

        # แสดงในตาราง
        for student in students:
            name = f"{student['title']}{student['first_name']} {student['last_name']}"
            health = health_dict.get(student['student_id'], {})

            brushed = "✓" if health.get('brushed_teeth') else "✗"
            drank = "✓" if health.get('drank_milk') else "✗"

            self.health_tree.insert("", "end", values=(
                student['student_id'],
                name,
                student['class_room'],
                brushed,
                drank
            ))

        self.update_status(f"โหลดข้อมูล {len(students)} คน")

    def toggle_health_status(self, field=None):
        """สลับสถานะแปรงฟัน/ดื่มนม"""

        selected = self.health_tree.selection()
        if not selected:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกนักเรียน")
            return

        student_id = self.health_tree.item(selected[0])['values'][0]
        date = self.health_date_var.get()

        if not field:
            # Double-click แสดงหน้าต่างเลือก
            HealthDialog(self.parent, self.db, student_id, date, self.load_daily_health, self.update_status)
        else:
            # กดปุ่มเฉพาะ
            # ดึงข้อมูลปัจจุบัน
            current = self.health_tree.item(selected[0])['values']
            brushed = 0 if field == "drank_milk" else (0 if current[3] == "✗" else 1)
            drank = 0 if field == "brushed_teeth" else (0 if current[4] == "✗" else 1)

            # สลับค่า
            if field == "brushed_teeth":
                brushed = 1 - brushed
            else:
                drank = 1 - drank

            # บันทึก
            if self.db.update_health_daily(student_id, date, brushed, drank):
                self.load_daily_health()
                self.update_status("บันทึกข้อมูลสุขภาพเรียบร้อย")

    def mark_all_health(self):
        """ทำเครื่องหมายทั้งหมด"""

        date = self.health_date_var.get()
        class_room = None if self.health_class_var.get() == "ทั้งหมด" else self.health_class_var.get()

        students = self.db.get_all_students(class_room=class_room)

        confirm = messagebox.askyesno(
            "ยืนยัน",
            f"ต้องการทำเครื่องหมายแปรงฟัน และ ดื่มนม ให้นักเรียนทั้งหมด {len(students)} คน หรือไม่?"
        )

        if not confirm:
            return

        success = 0
        for student in students:
            if self.db.update_health_daily(student['student_id'], date, 1, 1):
                success += 1

        self.load_daily_health()
        self.update_status(f"บันทึกข้อมูล {success} คน")
        messagebox.showinfo("สำเร็จ", f"บันทึกข้อมูล {success} คน")

    def load_student_list_for_weight(self):
        """โหลดรายชื่อนักเรียนสำหรับน้ำหนัก-ส่วนสูง"""

        students = self.db.get_all_students()
        student_options = [f"{s['student_id']} - {s['title']}{s['first_name']} {s['last_name']}" for s in students]

        if student_options:
            self.weight_student_menu.configure(values=student_options)
            self.weight_student_var.set(student_options[0])
            self.load_weight_height_data()

    def load_student_list_for_chart(self):
        """โหลดรายชื่อนักเรียนสำหรับกราฟ"""

        students = self.db.get_all_students()
        student_options = [f"{s['student_id']} - {s['title']}{s['first_name']} {s['last_name']}" for s in students]

        if student_options:
            self.chart_student_menu.configure(values=student_options)
            self.chart_student_var.set(student_options[0])

    def load_weight_height_data(self):
        """โหลดข้อมูลน้ำหนัก-ส่วนสูง"""

        # ล้างตาราง
        for item in self.weight_tree.get_children():
            self.weight_tree.delete(item)

        # ดึงข้อมูล
        selected = self.weight_student_var.get()
        if not selected or selected == "เลือกนักเรียน":
            return

        student_id = selected.split(" - ")[0]
        records = self.db.get_health_records(student_id)

        # กรองเฉพาะที่มีน้ำหนัก/ส่วนสูง
        weight_records = [r for r in records if r['weight_kg'] or r['height_cm']]

        # แสดงในตาราง
        for record in weight_records:
            bmi = record['bmi'] if record['bmi'] else "-"
            status = self.get_bmi_status(record['bmi']) if record['bmi'] else "-"

            self.weight_tree.insert("", "end", values=(
                record['record_date'],
                record['weight_kg'] or "-",
                record['height_cm'] or "-",
                bmi if bmi != "-" else "-",
                status
            ))

        # แสดงข้อมูล BMI ล่าสุด
        latest = self.db.get_latest_health(student_id)
        if latest and latest['bmi']:
            bmi = latest['bmi']
            status = self.get_bmi_status(bmi)
            color = self.get_bmi_color(bmi)

            # ล้างข้อมูลเดิม
            for widget in self.bmi_frame.winfo_children():
                widget.destroy()

            info_frame = ctk.CTkFrame(self.bmi_frame, fg_color=color, corner_radius=10)
            info_frame.pack(pady=20, padx=20)

            ctk.CTkLabel(
                info_frame,
                text=f"BMI ล่าสุด: {bmi:.2f}",
                font=ctk.CTkFont(family="TH Sarabun New", size=20, weight="bold"),
                text_color="white"
            ).pack(padx=30, pady=(15, 5))

            ctk.CTkLabel(
                info_frame,
                text=f"สถานะ: {status}",
                font=ctk.CTkFont(family="TH Sarabun New", size=16),
                text_color="white"
            ).pack(padx=30, pady=(5, 15))

            ctk.CTkLabel(
                self.bmi_frame,
                text=f"น้ำหนัก: {latest['weight_kg']} kg  |  ส่วนสูง: {latest['height_cm']} cm",
                font=ctk.CTkFont(family="TH Sarabun New", size=14)
            ).pack(pady=5)

        self.update_status("โหลดข้อมูลเรียบร้อย")

    def get_bmi_status(self, bmi):
        """คำนวณสถานะ BMI"""
        if bmi < 18.5:
            return "น้ำหนักต่ำกว่าเกณฑ์"
        elif bmi < 23:
            return "น้ำหนักปกติ"
        elif bmi < 25:
            return "น้ำหนักเกิน"
        else:
            return "อ้วน"

    def get_bmi_color(self, bmi):
        """คำนวณสี BMI"""
        if bmi < 18.5:
            return "#E74C3C"  # แดง
        elif bmi < 23:
            return "#27AE60"  # เขียว
        else:
            return "#F39C12"  # ส้ม

    def add_weight_height(self):
        """เพิ่มข้อมูลน้ำหนัก-ส่วนสูง"""

        selected = self.weight_student_var.get()
        if not selected or selected == "เลือกนักเรียน":
            messagebox.showwarning("คำเตือน", "กรุณาเลือกนักเรียน")
            return

        student_id = selected.split(" - ")[0]
        WeightHeightDialog(
            self.parent,
            self.db,
            student_id,
            self.load_weight_height_data,
            self.update_status
        )

    def show_growth_chart(self):
        """แสดงกราฟพัฒนาการ"""

        # ล้างกราฟเดิม
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        # ดึงข้อมูล
        selected = self.chart_student_var.get()
        if not selected or selected == "เลือกนักเรียน":
            messagebox.showwarning("คำเตือน", "กรุณาเลือกนักเรียน")
            return

        student_id = selected.split(" - ")[0]
        student = self.db.get_student_by_id(student_id)
        records = self.db.get_health_records(student_id)

        # กรองเฉพาะที่มีข้อมูล
        weight_records = [r for r in records if r['weight_kg'] and r['height_cm']]

        if not weight_records:
            ctk.CTkLabel(
                self.chart_frame,
                text="ไม่มีข้อมูลเพียงพอสำหรับสร้างกราฟ",
                font=ctk.CTkFont(family="TH Sarabun New", size=14)
            ).pack(pady=50)
            return

        # เรียงตามวันที่
        weight_records.sort(key=lambda x: x['record_date'])

        # ดึงข้อมูล
        dates = [r['record_date'] for r in weight_records]
        weights = [r['weight_kg'] for r in weight_records]
        heights = [r['height_cm'] for r in weight_records]

        # สร้างกราฟ
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        # กราฟน้ำหนัก
        ax1.plot(dates, weights, marker='o', color='#3498DB', linewidth=2)
        ax1.set_title(f'กราฟน้ำหนัก - {student["title"]}{student["first_name"]} {student["last_name"]}',
                      fontsize=14, fontweight='bold', fontproperties='TH Sarabun New')
        ax1.set_xlabel('วันที่', fontsize=12)
        ax1.set_ylabel('น้ำหนัก (kg)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)

        # กราฟส่วนสูง
        ax2.plot(dates, heights, marker='s', color='#27AE60', linewidth=2)
        ax2.set_title('กราฟส่วนสูง', fontsize=14, fontweight='bold')
        ax2.set_xlabel('วันที่', fontsize=12)
        ax2.set_ylabel('ส่วนสูง (cm)', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)

        plt.tight_layout()

        # แสดงกราฟใน Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        self.update_status("แสดงกราฟพัฒนาการเรียบร้อย")


class HealthDialog(ctk.CTkToplevel):
    """หน้าต่างบันทึกสุขภาพรายวัน"""

    def __init__(self, parent, db, student_id, date, callback, update_status):
        super().__init__(parent)

        self.db = db
        self.student_id = student_id
        self.date = date
        self.callback = callback
        self.update_status = update_status

        self.title("บันทึกสุขภาพ")
        self.geometry("350x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # ดึงข้อมูลนักเรียน
        student = db.get_student_by_id(student_id)
        name = f"{student['title']}{student['first_name']} {student['last_name']}"

        # UI
        ctk.CTkLabel(
            self,
            text=f"บันทึกสุขภาพ: {name}",
            font=ctk.CTkFont(family="TH Sarabun New", size=16, weight="bold")
        ).pack(pady=20)

        # Checkbox
        self.brushed_var = ctk.IntVar()
        ctk.CTkCheckBox(
            self,
            text="🦷 แปรงฟัน",
            variable=self.brushed_var,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(pady=10)

        self.drank_var = ctk.IntVar()
        ctk.CTkCheckBox(
            self,
            text="🥛 ดื่มนม",
            variable=self.drank_var,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(pady=10)

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

    def save(self):
        """บันทึก"""

        brushed = self.brushed_var.get()
        drank = self.drank_var.get()

        if self.db.update_health_daily(self.student_id, self.date, brushed, drank):
            self.update_status("บันทึกข้อมูลสุขภาพเรียบร้อย")
            self.callback()
            self.destroy()
        else:
            messagebox.showerror("ผิดพลาด", "ไม่สามารถบันทึกได้")


class WeightHeightDialog(ctk.CTkToplevel):
    """หน้าต่างบันทึกน้ำหนัก-ส่วนสูง"""

    def __init__(self, parent, db, student_id, callback, update_status):
        super().__init__(parent)

        self.db = db
        self.student_id = student_id
        self.callback = callback
        self.update_status = update_status

        self.title("บันทึกน้ำหนัก-ส่วนสูง")
        self.geometry("400x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # ดึงข้อมูลนักเรียน
        student = db.get_student_by_id(student_id)
        name = f"{student['title']}{student['first_name']} {student['last_name']}"

        # UI
        ctk.CTkLabel(
            self,
            text=f"บันทึกน้ำหนัก-ส่วนสูง",
            font=ctk.CTkFont(family="TH Sarabun New", size=18, weight="bold")
        ).pack(pady=20)

        ctk.CTkLabel(
            self,
            text=name,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(pady=5)

        # Form
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(pady=20)

        # วันที่
        ctk.CTkLabel(
            form_frame,
            text="วันที่:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=0, column=0, sticky="w", pady=10, padx=(0, 10))

        self.date_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ctk.CTkEntry(
            form_frame,
            textvariable=self.date_var,
            width=200,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=0, column=1, pady=10)

        # น้ำหนัก
        ctk.CTkLabel(
            form_frame,
            text="น้ำหนัก (kg):",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=1, column=0, sticky="w", pady=10, padx=(0, 10))

        self.weight_var = ctk.StringVar()
        ctk.CTkEntry(
            form_frame,
            textvariable=self.weight_var,
            width=200,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=1, column=1, pady=10)

        # ส่วนสูง
        ctk.CTkLabel(
            form_frame,
            text="ส่วนสูง (cm):",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=2, column=0, sticky="w", pady=10, padx=(0, 10))

        self.height_var = ctk.StringVar()
        ctk.CTkEntry(
            form_frame,
            textvariable=self.height_var,
            width=200,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=2, column=1, pady=10)

        # ปุ่ม
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

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

    def save(self):
        """บันทึก"""

        try:
            weight = float(self.weight_var.get())
            height = float(self.height_var.get())
        except:
            messagebox.showwarning("คำเตือน", "กรุณากรอกตัวเลขที่ถูกต้อง")
            return

        # คำนวณ BMI
        bmi = weight / ((height / 100) ** 2)

        health_data = {
            'student_id': self.student_id,
            'record_date': self.date_var.get(),
            'brushed_teeth': 0,
            'drank_milk': 0,
            'weight_kg': weight,
            'height_cm': height,
            'bmi': round(bmi, 2)
        }

        if self.db.save_health_record(health_data):
            self.update_status("บันทึกน้ำหนัก-ส่วนสูงเรียบร้อย")
            self.callback()
            messagebox.showinfo("สำเร็จ", f"บันทึกเรียบร้อย\nBMI: {bmi:.2f}")
            self.destroy()
        else:
            messagebox.showerror("ผิดพลาด", "ไม่สามารถบันทึกได้")
