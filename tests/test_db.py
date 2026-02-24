"""
test_db.py
ทดสอบฟังก์ชัน CRUD ทุกตัวในระบบฐานข้อมูล
"""

import pytest
from datetime import datetime, timedelta


class TestStudents:
    """ทดสอบการจัดการนักเรียน"""

    def test_add_student_success(self, test_db):
        """ทดสอบเพิ่มนักเรียนใหม่สำเร็จ"""
        student_data = {
            'student_id': '66001',
            'title': 'เด็กชาย',
            'first_name': 'ทดสอบ',
            'last_name': 'ระบบ',
            'class_room': 'ป.1/1',
            'class_year': '2567',
            'birth_date': '2016-01-01',
            'parent_name': 'นายทดสอบ',
            'parent_phone': '0812345678',
            'photo_path': None
        }

        result = test_db.add_student(student_data)
        assert result is True

        # ตรวจสอบว่าข้อมูลถูกบันทึกจริง
        student = test_db.get_student_by_id('66001')
        assert student is not None
        assert student['first_name'] == 'ทดสอบ'
        assert student['last_name'] == 'ระบบ'

    def test_add_student_duplicate_id(self, db_with_students):
        """ทดสอบเพิ่มนักเรียนที่มี ID ซ้ำ - ต้องล้มเหลว"""
        student_data = {
            'student_id': '65001',  # ID ซ้ำ
            'title': 'เด็กชาย',
            'first_name': 'ซ้ำ',
            'last_name': 'กัน',
            'class_room': 'ป.1/1',
            'class_year': '2567',
            'birth_date': '2016-01-01',
            'parent_name': 'นายซ้ำ',
            'parent_phone': '0812345678',
            'photo_path': None
        }

        result = db_with_students.add_student(student_data)
        assert result is False

    def test_get_all_students(self, db_with_students):
        """ทดสอบดึงรายชื่อนักเรียนทั้งหมด"""
        students = db_with_students.get_all_students()
        assert len(students) == 5
        assert all(s['is_active'] == 1 for s in students)

    def test_get_students_by_class_room(self, db_with_students):
        """ทดสอบกรองนักเรียนตามห้อง"""
        students = db_with_students.get_all_students(class_room='ป.1/1')
        assert len(students) == 2
        assert all(s['class_room'] == 'ป.1/1' for s in students)

    def test_get_students_by_class_year(self, db_with_students):
        """ทดสอบกรองนักเรียนตามปีการศึกษา"""
        students = db_with_students.get_all_students(class_year='2567')
        assert len(students) == 5

    def test_update_student_success(self, db_with_students):
        """ทดสอบแก้ไขข้อมูลนักเรียนสำเร็จ"""
        updated_data = {
            'title': 'เด็กชาย',
            'first_name': 'สมชาย_แก้ไข',
            'last_name': 'ใจดี_แก้ไข',
            'class_room': 'ป.2/1',
            'class_year': '2567',
            'birth_date': '2016-01-15',
            'parent_name': 'นายสมศักดิ์ ใจดี',
            'parent_phone': '0999999999',
            'photo_path': None
        }

        result = db_with_students.update_student('65001', updated_data)
        assert result is True

        # ตรวจสอบข้อมูลถูกแก้ไขจริง
        student = db_with_students.get_student_by_id('65001')
        assert student['first_name'] == 'สมชาย_แก้ไข'
        assert student['class_room'] == 'ป.2/1'
        assert student['parent_phone'] == '0999999999'

    def test_delete_student_soft_delete(self, db_with_students):
        """ทดสอบลบนักเรียน (soft delete)"""
        result = db_with_students.delete_student('65001')
        assert result is True

        # ตรวจสอบว่า is_active เปลี่ยนเป็น 0
        student = db_with_students.get_student_by_id('65001')
        assert student['is_active'] == 0

        # ไม่แสดงในรายการ active
        students = db_with_students.get_all_students(active_only=True)
        assert len(students) == 4

        # แต่ยังแสดงถ้าดึงทั้งหมด
        all_students = db_with_students.get_all_students(active_only=False)
        assert len(all_students) == 5

    def test_search_students_by_name(self, db_with_students):
        """ทดสอบค้นหานักเรียนด้วยชื่อ"""
        results = db_with_students.search_students('สมชาย')
        assert len(results) == 1
        assert results[0]['first_name'] == 'สมชาย'

    def test_search_students_by_id(self, db_with_students):
        """ทดสอบค้นหานักเรียนด้วยรหัส"""
        results = db_with_students.search_students('65002')
        assert len(results) == 1
        assert results[0]['student_id'] == '65002'

    def test_search_students_partial_match(self, db_with_students):
        """ทดสอบค้นหาแบบบางส่วน"""
        results = db_with_students.search_students('สม')
        assert len(results) >= 2  # สมชาย, สมหญิง

    def test_get_class_rooms(self, db_with_students):
        """ทดสอบดึงรายชื่อห้องเรียนทั้งหมด"""
        class_rooms = db_with_students.get_class_rooms()
        assert len(class_rooms) == 3
        assert 'ป.1/1' in class_rooms
        assert 'ป.2/1' in class_rooms
        assert 'ป.3/1' in class_rooms

    def test_get_class_years(self, db_with_students):
        """ทดสอบดึงรายการปีการศึกษา"""
        class_years = db_with_students.get_class_years()
        assert len(class_years) >= 1
        assert '2567' in class_years


