"""
database/db.py
ระบบจัดการฐานข้อมูล SQLite สำหรับโปรแกรมบริหารจัดการโรงเรียน
ประกอบด้วย: นักเรียน, การเช็คชื่อ, สุขภาพ, เกรด, ครู, ตารางเรียน
"""

import sqlite3
import os
from datetime import datetime


class Database:
    """คลาสหลักสำหรับจัดการฐานข้อมูล SQLite"""

    def __init__(self, db_path="school_data.db"):
        """
        สร้างการเชื่อมต่อฐานข้อมูล
        Args:
            db_path: ที่อยู่ไฟล์ฐานข้อมูล (ค่าเริ่มต้น school_data.db)
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self):
        """สร้างการเชื่อมต่อกับฐานข้อมูล"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # ให้ผลลัพธ์เป็น dict-like
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            print(f"เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล: {e}")
            return False

    def close(self):
        """ปิดการเชื่อมต่อฐานข้อมูล"""
        if self.conn:
            self.conn.close()

    def create_tables(self):
        """สร้างตารางทั้งหมดในฐานข้อมูล"""

        # ตารางนักเรียน
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                class_room TEXT NOT NULL,
                class_year TEXT NOT NULL,
                birth_date TEXT,
                photo_path TEXT,
                parent_name TEXT,
                parent_phone TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ตารางการเช็คชื่อ
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                att_date TEXT NOT NULL,
                status TEXT NOT NULL,
                note TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                UNIQUE(student_id, att_date)
            )
        """)

        # ตารางบันทึกสุขภาพ
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                record_date TEXT NOT NULL,
                brushed_teeth INTEGER DEFAULT 0,
                drank_milk INTEGER DEFAULT 0,
                weight_kg REAL,
                height_cm REAL,
                bmi REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        """)

        # ตารางเกรด
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                academic_year TEXT NOT NULL,
                semester TEXT NOT NULL,
                subject_code TEXT NOT NULL,
                subject_name TEXT NOT NULL,
                full_score REAL DEFAULT 100,
                score REAL,
                grade TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                UNIQUE(student_id, academic_year, semester, subject_code)
            )
        """)

        # ตารางครู
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ตารางตารางเรียน
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_room TEXT NOT NULL,
                day_of_week TEXT NOT NULL,
                period_no INTEGER NOT NULL,
                start_time TEXT,
                end_time TEXT,
                subject_name TEXT NOT NULL,
                teacher_id TEXT NOT NULL,
                room_no TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id),
                UNIQUE(teacher_id, day_of_week, period_no)
            )
        """)

        # สร้าง index เพื่อเพิ่มประสิทธิภาพการค้นหา
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_attendance_date
            ON attendance(att_date)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_health_date
            ON health_records(record_date)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_grades_year
            ON grades(academic_year, semester)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_schedule_class
            ON schedule(class_room, day_of_week)
        """)

        # ตารางห้องเรียน
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS classrooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    # ==================== STUDENTS ====================

    def add_student(self, student_data):
        """
        เพิ่มนักเรียนใหม่
        Args:
            student_data: dict ข้อมูลนักเรียน
        Returns:
            True/False
        """
        try:
            self.cursor.execute("""
                INSERT INTO students (
                    student_id, title, first_name, last_name,
                    class_room, class_year, birth_date,
                    photo_path, parent_name, parent_phone
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                student_data.get('student_id'),
                student_data.get('title'),
                student_data.get('first_name'),
                student_data.get('last_name'),
                student_data.get('class_room'),
                student_data.get('class_year'),
                student_data.get('birth_date'),
                student_data.get('photo_path'),
                student_data.get('parent_name'),
                student_data.get('parent_phone')
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"เกิดข้อผิดพลาดในการเพิ่มนักเรียน: {e}")
            return False

    def update_student(self, student_id, student_data):
        """
        แก้ไขข้อมูลนักเรียน
        Args:
            student_id: รหัสนักเรียน
            student_data: dict ข้อมูลที่ต้องการแก้ไข
        Returns:
            True/False
        """
        try:
            self.cursor.execute("""
                UPDATE students SET
                    title = ?,
                    first_name = ?,
                    last_name = ?,
                    class_room = ?,
                    class_year = ?,
                    birth_date = ?,
                    photo_path = ?,
                    parent_name = ?,
                    parent_phone = ?
                WHERE student_id = ?
            """, (
                student_data.get('title'),
                student_data.get('first_name'),
                student_data.get('last_name'),
                student_data.get('class_room'),
                student_data.get('class_year'),
                student_data.get('birth_date'),
                student_data.get('photo_path'),
                student_data.get('parent_name'),
                student_data.get('parent_phone'),
                student_id
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"เกิดข้อผิดพลาดในการแก้ไขนักเรียน: {e}")
            return False

    def delete_student(self, student_id):
        """
        ลบนักเรียน (soft delete - เปลี่ยน is_active เป็น 0)
        Args:
            student_id: รหัสนักเรียน
        Returns:
            True/False
        """
        try:
            self.cursor.execute("""
                UPDATE students SET is_active = 0 WHERE student_id = ?
            """, (student_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"เกิดข้อผิดพลาดในการลบนักเรียน: {e}")
            return False

    def get_all_students(self, class_room=None, class_year=None, active_only=True):
        """
        ดึงข้อมูลนักเรียนทั้งหมด
        Args:
            class_room: กรองตามห้อง (optional)
            class_year: กรองตามปีการศึกษา (optional)
            active_only: แสดงเฉพาะที่ active (default True)
        Returns:
            list of dict
        """
        query = "SELECT * FROM students WHERE 1=1"
        params = []

        if active_only:
            query += " AND is_active = 1"

        if class_room:
            query += " AND class_room = ?"
            params.append(class_room)

        if class_year:
            query += " AND class_year = ?"
            params.append(class_year)

        query += " ORDER BY class_room, first_name"

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def search_students(self, keyword):
        """
        ค้นหานักเรียนจากชื่อหรือรหัส
        Args:
            keyword: คำค้นหา
        Returns:
            list of dict
        """
        self.cursor.execute("""
            SELECT * FROM students
            WHERE is_active = 1 AND (
                student_id LIKE ? OR
                first_name LIKE ? OR
                last_name LIKE ?
            )
            ORDER BY first_name
        """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_student_by_id(self, student_id):
        """
        ดึงข้อมูลนักเรียนจากรหัส
        Args:
            student_id: รหัสนักเรียน
        Returns:
            dict หรือ None
        """
        self.cursor.execute("""
            SELECT * FROM students WHERE student_id = ?
        """, (student_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_class_rooms(self):
        """
        ดึงรายชื่อห้องเรียนทั้งหมด (รวมจากตาราง classrooms + students)
        Returns:
            list of str
        """
        self.cursor.execute("""
            SELECT name FROM classrooms
            UNION
            SELECT DISTINCT class_room FROM students WHERE is_active = 1
            ORDER BY 1
        """)
        return [row[0] for row in self.cursor.fetchall()]

    def count_students_by_classroom(self, classroom_name):
        """นับจำนวนนักเรียนในห้องที่ระบุ"""
        self.cursor.execute("""
            SELECT COUNT(*) FROM students 
            WHERE class_room = ? AND is_active = 1
        """, (classroom_name,))
        result = self.cursor.fetchone()
        return result[0] if result else 0

    # ==================== CLASSROOMS ====================

    def add_classroom(self, name):
        """เพิ่มห้องเรียนใหม่"""
        try:
            self.cursor.execute("INSERT INTO classrooms (name) VALUES (?)", (name,))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_classroom(self, classroom_id):
        """ลบห้องเรียน"""
        try:
            self.cursor.execute("DELETE FROM classrooms WHERE id = ?", (classroom_id,))
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def get_all_classrooms(self):
        """ดึงห้องเรียนทั้งหมดพร้อมจำนวนนักเรียน"""
        self.cursor.execute("""
            SELECT c.id, c.name,
                   COUNT(s.student_id) as student_count
            FROM classrooms c
            LEFT JOIN students s ON s.class_room = c.name AND s.is_active = 1
            GROUP BY c.id, c.name
            ORDER BY c.name
        """)
        return [dict(row) for row in self.cursor.fetchall()]

    def get_class_years(self):
        """
        ดึงรายการปีการศึกษาทั้งหมด
        Returns:
            list of str
        """
        self.cursor.execute("""
            SELECT DISTINCT class_year FROM students
            WHERE is_active = 1
            ORDER BY class_year DESC
        """)
        return [row[0] for row in self.cursor.fetchall()]

    # ==================== ATTENDANCE ====================

    def save_attendance(self, student_id, att_date, status, note=""):
        """
        บันทึกการเช็คชื่อ
        Args:
            student_id: รหัสนักเรียน
            att_date: วันที่ (YYYY-MM-DD)
            status: สถานะ (มา/ขาด/ลา/มาสาย)
            note: หมายเหตุ
        Returns:
            True/False
        """
        try:
            self.cursor.execute("""
                INSERT INTO attendance (student_id, att_date, status, note)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(student_id, att_date)
                DO UPDATE SET status = ?, note = ?
            """, (student_id, att_date, status, note, status, note))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"เกิดข้อผิดพลาดในการบันทึกการเช็คชื่อ: {e}")
            return False

    def get_attendance_by_date(self, att_date, class_room=None):
        """
        ดึงข้อมูลการเช็คชื่อตามวันที่
        Args:
            att_date: วันที่ (YYYY-MM-DD)
            class_room: ห้องเรียน (optional)
        Returns:
            list of dict
        """
        query = """
            SELECT a.*, s.title, s.first_name, s.last_name, s.class_room
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE a.att_date = ?
        """
        params = [att_date]

        if class_room:
            query += " AND s.class_room = ?"
            params.append(class_room)

        query += " ORDER BY s.class_room, s.first_name"

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def get_attendance_by_student(self, student_id, start_date=None, end_date=None):
        """
        ดึงข้อมูลการเช็คชื่อตามนักเรียน
        Args:
            student_id: รหัสนักเรียน
            start_date: วันที่เริ่มต้น (optional)
            end_date: วันที่สิ้นสุด (optional)
        Returns:
            list of dict
        """
        query = "SELECT * FROM attendance WHERE student_id = ?"
        params = [student_id]

        if start_date:
            query += " AND att_date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND att_date <= ?"
            params.append(end_date)

        query += " ORDER BY att_date DESC"

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def get_attendance_stats(self, student_id, start_date=None, end_date=None):
        """
        สถิติการเช็คชื่อของนักเรียน
        Args:
            student_id: รหัสนักเรียน
            start_date: วันที่เริ่มต้น (optional)
            end_date: วันที่สิ้นสุด (optional)
        Returns:
            dict {มา, ขาด, ลา, มาสาย}
        """
        query = """
            SELECT status, COUNT(*) as count
            FROM attendance
            WHERE student_id = ?
        """
        params = [student_id]

        if start_date:
            query += " AND att_date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND att_date <= ?"
            params.append(end_date)

        query += " GROUP BY status"

        self.cursor.execute(query, params)
        stats = {'มา': 0, 'ขาด': 0, 'ลา': 0, 'มาสาย': 0}
        for row in self.cursor.fetchall():
            stats[row[0]] = row[1]
        return stats

    def get_students_absent_more_than(self, days, class_room=None, start_date=None, end_date=None):
        """
        รายชื่อนักเรียนที่ขาดเกิน N วัน
        Args:
            days: จำนวนวันที่กำหนด
            class_room: ห้องเรียน (optional)
            start_date: วันที่เริ่มต้น (optional)
            end_date: วันที่สิ้นสุด (optional)
        Returns:
            list of dict
        """
        query = """
            SELECT s.*, COUNT(a.id) as absent_days
            FROM students s
            JOIN attendance a ON s.student_id = a.student_id
            WHERE a.status = 'ขาด' AND s.is_active = 1
        """
        params = []

        if class_room:
            query += " AND s.class_room = ?"
            params.append(class_room)

        if start_date:
            query += " AND a.att_date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND a.att_date <= ?"
            params.append(end_date)

        query += " GROUP BY s.student_id HAVING absent_days > ? ORDER BY absent_days DESC"
        params.append(days)

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    # ==================== HEALTH ====================

    def save_health_record(self, health_data):
        """
        บันทึกข้อมูลสุขภาพ
        Args:
            health_data: dict ข้อมูลสุขภาพ
        Returns:
            True/False
        """
        try:
            self.cursor.execute("""
                INSERT INTO health_records (
                    student_id, record_date, brushed_teeth, drank_milk,
                    weight_kg, height_cm, bmi
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                health_data.get('student_id'),
                health_data.get('record_date'),
                health_data.get('brushed_teeth', 0),
                health_data.get('drank_milk', 0),
                health_data.get('weight_kg'),
                health_data.get('height_cm'),
                health_data.get('bmi')
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"เกิดข้อผิดพลาดในการบันทึกข้อมูลสุขภาพ: {e}")
            return False

    def update_health_daily(self, student_id, record_date, brushed_teeth, drank_milk):
        """
        อัพเดทการแปรงฟัน/ดื่มนมรายวัน
        Args:
            student_id: รหัสนักเรียน
            record_date: วันที่
            brushed_teeth: แปรงฟัน (0/1)
            drank_milk: ดื่มนม (0/1)
        Returns:
            True/False
        """
        try:
            # ตรวจสอบว่ามีข้อมูลวันนี้หรือยัง
            self.cursor.execute("""
                SELECT id FROM health_records
                WHERE student_id = ? AND record_date = ?
            """, (student_id, record_date))

            if self.cursor.fetchone():
                # อัพเดท
                self.cursor.execute("""
                    UPDATE health_records
                    SET brushed_teeth = ?, drank_milk = ?
                    WHERE student_id = ? AND record_date = ?
                """, (brushed_teeth, drank_milk, student_id, record_date))
            else:
                # สร้างใหม่
                self.cursor.execute("""
                    INSERT INTO health_records (
                        student_id, record_date, brushed_teeth, drank_milk
                    ) VALUES (?, ?, ?, ?)
                """, (student_id, record_date, brushed_teeth, drank_milk))

            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"เกิดข้อผิดพลาดในการอัพเดทข้อมูลสุขภาพรายวัน: {e}")
            return False

    def get_health_records(self, student_id):
        """
        ดึงประวัติสุขภาพของนักเรียน
        Args:
            student_id: รหัสนักเรียน
        Returns:
            list of dict
        """
        self.cursor.execute("""
            SELECT * FROM health_records
            WHERE student_id = ?
            ORDER BY record_date DESC
        """, (student_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_latest_health(self, student_id):
        """
        ดึงข้อมูลสุขภาพล่าสุด
        Args:
            student_id: รหัสนักเรียน
        Returns:
            dict หรือ None
        """
        self.cursor.execute("""
            SELECT * FROM health_records
            WHERE student_id = ? AND (weight_kg IS NOT NULL OR height_cm IS NOT NULL)
            ORDER BY record_date DESC LIMIT 1
        """, (student_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_health_by_date(self, record_date, class_room=None):
        """
        ดึงข้อมูลสุขภาพตามวันที่
        Args:
            record_date: วันที่
            class_room: ห้องเรียน (optional)
        Returns:
            list of dict
        """
        query = """
            SELECT h.*, s.title, s.first_name, s.last_name, s.class_room
            FROM health_records h
            JOIN students s ON h.student_id = s.student_id
            WHERE h.record_date = ? AND s.is_active = 1
        """
        params = [record_date]

        if class_room:
            query += " AND s.class_room = ?"
            params.append(class_room)

        query += " ORDER BY s.class_room, s.first_name"

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    # ==================== GRADES ====================

    def save_grade(self, grade_data):
        """
        บันทึกเกรด
        Args:
            grade_data: dict ข้อมูลเกรด
        Returns:
            True/False
        """
        try:
            self.cursor.execute("""
                INSERT INTO grades (
                    student_id, academic_year, semester, subject_code,
                    subject_name, full_score, score, grade
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_id, academic_year, semester, subject_code)
                DO UPDATE SET score = ?, grade = ?
            """, (
                grade_data.get('student_id'),
                grade_data.get('academic_year'),
                grade_data.get('semester'),
                grade_data.get('subject_code'),
                grade_data.get('subject_name'),
                grade_data.get('full_score', 100),
                grade_data.get('score'),
                grade_data.get('grade'),
                grade_data.get('score'),
                grade_data.get('grade')
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"เกิดข้อผิดพลาดในการบันทึกเกรด: {e}")
            return False

    def get_grades(self, student_id, academic_year=None, semester=None):
        """
        ดึงเกรดของนักเรียน
        Args:
            student_id: รหัสนักเรียน
            academic_year: ปีการศึกษา (optional)
            semester: ภาคเรียน (optional)
        Returns:
            list of dict
        """
        query = "SELECT * FROM grades WHERE student_id = ?"
        params = [student_id]

        if academic_year:
            query += " AND academic_year = ?"
            params.append(academic_year)

        if semester:
            query += " AND semester = ?"
            params.append(semester)

        query += " ORDER BY academic_year, semester, subject_code"

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def get_transcript(self, student_id):
        """
        ดึง Transcript รายบุคคล
        Args:
            student_id: รหัสนักเรียน
        Returns:
            list of dict (เรียงตามปี ภาค วิชา)
        """
        self.cursor.execute("""
            SELECT * FROM grades
            WHERE student_id = ?
            ORDER BY academic_year, semester, subject_code
        """, (student_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    def calculate_grade(self, score):
        """
        คำนวณเกรดจากคะแนน
        Args:
            score: คะแนนที่ได้
        Returns:
            str เกรด
        """
        if score is None:
            return "-"

        score = float(score)
        if score >= 80:
            return "4.0"
        elif score >= 75:
            return "3.5"
        elif score >= 70:
            return "3.0"
        elif score >= 65:
            return "2.5"
        elif score >= 60:
            return "2.0"
        elif score >= 55:
            return "1.5"
        elif score >= 50:
            return "1.0"
        else:
            return "0.0"

    # ==================== TEACHERS ====================

    def add_teacher(self, teacher_data):
        """
        เพิ่มครูใหม่
        Args:
            teacher_data: dict ข้อมูลครู
        Returns:
            True/False
        """
        try:
            self.cursor.execute("""
                INSERT INTO teachers (
                    teacher_id, title, first_name, last_name, phone
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                teacher_data.get('teacher_id'),
                teacher_data.get('title'),
                teacher_data.get('first_name'),
                teacher_data.get('last_name'),
                teacher_data.get('phone')
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"เกิดข้อผิดพลาดในการเพิ่มครู: {e}")
            return False

    def update_teacher(self, teacher_id, teacher_data):
        """
        แก้ไขข้อมูลครู
        Args:
            teacher_id: รหัสครู
            teacher_data: dict ข้อมูลที่ต้องการแก้ไข
        Returns:
            True/False
        """
        try:
            self.cursor.execute("""
                UPDATE teachers SET
                    title = ?,
                    first_name = ?,
                    last_name = ?,
                    phone = ?
                WHERE teacher_id = ?
            """, (
                teacher_data.get('title'),
                teacher_data.get('first_name'),
                teacher_data.get('last_name'),
                teacher_data.get('phone'),
                teacher_id
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"เกิดข้อผิดพลาดในการแก้ไขครู: {e}")
            return False

    def delete_teacher(self, teacher_id):
        """
        ลบครู (soft delete)
        Args:
            teacher_id: รหัสครู
        Returns:
            True/False
        """
        try:
            self.cursor.execute("""
                UPDATE teachers SET is_active = 0 WHERE teacher_id = ?
            """, (teacher_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"เกิดข้อผิดพลาดในการลบครู: {e}")
            return False

    def get_all_teachers(self, active_only=True):
        """
        ดึงข้อมูลครูทั้งหมด
        Args:
            active_only: แสดงเฉพาะที่ active (default True)
        Returns:
            list of dict
        """
        query = "SELECT * FROM teachers WHERE 1=1"
        if active_only:
            query += " AND is_active = 1"
        query += " ORDER BY first_name"

        self.cursor.execute(query)
        return [dict(row) for row in self.cursor.fetchall()]

    def get_teacher_by_id(self, teacher_id):
        """
        ดึงข้อมูลครูจากรหัส
        Args:
            teacher_id: รหัสครู
        Returns:
            dict หรือ None
        """
        self.cursor.execute("""
            SELECT * FROM teachers WHERE teacher_id = ?
        """, (teacher_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    # ==================== SCHEDULE ====================

    def add_schedule(self, schedule_data):
        """
        เพิ่มตารางเรียน
        Args:
            schedule_data: dict ข้อมูลตารางเรียน
        Returns:
            True/False หรือ error message
        """
        try:
            # ตรวจสอบความขัดแย้งของครู
            conflict = self.check_teacher_conflict(
                schedule_data.get('teacher_id'),
                schedule_data.get('day_of_week'),
                schedule_data.get('period_no'),
                exclude_id=None
            )

            if conflict:
                return conflict  # ส่ง error message กลับไป

            self.cursor.execute("""
                INSERT INTO schedule (
                    class_room, day_of_week, period_no, start_time, end_time,
                    subject_name, teacher_id, room_no
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                schedule_data.get('class_room'),
                schedule_data.get('day_of_week'),
                schedule_data.get('period_no'),
                schedule_data.get('start_time'),
                schedule_data.get('end_time'),
                schedule_data.get('subject_name'),
                schedule_data.get('teacher_id'),
                schedule_data.get('room_no')
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"เกิดข้อผิดพลาดในการเพิ่มตารางเรียน: {e}")
            return False

    def update_schedule(self, schedule_id, schedule_data):
        """
        แก้ไขตารางเรียน
        Args:
            schedule_id: id ของตาราง
            schedule_data: dict ข้อมูลที่ต้องการแก้ไข
        Returns:
            True/False หรือ error message
        """
        try:
            # ตรวจสอบความขัดแย้งของครู (ไม่รวมตัวเองที่กำลังแก้ไข)
            conflict = self.check_teacher_conflict(
                schedule_data.get('teacher_id'),
                schedule_data.get('day_of_week'),
                schedule_data.get('period_no'),
                exclude_id=schedule_id
            )

            if conflict:
                return conflict

            self.cursor.execute("""
                UPDATE schedule SET
                    class_room = ?,
                    day_of_week = ?,
                    period_no = ?,
                    start_time = ?,
                    end_time = ?,
                    subject_name = ?,
                    teacher_id = ?,
                    room_no = ?
                WHERE id = ?
            """, (
                schedule_data.get('class_room'),
                schedule_data.get('day_of_week'),
                schedule_data.get('period_no'),
                schedule_data.get('start_time'),
                schedule_data.get('end_time'),
                schedule_data.get('subject_name'),
                schedule_data.get('teacher_id'),
                schedule_data.get('room_no'),
                schedule_id
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"เกิดข้อผิดพลาดในการแก้ไขตารางเรียน: {e}")
            return False

    def delete_schedule(self, schedule_id):
        """
        ลบตารางเรียน
        Args:
            schedule_id: id ของตาราง
        Returns:
            True/False
        """
        try:
            self.cursor.execute("""
                DELETE FROM schedule WHERE id = ?
            """, (schedule_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"เกิดข้อผิดพลาดในการลบตารางเรียน: {e}")
            return False

    def check_teacher_conflict(self, teacher_id, day_of_week, period_no, exclude_id=None):
        """
        ตรวจสอบความขัดแย้งของครู
        Args:
            teacher_id: รหัสครู
            day_of_week: วัน
            period_no: คาบที่
            exclude_id: id ที่ไม่ต้องตรวจสอบ (กรณีแก้ไข)
        Returns:
            error message หรือ None
        """
        query = """
            SELECT s.*, t.title, t.first_name, t.last_name
            FROM schedule s
            JOIN teachers t ON s.teacher_id = t.teacher_id
            WHERE s.teacher_id = ? AND s.day_of_week = ? AND s.period_no = ?
        """
        params = [teacher_id, day_of_week, period_no]

        if exclude_id:
            query += " AND s.id != ?"
            params.append(exclude_id)

        self.cursor.execute(query, params)
        conflict = self.cursor.fetchone()

        if conflict:
            teacher_name = f"{conflict['title']}{conflict['first_name']} {conflict['last_name']}"
            return f"ครู {teacher_name} มีคาบสอนอยู่แล้วในวัน {day_of_week} คาบที่ {period_no} ที่ห้อง {conflict['class_room']} กรุณาเลือกคาบอื่น"

        return None

    def get_schedule_by_class(self, class_room):
        """
        ดึงตารางเรียนตามห้อง
        Args:
            class_room: ห้องเรียน
        Returns:
            list of dict
        """
        self.cursor.execute("""
            SELECT s.*, t.title, t.first_name, t.last_name
            FROM schedule s
            JOIN teachers t ON s.teacher_id = t.teacher_id
            WHERE s.class_room = ?
            ORDER BY
                CASE s.day_of_week
                    WHEN 'จันทร์' THEN 1
                    WHEN 'อังคาร' THEN 2
                    WHEN 'พุธ' THEN 3
                    WHEN 'พฤหัสบดี' THEN 4
                    WHEN 'ศุกร์' THEN 5
                END,
                s.period_no
        """, (class_room,))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_schedule_by_teacher(self, teacher_id):
        """
        ดึงตารางสอนของครู
        Args:
            teacher_id: รหัสครู
        Returns:
            list of dict
        """
        self.cursor.execute("""
            SELECT s.*, t.title, t.first_name, t.last_name
            FROM schedule s
            JOIN teachers t ON s.teacher_id = t.teacher_id
            WHERE s.teacher_id = ?
            ORDER BY
                CASE s.day_of_week
                    WHEN 'จันทร์' THEN 1
                    WHEN 'อังคาร' THEN 2
                    WHEN 'พุธ' THEN 3
                    WHEN 'พฤหัสบดี' THEN 4
                    WHEN 'ศุกร์' THEN 5
                END,
                s.period_no
        """, (teacher_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_teacher_workload(self):
        """
        คำนวณภาระงานของครูแต่ละคน
        Returns:
            list of dict {teacher_id, name, periods_per_week}
        """
        self.cursor.execute("""
            SELECT
                t.teacher_id,
                t.title || t.first_name || ' ' || t.last_name as name,
                COUNT(s.id) as periods_per_week
            FROM teachers t
            LEFT JOIN schedule s ON t.teacher_id = s.teacher_id
            WHERE t.is_active = 1
            GROUP BY t.teacher_id
            ORDER BY periods_per_week DESC, name
        """)
        return [dict(row) for row in self.cursor.fetchall()]

    def get_all_schedules(self):
        """
        ดึงตารางเรียนทั้งหมด
        Returns:
            list of dict
        """
        self.cursor.execute("""
            SELECT s.*, t.title, t.first_name, t.last_name
            FROM schedule s
            JOIN teachers t ON s.teacher_id = t.teacher_id
            ORDER BY s.class_room,
                CASE s.day_of_week
                    WHEN 'จันทร์' THEN 1
                    WHEN 'อังคาร' THEN 2
                    WHEN 'พุธ' THEN 3
                    WHEN 'พฤหัสบดี' THEN 4
                    WHEN 'ศุกร์' THEN 5
                END,
                s.period_no
        """)
        return [dict(row) for row in self.cursor.fetchall()]
