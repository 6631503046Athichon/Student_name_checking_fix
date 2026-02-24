"""
modules/grades.py
โมดูลบันทึกเกรด
- บันทึกคะแนนแต่ละวิชา/ภาค
- คำนวณเกรดอัตโนมัติ
- Transcript รายบุคคล
- Export PDF (A4)
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


class GradesModule:
    """โมดูลบันทึกเกรด"""

    def __init__(self, parent, db, update_status_callback):
        self.parent = parent
        self.db = db
        self.update_status = update_status_callback

        # วิชาทั้งหมด
        self.subjects = [
            ("TH", "ภาษาไทย"),
            ("MATH", "คณิตศาสตร์"),
            ("SCI", "วิทยาศาสตร์"),
            ("SOC", "สังคมศึกษา"),
            ("HIST", "ประวัติศาสตร์"),
            ("PE", "สุขศึกษาและพละ"),
            ("ART", "ศิลปะ"),
            ("WORK", "การงานอาชีพ"),
            ("ENG", "ภาษาอังกฤษ")
        ]

        # สร้าง UI
        self.create_ui()

    def create_ui(self):
        """สร้าง UI ของโมดูล"""

        # Tab control
        self.tabview = ctk.CTkTabview(self.parent)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        # Tab 1: บันทึกเกรด
        self.tabview.add("บันทึกเกรด")
        self.create_input_tab()

        # Tab 2: Transcript
        self.tabview.add("Transcript")
        self.create_transcript_tab()

    def create_input_tab(self):
        """สร้าง Tab บันทึกเกรด"""

        tab = self.tabview.tab("บันทึกเกรด")

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
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            command=lambda x: self.load_grades()
        )
        self.student_menu.pack(side="left", padx=(0, 20))

        # ปีการศึกษา
        ctk.CTkLabel(
            top_frame,
            text="ปีการศึกษา:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        current_year = datetime.now().year + 543
        self.year_var = ctk.StringVar(value=str(current_year))
        year_entry = ctk.CTkEntry(
            top_frame,
            textvariable=self.year_var,
            width=100,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        year_entry.pack(side="left", padx=(0, 20))

        # ภาคเรียน
        ctk.CTkLabel(
            top_frame,
            text="ภาคเรียน:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        self.semester_var = ctk.StringVar(value="1")
        semester_menu = ctk.CTkOptionMenu(
            top_frame,
            variable=self.semester_var,
            values=["1", "2"],
            width=80,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            command=lambda x: self.load_grades()
        )
        semester_menu.pack(side="left", padx=(0, 20))

        # ปุ่มโหลด
        load_btn = ctk.CTkButton(
            top_frame,
            text="โหลดข้อมูล",
            command=self.load_grades,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120
        )
        load_btn.pack(side="left")

        # ตาราง
        table_frame = ctk.CTkFrame(tab)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("subject_code", "subject_name", "score", "grade")
        self.grade_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)

        self.grade_tree.heading("subject_code", text="รหัสวิชา")
        self.grade_tree.heading("subject_name", text="ชื่อวิชา")
        self.grade_tree.heading("score", text="คะแนน")
        self.grade_tree.heading("grade", text="เกรด")

        self.grade_tree.column("subject_code", width=100, anchor="center")
        self.grade_tree.column("subject_name", width=250)
        self.grade_tree.column("score", width=120, anchor="center")
        self.grade_tree.column("grade", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.grade_tree.yview)
        self.grade_tree.configure(yscrollcommand=scrollbar.set)

        self.grade_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind
        self.grade_tree.bind("<Double-1>", lambda e: self.edit_grade())

        # ปุ่มด้านล่าง
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))

        ctk.CTkButton(
            btn_frame,
            text="➕ บันทึกคะแนน",
            command=self.add_grade,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=150
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="✏️ แก้ไข",
            command=self.edit_grade,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=120,
            fg_color="#F39C12",
            hover_color="#E67E22"
        ).pack(side="left")

        # เกณฑ์การให้เกรด
        criteria_frame = ctk.CTkFrame(tab)
        criteria_frame.pack(fill="x", padx=20, pady=(10, 20))

        ctk.CTkLabel(
            criteria_frame,
            text="เกณฑ์การให้เกรด: 80+=4.0 | 75+=3.5 | 70+=3.0 | 65+=2.5 | 60+=2.0 | 55+=1.5 | 50+=1.0 | <50=0.0",
            font=ctk.CTkFont(family="TH Sarabun New", size=13),
            text_color="gray"
        ).pack(pady=10)

        # โหลดรายชื่อนักเรียน
        self.load_student_list()

    def create_transcript_tab(self):
        """สร้าง Tab Transcript"""

        tab = self.tabview.tab("Transcript")

        # Top frame
        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        # นักเรียน
        ctk.CTkLabel(
            top_frame,
            text="เลือกนักเรียน:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(side="left", padx=(0, 10))

        self.transcript_student_var = ctk.StringVar()
        self.transcript_student_menu = ctk.CTkOptionMenu(
            top_frame,
            variable=self.transcript_student_var,
            values=["เลือกนักเรียน"],
            width=300,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        self.transcript_student_menu.pack(side="left", padx=(0, 20))

        # ปุ่มดู Transcript
        view_btn = ctk.CTkButton(
            top_frame,
            text="📋 ดู Transcript",
            command=self.show_transcript,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=150
        )
        view_btn.pack(side="left", padx=(0, 10))

        # ปุ่ม Export PDF
        export_btn = ctk.CTkButton(
            top_frame,
            text="📄 Export PDF",
            command=self.export_transcript_pdf,
            font=ctk.CTkFont(family="TH Sarabun New", size=14),
            width=150,
            fg_color="#8E44AD",
            hover_color="#6C3483"
        )
        export_btn.pack(side="left")

        # พื้นที่แสดง Transcript
        self.transcript_frame = ctk.CTkScrollableFrame(tab)
        self.transcript_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # ข้อความตัวอย่าง
        ctk.CTkLabel(
            self.transcript_frame,
            text="เลือกนักเรียนและกดดู Transcript",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(pady=50)

        # โหลดรายชื่อนักเรียน
        self.load_student_list_for_transcript()

    # ==================== FUNCTIONS ====================

    def load_student_list(self):
        """โหลดรายชื่อนักเรียน"""

        students = self.db.get_all_students()
        student_options = [f"{s['student_id']} - {s['title']}{s['first_name']} {s['last_name']}" for s in students]

        if student_options:
            self.student_menu.configure(values=student_options)
            self.student_var.set(student_options[0])
            self.load_grades()

    def load_student_list_for_transcript(self):
        """โหลดรายชื่อนักเรียนสำหรับ Transcript"""

        students = self.db.get_all_students()
        student_options = [f"{s['student_id']} - {s['title']}{s['first_name']} {s['last_name']}" for s in students]

        if student_options:
            self.transcript_student_menu.configure(values=student_options)
            self.transcript_student_var.set(student_options[0])

    def load_grades(self):
        """โหลดข้อมูลเกรด"""

        # ล้างตาราง
        for item in self.grade_tree.get_children():
            self.grade_tree.delete(item)

        # ดึงข้อมูล
        selected = self.student_var.get()
        if not selected or selected == "เลือกนักเรียน":
            return

        student_id = selected.split(" - ")[0]
        year = self.year_var.get()
        semester = self.semester_var.get()

        # ดึงเกรด
        grades = self.db.get_grades(student_id, year, semester)
        grade_dict = {g['subject_code']: g for g in grades}

        # แสดงวิชาทั้งหมด
        for code, name in self.subjects:
            if code in grade_dict:
                grade = grade_dict[code]
                score = grade['score'] if grade['score'] is not None else "-"
                grade_val = grade['grade'] if grade['grade'] else "-"
            else:
                score = "-"
                grade_val = "-"

            self.grade_tree.insert("", "end", values=(code, name, score, grade_val))

        self.update_status("โหลดข้อมูลเกรดเรียบร้อย")

    def add_grade(self):
        """เพิ่มคะแนน"""

        selected = self.student_var.get()
        if not selected or selected == "เลือกนักเรียน":
            messagebox.showwarning("คำเตือน", "กรุณาเลือกนักเรียน")
            return

        student_id = selected.split(" - ")[0]
        year = self.year_var.get()
        semester = self.semester_var.get()

        GradeDialog(
            self.parent,
            self.db,
            student_id,
            year,
            semester,
            self.subjects,
            None,
            self.load_grades,
            self.update_status
        )

    def edit_grade(self):
        """แก้ไขคะแนน"""

        selected_tree = self.grade_tree.selection()
        if not selected_tree:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกวิชาที่ต้องการแก้ไข")
            return

        selected_student = self.student_var.get()
        if not selected_student or selected_student == "เลือกนักเรียน":
            messagebox.showwarning("คำเตือน", "กรุณาเลือกนักเรียน")
            return

        student_id = selected_student.split(" - ")[0]
        year = self.year_var.get()
        semester = self.semester_var.get()

        # ดึงข้อมูลวิชาที่เลือก
        values = self.grade_tree.item(selected_tree[0])['values']
        subject_code = values[0]
        subject_name = values[1]

        # ดึงคะแนนปัจจุบัน
        grades = self.db.get_grades(student_id, year, semester)
        current_grade = next((g for g in grades if g['subject_code'] == subject_code), None)

        GradeDialog(
            self.parent,
            self.db,
            student_id,
            year,
            semester,
            self.subjects,
            current_grade,
            self.load_grades,
            self.update_status
        )

    def show_transcript(self):
        """แสดง Transcript"""

        # ล้างข้อมูลเดิม
        for widget in self.transcript_frame.winfo_children():
            widget.destroy()

        # ดึงข้อมูล
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
                text="ไม่มีข้อมูลเกรด",
                font=ctk.CTkFont(family="TH Sarabun New", size=14)
            ).pack(pady=20)
            return

        # หัวเรื่อง
        name = f"{student['title']}{student['first_name']} {student['last_name']}"
        ctk.CTkLabel(
            self.transcript_frame,
            text=f"Transcript - {name}",
            font=ctk.CTkFont(family="TH Sarabun New", size=20, weight="bold")
        ).pack(pady=20)

        ctk.CTkLabel(
            self.transcript_frame,
            text=f"รหัสนักเรียน: {student_id} | ห้อง: {student['class_room']}",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).pack(pady=5)

        # จัดกลุ่มตามปีและภาค
        grouped = {}
        for grade in transcript_data:
            key = f"{grade['academic_year']}/{grade['semester']}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(grade)

        # แสดงแต่ละภาค
        for key, grades in sorted(grouped.items()):
            year, semester = key.split("/")

            # กรอบแต่ละภาค
            semester_frame = ctk.CTkFrame(self.transcript_frame)
            semester_frame.pack(fill="x", pady=10, padx=20)

            ctk.CTkLabel(
                semester_frame,
                text=f"ปีการศึกษา {year} ภาคเรียนที่ {semester}",
                font=ctk.CTkFont(family="TH Sarabun New", size=16, weight="bold")
            ).pack(pady=10)

            # ตาราง
            table_frame = ctk.CTkFrame(semester_frame, fg_color="transparent")
            table_frame.pack(fill="x", padx=10, pady=10)

            # หัวตาราง
            headers = ["รหัสวิชา", "ชื่อวิชา", "คะแนน", "เกรด"]
            for col, header in enumerate(headers):
                ctk.CTkLabel(
                    table_frame,
                    text=header,
                    font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold"),
                    fg_color="#1F4E78",
                    text_color="white",
                    corner_radius=5,
                    width=150 if col == 1 else 100
                ).grid(row=0, column=col, padx=2, pady=2, sticky="ew")

            # ข้อมูล
            for row, grade in enumerate(grades, start=1):
                data = [
                    grade['subject_code'],
                    grade['subject_name'],
                    str(grade['score']) if grade['score'] is not None else "-",
                    grade['grade'] if grade['grade'] else "-"
                ]

                for col, value in enumerate(data):
                    ctk.CTkLabel(
                        table_frame,
                        text=value,
                        font=ctk.CTkFont(family="TH Sarabun New", size=13),
                        fg_color="#ECF0F1",
                        corner_radius=5,
                        width=150 if col == 1 else 100
                    ).grid(row=row, column=col, padx=2, pady=2, sticky="ew")

            # คำนวณ GPA
            valid_grades = [float(g['grade']) for g in grades if g['grade'] and g['grade'] != '-']
            if valid_grades:
                gpa = sum(valid_grades) / len(valid_grades)
                ctk.CTkLabel(
                    semester_frame,
                    text=f"GPA: {gpa:.2f}",
                    font=ctk.CTkFont(family="TH Sarabun New", size=14, weight="bold")
                ).pack(pady=10)

        self.update_status("แสดง Transcript เรียบร้อย")

    def export_transcript_pdf(self):
        """Export Transcript เป็น PDF"""

        selected = self.transcript_student_var.get()
        if not selected or selected == "เลือกนักเรียน":
            messagebox.showwarning("คำเตือน", "กรุณาเลือกนักเรียน")
            return

        student_id = selected.split(" - ")[0]
        student = self.db.get_student_by_id(student_id)
        transcript_data = self.db.get_transcript(student_id)

        if not transcript_data:
            messagebox.showwarning("คำเตือน", "ไม่มีข้อมูลเกรด")
            return

        file_path = filedialog.asksaveasfilename(
            title="บันทึกไฟล์ PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Transcript_{student_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )

        if not file_path:
            return

        try:
            # ลงทะเบียนฟอนต์
            try:
                pdfmetrics.registerFont(TTFont('Sarabun', 'THSarabunNew.ttf'))
                font_name = 'Sarabun'
            except:
                font_name = 'Helvetica'

            # สร้าง PDF
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            elements = []

            # สไตล์
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=18,
                alignment=1
            )

            # หัวเรื่อง
            name = f"{student['title']}{student['first_name']} {student['last_name']}"
            title = Paragraph(f"Transcript - {name}", title_style)
            elements.append(title)
            elements.append(Spacer(1, 0.3*cm))

            info = Paragraph(
                f"รหัสนักเรียน: {student_id} | ห้อง: {student['class_room']}",
                ParagraphStyle('Info', parent=styles['Normal'], fontName=font_name, fontSize=12, alignment=1)
            )
            elements.append(info)
            elements.append(Spacer(1, 0.5*cm))

            # จัดกลุ่มตามปีและภาค
            grouped = {}
            for grade in transcript_data:
                key = f"{grade['academic_year']}/{grade['semester']}"
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(grade)

            # แสดงแต่ละภาค
            for key, grades in sorted(grouped.items()):
                year, semester = key.split("/")

                # หัวข้อภาค
                semester_title = Paragraph(
                    f"ปีการศึกษา {year} ภาคเรียนที่ {semester}",
                    ParagraphStyle('Semester', parent=styles['Heading2'], fontName=font_name, fontSize=14)
                )
                elements.append(semester_title)
                elements.append(Spacer(1, 0.3*cm))

                # ตาราง
                data = [["รหัสวิชา", "ชื่อวิชา", "คะแนน", "เกรด"]]

                for grade in grades:
                    data.append([
                        grade['subject_code'],
                        grade['subject_name'],
                        str(grade['score']) if grade['score'] is not None else "-",
                        grade['grade'] if grade['grade'] else "-"
                    ])

                table = Table(data, colWidths=[3*cm, 8*cm, 3*cm, 3*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), font_name),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), font_name),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                ]))

                elements.append(table)

                # GPA
                valid_grades = [float(g['grade']) for g in grades if g['grade'] and g['grade'] != '-']
                if valid_grades:
                    gpa = sum(valid_grades) / len(valid_grades)
                    gpa_text = Paragraph(
                        f"GPA: {gpa:.2f}",
                        ParagraphStyle('GPA', parent=styles['Normal'], fontName=font_name, fontSize=12, alignment=2)
                    )
                    elements.append(Spacer(1, 0.2*cm))
                    elements.append(gpa_text)

                elements.append(Spacer(1, 0.5*cm))

            doc.build(elements)

            self.update_status("Export PDF สำเร็จ")
            messagebox.showinfo("สำเร็จ", "Export Transcript เป็น PDF เรียบร้อย")

        except Exception as e:
            messagebox.showerror("ผิดพลาด", f"ไม่สามารถสร้าง PDF ได้\n{str(e)}")


class GradeDialog(ctk.CTkToplevel):
    """หน้าต่างบันทึกคะแนน"""

    def __init__(self, parent, db, student_id, year, semester, subjects, current_grade, callback, update_status):
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
        self.geometry("450x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.create_form()

        # ถ้ามีข้อมูลเดิม ให้แสดง
        if current_grade:
            self.fill_data()

    def create_form(self):
        """สร้างฟอร์ม"""

        # Title
        ctk.CTkLabel(
            self,
            text="บันทึกคะแนน",
            font=ctk.CTkFont(family="TH Sarabun New", size=18, weight="bold")
        ).pack(pady=20)

        # Form
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(pady=10)

        # วิชา
        ctk.CTkLabel(
            form_frame,
            text="เลือกวิชา:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=0, column=0, sticky="w", pady=10, padx=(0, 10))

        self.subject_var = ctk.StringVar()
        subject_options = [f"{code} - {name}" for code, name in self.subjects]
        subject_menu = ctk.CTkOptionMenu(
            form_frame,
            variable=self.subject_var,
            values=subject_options,
            width=250,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        subject_menu.grid(row=0, column=1, pady=10)

        # คะแนน
        ctk.CTkLabel(
            form_frame,
            text="คะแนน:",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=1, column=0, sticky="w", pady=10, padx=(0, 10))

        self.score_var = ctk.StringVar()
        score_entry = ctk.CTkEntry(
            form_frame,
            textvariable=self.score_var,
            width=250,
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        )
        score_entry.grid(row=1, column=1, pady=10)

        # เกรดที่คำนวณได้
        ctk.CTkLabel(
            form_frame,
            text="เกรด (คำนวณอัตโนมัติ):",
            font=ctk.CTkFont(family="TH Sarabun New", size=14)
        ).grid(row=2, column=0, sticky="w", pady=10, padx=(0, 10))

        self.grade_label = ctk.CTkLabel(
            form_frame,
            text="-",
            font=ctk.CTkFont(family="TH Sarabun New", size=16, weight="bold"),
            text_color="#2980B9"
        )
        self.grade_label.grid(row=2, column=1, pady=10, sticky="w")

        # Bind score entry
        self.score_var.trace("w", lambda *args: self.calculate_grade())

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

        subject_text = f"{self.current_grade['subject_code']} - {self.current_grade['subject_name']}"
        self.subject_var.set(subject_text)
        self.score_var.set(str(self.current_grade['score']) if self.current_grade['score'] is not None else "")

    def calculate_grade(self):
        """คำนวณเกรด"""

        try:
            score = float(self.score_var.get())
            grade = self.db.calculate_grade(score)
            self.grade_label.configure(text=grade)
        except:
            self.grade_label.configure(text="-")

    def save(self):
        """บันทึก"""

        subject_text = self.subject_var.get()
        if not subject_text:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกวิชา")
            return

        try:
            score = float(self.score_var.get())
        except:
            messagebox.showwarning("คำเตือน", "กรุณากรอกคะแนนที่ถูกต้อง")
            return

        # แยกรหัสวิชาและชื่อวิชา
        subject_code = subject_text.split(" - ")[0]
        subject_name = subject_text.split(" - ")[1]

        # คำนวณเกรด
        grade = self.db.calculate_grade(score)

        # บันทึก
        grade_data = {
            'student_id': self.student_id,
            'academic_year': self.year,
            'semester': self.semester,
            'subject_code': subject_code,
            'subject_name': subject_name,
            'full_score': 100,
            'score': score,
            'grade': grade
        }

        if self.db.save_grade(grade_data):
            self.update_status("บันทึกคะแนนเรียบร้อย")
            self.callback()
            messagebox.showinfo("สำเร็จ", f"บันทึกคะแนนเรียบร้อย\nเกรด: {grade}")
            self.destroy()
        else:
            messagebox.showerror("ผิดพลาด", "ไม่สามารถบันทึกได้")