class TestAttendance:
    """ทดสอบการเช็คชื่อ"""

    def test_save_attendance_new_record(self, db_with_students, sample_date):
        """ทดสอบบันทึกการเช็คชื่อใหม่"""
        result = db_with_students.save_attendance('65001', sample_date, 'มา')
        assert result is True

        # ตรวจสอบข้อมูล
        records = db_with_students.get_attendance_by_date(sample_date)
        assert len(records) == 1
        assert records[0]['status'] == 'มา'

    def test_save_attendance_update_existing(self, db_with_students, sample_date):
        """ทดสอบอัพเดทการเช็คชื่อที่มีอยู่แล้ว"""
        # บันทึกครั้งแรก
        db_with_students.save_attendance('65001', sample_date, 'มา')

        # อัพเดท
        result = db_with_students.save_attendance('65001', sample_date, 'ลา', 'ป่วย')
        assert result is True

        # ตรวจสอบข้อมูลถูกอัพเดท
        records = db_with_students.get_attendance_by_date(sample_date)
        assert len(records) == 1
        assert records[0]['status'] == 'ลา'
        assert records[0]['note'] == 'ป่วย'

    def test_get_attendance_by_date(self, db_with_students, sample_date):
        """ทดสอบดึงข้อมูลเช็คชื่อตามวันที่"""
        # บันทึกข้อมูลหลายคน
        db_with_students.save_attendance('65001', sample_date, 'มา')
        db_with_students.save_attendance('65002', sample_date, 'ขาด')
        db_with_students.save_attendance('65003', sample_date, 'ลา')

        records = db_with_students.get_attendance_by_date(sample_date)
        assert len(records) == 3

    def test_get_attendance_by_date_with_class(self, db_with_students, sample_date):
        """ทดสอบดึงข้อมูลเช็คชื่อกรองตามห้อง"""
        db_with_students.save_attendance('65001', sample_date, 'มา')
        db_with_students.save_attendance('65002', sample_date, 'มา')
        db_with_students.save_attendance('65003', sample_date, 'มา')

        records = db_with_students.get_attendance_by_date(sample_date, class_room='ป.1/1')
        assert len(records) == 2

    def test_get_attendance_by_student(self, db_with_students):
        """ทดสอบดึงประวัติเช็คชื่อของนักเรียน"""
        today = datetime.now()
        dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(5)]

        # บันทึกหลายวัน
        for date in dates:
            db_with_students.save_attendance('65001', date, 'มา')

        records = db_with_students.get_attendance_by_student('65001')
        assert len(records) == 5

    def test_get_attendance_stats_all_status(self, db_with_students):
        """ทดสอบสถิติการเช็คชื่อทุกสถานะ"""
        today = datetime.now()

        # บันทึก: มา 3 วัน, ขาด 2 วัน, ลา 1 วัน, มาสาย 1 วัน
        db_with_students.save_attendance('65001', (today - timedelta(days=0)).strftime('%Y-%m-%d'), 'มา')
        db_with_students.save_attendance('65001', (today - timedelta(days=1)).strftime('%Y-%m-%d'), 'มา')
        db_with_students.save_attendance('65001', (today - timedelta(days=2)).strftime('%Y-%m-%d'), 'มา')
        db_with_students.save_attendance('65001', (today - timedelta(days=3)).strftime('%Y-%m-%d'), 'ขาด')
        db_with_students.save_attendance('65001', (today - timedelta(days=4)).strftime('%Y-%m-%d'), 'ขาด')
        db_with_students.save_attendance('65001', (today - timedelta(days=5)).strftime('%Y-%m-%d'), 'ลา')
        db_with_students.save_attendance('65001', (today - timedelta(days=6)).strftime('%Y-%m-%d'), 'มาสาย')

        stats = db_with_students.get_attendance_stats('65001')
        assert stats['มา'] == 3
        assert stats['ขาด'] == 2
        assert stats['ลา'] == 1
        assert stats['มาสาย'] == 1

    def test_get_students_absent_more_than(self, db_with_students):
        """ทดสอบรายชื่อนักเรียนที่ขาดเกิน N วัน"""
        today = datetime.now()

        # นักเรียน 65001 ขาด 5 วัน
        for i in range(5):
            db_with_students.save_attendance('65001', (today - timedelta(days=i)).strftime('%Y-%m-%d'), 'ขาด')

        # นักเรียน 65002 ขาด 2 วัน
        for i in range(2):
            db_with_students.save_attendance('65002', (today - timedelta(days=i)).strftime('%Y-%m-%d'), 'ขาด')

        # หานักเรียนที่ขาดเกิน 3 วัน
        result = db_with_students.get_students_absent_more_than(3)
        assert len(result) == 1
        assert result[0]['student_id'] == '65001'
        assert result[0]['absent_days'] == 5


class TestHealth:
    """ทดสอบการบันทึกสุขภาพ"""

    def test_save_health_record_complete(self, db_with_students, sample_date):
        """ทดสอบบันทึกข้อมูลสุขภาพครบถ้วน"""
        health_data = {
            'student_id': '65001',
            'record_date': sample_date,
            'brushed_teeth': 1,
            'drank_milk': 1,
            'weight_kg': 40.5,
            'height_cm': 150.0,
            'bmi': 18.0
        }

        result = db_with_students.save_health_record(health_data)
        assert result is True

        # ตรวจสอบข้อมูล
        records = db_with_students.get_health_records('65001')
        assert len(records) == 1
        assert records[0]['weight_kg'] == 40.5
        assert records[0]['height_cm'] == 150.0

    def test_update_health_daily_new_record(self, db_with_students, sample_date):
        """ทดสอบอัพเดทการแปรงฟัน/ดื่มนมรายวัน (สร้างใหม่)"""
        result = db_with_students.update_health_daily('65001', sample_date, 1, 1)
        assert result is True

        records = db_with_students.get_health_by_date(sample_date)
        assert len(records) == 1
        assert records[0]['brushed_teeth'] == 1
        assert records[0]['drank_milk'] == 1

    def test_update_health_daily_existing_record(self, db_with_students, sample_date):
        """ทดสอบอัพเดทการแปรงฟัน/ดื่มนมรายวัน (แก้ไข)"""
        # สร้างข้อมูลเดิม
        db_with_students.update_health_daily('65001', sample_date, 0, 0)

        # อัพเดท
        result = db_with_students.update_health_daily('65001', sample_date, 1, 1)
        assert result is True

        records = db_with_students.get_health_by_date(sample_date)
        assert records[0]['brushed_teeth'] == 1
        assert records[0]['drank_milk'] == 1

    def test_calculate_bmi_normal(self, test_db):
        """ทดสอบคำนวณ BMI - สถานะปกติ"""
        # BMI = weight / (height_m ^ 2)
        # 60kg / (1.6m ^ 2) = 60 / 2.56 = 23.44 (ปกติ)
        weight_kg = 60.0
        height_cm = 160.0
        bmi = weight_kg / ((height_cm / 100) ** 2)

        assert 18.5 <= bmi < 25.0  # ช่วงปกติ
        assert abs(bmi - 23.44) < 0.1

    def test_calculate_bmi_underweight(self, test_db):
        """ทดสอบคำนวณ BMI - ต่ำกว่าเกณฑ์"""
        # 40kg / (1.5m ^ 2) = 40 / 2.25 = 17.78 (ต่ำกว่าเกณฑ์)
        weight_kg = 40.0
        height_cm = 150.0
        bmi = weight_kg / ((height_cm / 100) ** 2)

        assert bmi < 18.5  # ต่ำกว่าเกณฑ์
        assert abs(bmi - 17.78) < 0.1

    def test_calculate_bmi_overweight(self, test_db):
        """ทดสอบคำนวณ BMI - เกินเกณฑ์"""
        # 80kg / (1.6m ^ 2) = 80 / 2.56 = 31.25 (เกินเกณฑ์)
        weight_kg = 80.0
        height_cm = 160.0
        bmi = weight_kg / ((height_cm / 100) ** 2)

        assert bmi >= 25.0  # เกินเกณฑ์
        assert abs(bmi - 31.25) < 0.1

    def test_get_latest_health(self, db_with_students):
        """ทดสอบดึงข้อมูลสุขภาพล่าสุด"""
        today = datetime.now()

        # บันทึกหลายครั้ง
        for i in range(3):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            health_data = {
                'student_id': '65001',
                'record_date': date,
                'brushed_teeth': 1,
                'drank_milk': 1,
                'weight_kg': 40.0 + i,
                'height_cm': 150.0,
                'bmi': (40.0 + i) / ((150.0 / 100) ** 2)
            }
            db_with_students.save_health_record(health_data)

        # ดึงข้อมูลล่าสุด
        latest = db_with_students.get_latest_health('65001')
        assert latest is not None
        assert latest['weight_kg'] == 40.0  # ข้อมูลล่าสุด

    def test_get_health_by_date_with_class(self, db_with_students, sample_date):
        """ทดสอบดึงข้อมูลสุขภาพตามวันที่และห้อง"""
        # บันทึกข้อมูลหลายคน
        for student_id in ['65001', '65002', '65003']:
            health_data = {
                'student_id': student_id,
                'record_date': sample_date,
                'brushed_teeth': 1,
                'drank_milk': 1,
                'weight_kg': 40.0,
                'height_cm': 150.0,
                'bmi': 17.78
            }
            db_with_students.save_health_record(health_data)

        # กรองตามห้อง
        records = db_with_students.get_health_by_date(sample_date, class_room='ป.1/1')
        assert len(records) == 2


class TestGrades:
    """ทดสอบการบันทึกเกรด"""

    def test_save_grade_new_record(self, db_with_students):
        """ทดสอบบันทึกเกรดใหม่"""
        grade_data = {
            'student_id': '65001',
            'academic_year': '2567',
            'semester': '1',
            'subject_code': 'TH101',
            'subject_name': 'ภาษาไทย',
            'full_score': 100,
            'score': 85,
            'grade': '4.0'
        }

        result = db_with_students.save_grade(grade_data)
        assert result is True

        # ตรวจสอบข้อมูล
        grades = db_with_students.get_grades('65001')
        assert len(grades) == 1
        assert grades[0]['score'] == 85
        assert grades[0]['grade'] == '4.0'

    def test_save_grade_update_existing(self, db_with_students):
        """ทดสอบอัพเดทเกรดที่มีอยู่แล้ว"""
        grade_data = {
            'student_id': '65001',
            'academic_year': '2567',
            'semester': '1',
            'subject_code': 'TH101',
            'subject_name': 'ภาษาไทย',
            'full_score': 100,
            'score': 75,
            'grade': '3.5'
        }
        db_with_students.save_grade(grade_data)

        # อัพเดท
        grade_data['score'] = 90
        grade_data['grade'] = '4.0'
        result = db_with_students.save_grade(grade_data)
        assert result is True

        grades = db_with_students.get_grades('65001')
        assert len(grades) == 1  # ยังคงมี 1 รายการ
        assert grades[0]['score'] == 90
        assert grades[0]['grade'] == '4.0'

    def test_calculate_grade_4_0(self, test_db):
        """ทดสอบคำนวณเกรด 4.0 (คะแนน >= 80)"""
        assert test_db.calculate_grade(80) == "4.0"
        assert test_db.calculate_grade(85) == "4.0"
        assert test_db.calculate_grade(100) == "4.0"

    def test_calculate_grade_3_5(self, test_db):
        """ทดสอบคำนวณเกรด 3.5 (คะแนน >= 75)"""
        assert test_db.calculate_grade(75) == "3.5"
        assert test_db.calculate_grade(77) == "3.5"
        assert test_db.calculate_grade(79) == "3.5"

    def test_calculate_grade_3_0(self, test_db):
        """ทดสอบคำนวณเกรด 3.0 (คะแนน >= 70)"""
        assert test_db.calculate_grade(70) == "3.0"
        assert test_db.calculate_grade(72) == "3.0"
        assert test_db.calculate_grade(74) == "3.0"

    def test_calculate_grade_2_5(self, test_db):
        """ทดสอบคำนวณเกรด 2.5 (คะแนน >= 65)"""
        assert test_db.calculate_grade(65) == "2.5"
        assert test_db.calculate_grade(69) == "2.5"

    def test_calculate_grade_2_0(self, test_db):
        """ทดสอบคำนวณเกรด 2.0 (คะแนน >= 60)"""
        assert test_db.calculate_grade(60) == "2.0"
        assert test_db.calculate_grade(64) == "2.0"

    def test_calculate_grade_1_5(self, test_db):
        """ทดสอบคำนวณเกรด 1.5 (คะแนน >= 55)"""
        assert test_db.calculate_grade(55) == "1.5"
        assert test_db.calculate_grade(59) == "1.5"

    def test_calculate_grade_1_0(self, test_db):
        """ทดสอบคำนวณเกรด 1.0 (คะแนน >= 50)"""
        assert test_db.calculate_grade(50) == "1.0"
        assert test_db.calculate_grade(54) == "1.0"

    def test_calculate_grade_0_0(self, test_db):
        """ทดสอบคำนวณเกรด 0.0 (คะแนน < 50)"""
        assert test_db.calculate_grade(0) == "0.0"
        assert test_db.calculate_grade(25) == "0.0"
        assert test_db.calculate_grade(49) == "0.0"

    def test_calculate_grade_none(self, test_db):
        """ทดสอบคำนวณเกรดเมื่อไม่มีคะแนน"""
        assert test_db.calculate_grade(None) == "-"

    def test_get_transcript(self, db_with_students):
        """ทดสอบดึง Transcript รายบุคคล"""
        # บันทึกหลายวิชา
        subjects = [
            ('TH101', 'ภาษาไทย', 85, '4.0'),
            ('MA101', 'คณิตศาสตร์', 75, '3.5'),
            ('EN101', 'ภาษาอังกฤษ', 70, '3.0'),
            ('SC101', 'วิทยาศาสตร์', 65, '2.5')
        ]

        for code, name, score, grade in subjects:
            grade_data = {
                'student_id': '65001',
                'academic_year': '2567',
                'semester': '1',
                'subject_code': code,
                'subject_name': name,
                'full_score': 100,
                'score': score,
                'grade': grade
            }
            db_with_students.save_grade(grade_data)

        transcript = db_with_students.get_transcript('65001')
        assert len(transcript) == 4
        assert transcript[0]['subject_name'] == 'ภาษาอังกฤษ'  # เรียงตาม subject_code

    def test_get_grades_by_year_semester(self, db_with_students):
        """ทดสอบดึงเกรดกรองตามปีและภาคเรียน"""
        # บันทึกหลายภาค
        for semester in ['1', '2']:
            grade_data = {
                'student_id': '65001',
                'academic_year': '2567',
                'semester': semester,
                'subject_code': f'TH10{semester}',
                'subject_name': 'ภาษาไทย',
                'full_score': 100,
                'score': 80,
                'grade': '4.0'
            }
            db_with_students.save_grade(grade_data)

        # ดึงเฉพาะภาค 1
        grades = db_with_students.get_grades('65001', semester='1')
        assert len(grades) == 1
        assert grades[0]['semester'] == '1'


class TestTeachers:
    """ทดสอบการจัดการครู"""

    def test_add_teacher_success(self, test_db):
        """ทดสอบเพิ่มครูใหม่สำเร็จ"""
        teacher_data = {
            'teacher_id': 'T999',
            'title': 'นาย',
            'first_name': 'ทดสอบ',
            'last_name': 'ครู',
            'phone': '0899999999'
        }

        result = test_db.add_teacher(teacher_data)
        assert result is True

        teacher = test_db.get_teacher_by_id('T999')
        assert teacher is not None
        assert teacher['first_name'] == 'ทดสอบ'

    def test_add_teacher_duplicate_id(self, db_with_teachers):
        """ทดสอบเพิ่มครูที่มี ID ซ้ำ - ต้องล้มเหลว"""
        teacher_data = {
            'teacher_id': 'T001',  # ID ซ้ำ
            'title': 'นาย',
            'first_name': 'ซ้ำ',
            'last_name': 'กัน',
            'phone': '0899999999'
        }

        result = db_with_teachers.add_teacher(teacher_data)
        assert result is False

    def test_get_all_teachers(self, db_with_teachers):
        """ทดสอบดึงรายชื่อครูทั้งหมด"""
        teachers = db_with_teachers.get_all_teachers()
        assert len(teachers) == 3

    def test_update_teacher_success(self, db_with_teachers):
        """ทดสอบแก้ไขข้อมูลครูสำเร็จ"""
        updated_data = {
            'title': 'นาย',
            'first_name': 'สมศักดิ์_แก้ไข',
            'last_name': 'สอนดี_แก้ไข',
            'phone': '0800000000'
        }

        result = db_with_teachers.update_teacher('T001', updated_data)
        assert result is True

        teacher = db_with_teachers.get_teacher_by_id('T001')
        assert teacher['first_name'] == 'สมศักดิ์_แก้ไข'
        assert teacher['phone'] == '0800000000'

    def test_delete_teacher_soft_delete(self, db_with_teachers):
        """ทดสอบลบครู (soft delete)"""
        result = db_with_teachers.delete_teacher('T001')
        assert result is True

        teacher = db_with_teachers.get_teacher_by_id('T001')
        assert teacher['is_active'] == 0

        # ไม่แสดงในรายการ active
        teachers = db_with_teachers.get_all_teachers(active_only=True)
        assert len(teachers) == 2


class TestSchedule:
    """ทดสอบตารางเรียน - สำคัญมากสำหรับการตรวจจับความขัดแย้ง"""

    def test_add_schedule_success(self, db_with_teachers):
        """ทดสอบเพิ่มตารางเรียนสำเร็จ"""
        schedule_data = {
            'class_room': 'ป.1/1',
            'day_of_week': 'จันทร์',
            'period_no': 1,
            'start_time': '08:00',
            'end_time': '09:00',
            'subject_name': 'คณิตศาสตร์',
            'teacher_id': 'T001',
            'room_no': '101'
        }

        result = db_with_teachers.add_schedule(schedule_data)
        assert result is True

    def test_add_schedule_teacher_conflict(self, db_with_teachers):
        """ทดสอบความขัดแย้งครู - ครูคนเดียวสอน 2 ห้องพร้อมกัน (ต้อง REJECT)"""
        # เพิ่มตารางแรก
        schedule1 = {
            'class_room': 'ป.1/1',
            'day_of_week': 'จันทร์',
            'period_no': 1,
            'start_time': '08:00',
            'end_time': '09:00',
            'subject_name': 'คณิตศาสตร์',
            'teacher_id': 'T001',
            'room_no': '101'
        }
        db_with_teachers.add_schedule(schedule1)

        # พยายามเพิ่มตารางซ้ำ (ครูเดียวกัน, วันเดียวกัน, คาบเดียวกัน)
        schedule2 = {
            'class_room': 'ป.2/1',  # ห้องต่างกัน
            'day_of_week': 'จันทร์',  # วันเดียวกัน
            'period_no': 1,  # คาบเดียวกัน
            'start_time': '08:00',
            'end_time': '09:00',
            'subject_name': 'วิทยาศาสตร์',
            'teacher_id': 'T001',  # ครูเดียวกัน
            'room_no': '201'
        }

        result = db_with_teachers.add_schedule(schedule2)

        # ต้องได้ error message
        assert result is not True
        assert isinstance(result, str)
        assert 'มีคาบสอนอยู่แล้ว' in result
        assert 'จันทร์' in result
        assert 'คาบที่ 1' in result

    def test_check_teacher_conflict_message_format(self, db_with_teachers):
        """ทดสอบรูปแบบข้อความแจ้งเตือนความขัดแย้ง"""
        # เพิ่มตารางแรก
        schedule1 = {
            'class_room': 'ป.1/1',
            'day_of_week': 'อังคาร',
            'period_no': 3,
            'start_time': '10:00',
            'end_time': '11:00',
            'subject_name': 'ภาษาไทย',
            'teacher_id': 'T001',
            'room_no': '101'
        }
        db_with_teachers.add_schedule(schedule1)

        # ตรวจสอบความขัดแย้ง
        conflict = db_with_teachers.check_teacher_conflict('T001', 'อังคาร', 3)

        assert conflict is not None
        assert 'ครู' in conflict
        assert 'นายสมศักดิ์ สอนดี' in conflict
        assert 'อังคาร' in conflict
        assert 'คาบที่ 3' in conflict
        assert 'ป.1/1' in conflict

    def test_add_schedule_no_conflict_different_period(self, db_with_teachers):
        """ทดสอบไม่มีความขัดแย้ง - ครูเดียวกัน วันเดียวกัน แต่คาบต่างกัน"""
        schedule1 = {
            'class_room': 'ป.1/1',
            'day_of_week': 'พุธ',
            'period_no': 1,
            'start_time': '08:00',
            'end_time': '09:00',
            'subject_name': 'คณิตศาสตร์',
            'teacher_id': 'T001',
            'room_no': '101'
        }
        db_with_teachers.add_schedule(schedule1)

        schedule2 = {
            'class_room': 'ป.2/1',
            'day_of_week': 'พุธ',
            'period_no': 2,  # คาบต่างกัน
            'start_time': '09:00',
            'end_time': '10:00',
            'subject_name': 'วิทยาศาสตร์',
            'teacher_id': 'T001',
            'room_no': '201'
        }

        result = db_with_teachers.add_schedule(schedule2)
        assert result is True

    def test_add_schedule_no_conflict_different_day(self, db_with_teachers):
        """ทดสอบไม่มีความขัดแย้ง - ครูเดียวกัน คาบเดียวกัน แต่วันต่างกัน"""
        schedule1 = {
            'class_room': 'ป.1/1',
            'day_of_week': 'พฤหัสบดี',
            'period_no': 1,
            'start_time': '08:00',
            'end_time': '09:00',
            'subject_name': 'คณิตศาสตร์',
            'teacher_id': 'T001',
            'room_no': '101'
        }
        db_with_teachers.add_schedule(schedule1)

        schedule2 = {
            'class_room': 'ป.2/1',
            'day_of_week': 'ศุกร์',  # วันต่างกัน
            'period_no': 1,
            'start_time': '08:00',
            'end_time': '09:00',
            'subject_name': 'วิทยาศาสตร์',
            'teacher_id': 'T001',
            'room_no': '201'
        }

        result = db_with_teachers.add_schedule(schedule2)
        assert result is True

    def test_get_schedule_by_class(self, db_with_teachers):
        """ทดสอบดึงตารางเรียนตามห้อง"""
        # เพิ่มหลายคาบ
        days = ['จันทร์', 'อังคาร', 'พุธ']
        for i, day in enumerate(days, 1):
            schedule = {
                'class_room': 'ป.1/1',
                'day_of_week': day,
                'period_no': i,
                'start_time': f'{7+i}:00',
                'end_time': f'{8+i}:00',
                'subject_name': f'วิชา{i}',
                'teacher_id': 'T001',
                'room_no': '101'
            }
            db_with_teachers.add_schedule(schedule)

        schedules = db_with_teachers.get_schedule_by_class('ป.1/1')
        assert len(schedules) == 3

    def test_get_schedule_by_teacher(self, db_with_teachers):
        """ทดสอบดึงตารางสอนของครู"""
        # ครู T001 สอน 3 คาบ
        for i in range(1, 4):
            schedule = {
                'class_room': 'ป.1/1',
                'day_of_week': 'จันทร์',
                'period_no': i,
                'start_time': f'{7+i}:00',
                'end_time': f'{8+i}:00',
                'subject_name': f'วิชา{i}',
                'teacher_id': 'T001',
                'room_no': '101'
            }
            db_with_teachers.add_schedule(schedule)

        schedules = db_with_teachers.get_schedule_by_teacher('T001')
        assert len(schedules) == 3

    def test_calculate_teacher_workload(self, db_with_teachers):
        """ทดสอบคำนวณภาระงานครู (จำนวนคาบต่อสัปดาห์)"""
        # ครู T001 สอน 5 คาบ
        for i in range(1, 6):
            schedule = {
                'class_room': 'ป.1/1',
                'day_of_week': 'จันทร์',
                'period_no': i,
                'start_time': f'{7+i}:00',
                'end_time': f'{8+i}:00',
                'subject_name': f'วิชา{i}',
                'teacher_id': 'T001',
                'room_no': '101'
            }
            db_with_teachers.add_schedule(schedule)

        # ครู T002 สอน 3 คาบ
        for i in range(1, 4):
            schedule = {
                'class_room': 'ป.2/1',
                'day_of_week': 'อังคาร',
                'period_no': i,
                'start_time': f'{7+i}:00',
                'end_time': f'{8+i}:00',
                'subject_name': f'วิชา{i}',
                'teacher_id': 'T002',
                'room_no': '201'
            }
            db_with_teachers.add_schedule(schedule)

        workload = db_with_teachers.get_teacher_workload()

        # T001 ต้องมีภาระงานมากกว่า
        t001_workload = next(w for w in workload if w['teacher_id'] == 'T001')
        t002_workload = next(w for w in workload if w['teacher_id'] == 'T002')

        assert t001_workload['periods_per_week'] == 5
        assert t002_workload['periods_per_week'] == 3

    def test_update_schedule_with_conflict_check(self, db_with_teachers):
        """ทดสอบแก้ไขตารางพร้อมตรวจสอบความขัดแย้ง"""
        # เพิ่ม 2 ตาราง
        schedule1 = {
            'class_room': 'ป.1/1',
            'day_of_week': 'จันทร์',
            'period_no': 1,
            'start_time': '08:00',
            'end_time': '09:00',
            'subject_name': 'คณิตศาสตร์',
            'teacher_id': 'T001',
            'room_no': '101'
        }
        db_with_teachers.add_schedule(schedule1)

        schedule2 = {
            'class_room': 'ป.2/1',
            'day_of_week': 'จันทร์',
            'period_no': 2,
            'start_time': '09:00',
            'end_time': '10:00',
            'subject_name': 'วิทยาศาสตร์',
            'teacher_id': 'T002',
            'room_no': '201'
        }
        db_with_teachers.add_schedule(schedule2)

        # ดึง ID ของตารางที่ 2
        schedules = db_with_teachers.get_all_schedules()
        schedule2_id = next(s['id'] for s in schedules if s['teacher_id'] == 'T002')

        # พยายามแก้ไขให้ซ้ำกับตารางแรก
        updated_data = {
            'class_room': 'ป.3/1',
            'day_of_week': 'จันทร์',
            'period_no': 1,  # ซ้ำกับ T001
            'start_time': '08:00',
            'end_time': '09:00',
            'subject_name': 'วิทยาศาสตร์',
            'teacher_id': 'T001',  # เปลี่ยนครู แต่ซ้ำกับตารางแรก
            'room_no': '301'
        }

        result = db_with_teachers.update_schedule(schedule2_id, updated_data)
        assert result is not True
        assert isinstance(result, str)
        assert 'มีคาบสอนอยู่แล้ว' in result

    def test_delete_schedule(self, db_with_teachers):
        """ทดสอบลบตารางเรียน"""
        schedule = {
            'class_room': 'ป.1/1',
            'day_of_week': 'จันทร์',
            'period_no': 1,
            'start_time': '08:00',
            'end_time': '09:00',
            'subject_name': 'คณิตศาสตร์',
            'teacher_id': 'T001',
            'room_no': '101'
        }
        db_with_teachers.add_schedule(schedule)

        schedules = db_with_teachers.get_all_schedules()
        schedule_id = schedules[0]['id']

        result = db_with_teachers.delete_schedule(schedule_id)
        assert result is True

        # ตรวจสอบว่าถูกลบจริง
        schedules = db_with_teachers.get_all_schedules()
        assert len(schedules) == 0
