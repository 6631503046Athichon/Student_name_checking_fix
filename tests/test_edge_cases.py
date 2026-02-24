"""
test_edge_cases.py
ทดสอบ Edge Cases และ Error Handling
"""

import pytest
from datetime import datetime


class TestEdgeCasesStudents:
    """ทดสอบกรณีพิเศษสำหรับนักเรียน"""

    def test_student_with_empty_fields(self, test_db):
        """ทดสอบเพิ่มนักเรียนที่มีฟิลด์ว่าง (optional fields)"""
        student_data = {
            'student_id': '68001',
            'title': 'เด็กชาย',
            'first_name': 'ทดสอบ',
            'last_name': 'ระบบ',
            'class_room': 'ป.1/1',
            'class_year': '2567',
            'birth_date': None,  # ว่าง
            'parent_name': None,  # ว่าง
            'parent_phone': None,  # ว่าง
            'photo_path': None
        }

        result = test_db.add_student(student_data)
        assert result is True

        student = test_db.get_student_by_id('68001')
        assert student['birth_date'] is None
        assert student['parent_name'] is None

    def test_student_with_special_characters(self, test_db):
        """ทดสอบชื่อที่มีอักขระพิเศษ"""
        student_data = {
            'student_id': '68002',
            'title': 'เด็กหญิง',
            'first_name': 'ก้อย-กุ้ง',  # มีเครื่องหมาย
            'last_name': "O'Brien",  # มี apostrophe
            'class_room': 'ป.1/1',
            'class_year': '2567',
            'birth_date': '2016-01-01',
            'parent_name': 'นาย Test',
            'parent_phone': '081-234-5678',  # มีขีด
            'photo_path': None
        }

        result = test_db.add_student(student_data)
        assert result is True

        student = test_db.get_student_by_id('68002')
        assert student['first_name'] == 'ก้อย-กุ้ง'
        assert student['last_name'] == "O'Brien"

    def test_search_with_empty_keyword(self, db_with_students):
        """ทดสอบค้นหาด้วยคำค้นว่าง"""
        results = db_with_students.search_students('')
        # ต้องไม่ error และส่งคืนรายการว่าง หรือทั้งหมด (ขึ้นอยู่กับการ implement)
        assert isinstance(results, list)

    def test_search_with_special_sql_characters(self, db_with_students):
        """ทดสอบค้นหาด้วยอักขระพิเศษ SQL (ป้องกัน SQL injection)"""
        # ทดสอบอักขระที่อาจเป็นอันตราย
        dangerous_keywords = ["'; DROP TABLE students; --", "%", "_", "\\"]

        for keyword in dangerous_keywords:
            try:
                results = db_with_students.search_students(keyword)
                # ต้องไม่ error
                assert isinstance(results, list)
            except Exception as e:
                pytest.fail(f"Search failed with keyword '{keyword}': {e}")

    def test_get_nonexistent_student(self, test_db):
        """ทดสอบดึงข้อมูลนักเรียนที่ไม่มีอยู่"""
        student = test_db.get_student_by_id('99999')
        assert student is None

    def test_update_nonexistent_student(self, test_db):
        """ทดสอบแก้ไขนักเรียนที่ไม่มีอยู่"""
        student_data = {
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

        # ควรสำเร็จ (แต่ไม่มีการเปลี่ยนแปลงข้อมูล)
        result = test_db.update_student('99999', student_data)
        assert result is True

    def test_delete_already_deleted_student(self, db_with_students):
        """ทดสอบลบนักเรียนที่ถูกลบแล้ว"""
        # ลบครั้งแรก
        result1 = db_with_students.delete_student('65001')
        assert result1 is True

        # ลบอีกครั้ง
        result2 = db_with_students.delete_student('65001')
        assert result2 is True  # ยังคงสำเร็จ


class TestEdgeCasesAttendance:
    """ทดสอบกรณีพิเศษสำหรับการเช็คชื่อ"""

    def test_attendance_for_nonexistent_student(self, test_db, sample_date):
        """ทดสอบบันทึกการเช็คชื่อสำหรับนักเรียนที่ไม่มี"""
        # ควรทำงานได้ แต่ถ้ามี FK constraint จะ fail
        result = test_db.save_attendance('99999', sample_date, 'มา')
        # อาจเป็น True หรือ False ขึ้นอยู่กับ FK constraint
        assert isinstance(result, bool)

    def test_attendance_invalid_status(self, db_with_students, sample_date):
        """ทดสอบบันทึกสถานะที่ไม่ถูกต้อง"""
        # บันทึกสถานะแปลกๆ
        result = db_with_students.save_attendance('65001', sample_date, 'สถานะแปลก')
        # ควรทำงานได้ (ไม่มี constraint)
        assert result is True

        records = db_with_students.get_attendance_by_date(sample_date)
        assert records[0]['status'] == 'สถานะแปลก'

    def test_attendance_future_date(self, db_with_students):
        """ทดสอบบันทึกการเช็คชื่อวันในอนาคต"""
        future_date = '2030-12-31'
        result = db_with_students.save_attendance('65001', future_date, 'มา')
        assert result is True

    def test_attendance_very_old_date(self, db_with_students):
        """ทดสอบบันทึกการเช็คชื่อวันในอดีตไกล"""
        old_date = '1990-01-01'
        result = db_with_students.save_attendance('65001', old_date, 'มา')
        assert result is True

    def test_get_attendance_with_no_records(self, test_db, sample_date):
        """ทดสอบดึงการเช็คชื่อที่ไม่มีข้อมูล"""
        records = test_db.get_attendance_by_date(sample_date)
        assert len(records) == 0
        assert isinstance(records, list)

    def test_attendance_stats_no_records(self, db_with_students):
        """ทดสอบสถิติการเช็คชื่อสำหรับนักเรียนที่ไม่มีประวัติ"""
        stats = db_with_students.get_attendance_stats('65001')
        assert stats['มา'] == 0
        assert stats['ขาด'] == 0
        assert stats['ลา'] == 0
        assert stats['มาสาย'] == 0


class TestEdgeCasesHealth:
    """ทดสอบกรณีพิเศษสำหรับสุขภาพ"""

    def test_health_negative_weight(self, db_with_students, sample_date):
        """ทดสอบบันทึกน้ำหนักติดลบ"""
        health_data = {
            'student_id': '65001',
            'record_date': sample_date,
            'brushed_teeth': 1,
            'drank_milk': 1,
            'weight_kg': -10.0,  # ติดลบ
            'height_cm': 150.0,
            'bmi': -10.0 / ((150.0 / 100) ** 2)
        }

        # ควรทำงานได้ (ไม่มี validation)
        result = db_with_students.save_health_record(health_data)
        assert result is True

    def test_health_zero_height(self, db_with_students, sample_date):
        """ทดสอบบันทึกส่วนสูงเป็น 0 (จะทำให้ BMI error)"""
        health_data = {
            'student_id': '65001',
            'record_date': sample_date,
            'brushed_teeth': 1,
            'drank_milk': 1,
            'weight_kg': 40.0,
            'height_cm': 0.0,  # ส่วนสูง 0
            'bmi': None
        }

        result = db_with_students.save_health_record(health_data)
        assert result is True

    def test_health_extremely_high_bmi(self, db_with_students, sample_date):
        """ทดสอบ BMI สูงมาก"""
        # 200kg / (1.5m)^2 = 88.89
        weight_kg = 200.0
        height_cm = 150.0
        bmi = weight_kg / ((height_cm / 100) ** 2)

        health_data = {
            'student_id': '65001',
            'record_date': sample_date,
            'brushed_teeth': 1,
            'drank_milk': 1,
            'weight_kg': weight_kg,
            'height_cm': height_cm,
            'bmi': bmi
        }

        result = db_with_students.save_health_record(health_data)
        assert result is True
        assert bmi > 80  # BMI สูงมาก

    def test_get_health_no_records(self, db_with_students):
        """ทดสอบดึงข้อมูลสุขภาพที่ไม่มี"""
        records = db_with_students.get_health_records('65001')
        assert len(records) == 0

    def test_get_latest_health_no_weight_height(self, db_with_students, sample_date):
        """ทดสอบดึงข้อมูลล่าสุดเมื่อไม่มีน้ำหนัก-ส่วนสูง"""
        # บันทึกเฉพาะแปรงฟัน/ดื่มนม
        db_with_students.update_health_daily('65001', sample_date, 1, 1)

        latest = db_with_students.get_latest_health('65001')
        # ต้องไม่มีข้อมูล (query กรองเฉพาะที่มี weight_kg หรือ height_cm)
        assert latest is None


class TestEdgeCasesGrades:
    """ทดสอบกรณีพิเศษสำหรับเกรด"""

    def test_grade_score_over_100(self, db_with_students):
        """ทดสอบคะแนนเกิน 100"""
        grade_data = {
            'student_id': '65001',
            'academic_year': '2567',
            'semester': '1',
            'subject_code': 'TH101',
            'subject_name': 'ภาษาไทย',
            'full_score': 100,
            'score': 150,  # เกิน 100
            'grade': db_with_students.calculate_grade(150)
        }

        result = db_with_students.save_grade(grade_data)
        assert result is True
        assert grade_data['grade'] == '4.0'  # ยังคงเป็น 4.0

    def test_grade_negative_score(self, db_with_students):
        """ทดสอบคะแนนติดลบ"""
        score = -10
        grade = db_with_students.calculate_grade(score)
        assert grade == '0.0'

    def test_grade_float_score(self, db_with_students):
        """ทดสอบคะแนนทศนิยม"""
        # ทดสอบ boundary
        assert db_with_students.calculate_grade(79.9) == '3.5'
        assert db_with_students.calculate_grade(80.0) == '4.0'
        assert db_with_students.calculate_grade(74.9) == '3.0'
        assert db_with_students.calculate_grade(75.0) == '3.5'

    def test_grade_none_score(self, db_with_students):
        """ทดสอบคะแนน None"""
        grade = db_with_students.calculate_grade(None)
        assert grade == '-'

    def test_get_grades_no_records(self, db_with_students):
        """ทดสอบดึงเกรดที่ไม่มีข้อมูล"""
        grades = db_with_students.get_grades('65001')
        assert len(grades) == 0

    def test_transcript_empty(self, db_with_students):
        """ทดสอบ Transcript ว่าง"""
        transcript = db_with_students.get_transcript('65001')
        assert len(transcript) == 0
        assert isinstance(transcript, list)


class TestEdgeCasesTeachers:
    """ทดสอบกรณีพิเศษสำหรับครู"""

    def test_teacher_with_empty_phone(self, test_db):
        """ทดสอบครูที่ไม่มีเบอร์โทร"""
        teacher_data = {
            'teacher_id': 'T999',
            'title': 'นาย',
            'first_name': 'ทดสอบ',
            'last_name': 'ครู',
            'phone': None
        }

        result = test_db.add_teacher(teacher_data)
        assert result is True

    def test_get_nonexistent_teacher(self, test_db):
        """ทดสอบดึงข้อมูลครูที่ไม่มี"""
        teacher = test_db.get_teacher_by_id('T999')
        assert teacher is None

    def test_teacher_workload_no_schedule(self, db_with_teachers):
        """ทดสอบภาระงานครูที่ไม่มีตารางสอน"""
        workload = db_with_teachers.get_teacher_workload()

        # ครูทุกคนควรมีภาระงาน 0
        for w in workload:
            assert w['periods_per_week'] == 0


class TestEdgeCasesSchedule:
    """ทดสอบกรณีพิเศษสำหรับตารางเรียน"""

    def test_schedule_invalid_day(self, db_with_teachers):
        """ทดสอบวันที่ไม่ถูกต้อง"""
        schedule_data = {
            'class_room': 'ป.1/1',
            'day_of_week': 'วันพุธ',  # ผิดรูปแบบ (ควรเป็น 'พุธ')
            'period_no': 1,
            'start_time': '08:00',
            'end_time': '09:00',
            'subject_name': 'คณิตศาสตร์',
            'teacher_id': 'T001',
            'room_no': '101'
        }

        # ควรทำงานได้ (ไม่มี validation)
        result = db_with_teachers.add_schedule(schedule_data)
        assert result is True

    def test_schedule_period_zero(self, db_with_teachers):
        """ทดสอบคาบที่ 0"""
        schedule_data = {
            'class_room': 'ป.1/1',
            'day_of_week': 'จันทร์',
            'period_no': 0,  # คาบที่ 0
            'start_time': '07:00',
            'end_time': '08:00',
            'subject_name': 'คณิตศาสตร์',
            'teacher_id': 'T001',
            'room_no': '101'
        }

        result = db_with_teachers.add_schedule(schedule_data)
        assert result is True

    def test_schedule_negative_period(self, db_with_teachers):
        """ทดสอบคาบติดลบ"""
        schedule_data = {
            'class_room': 'ป.1/1',
            'day_of_week': 'จันทร์',
            'period_no': -1,  # คาบติดลบ
            'start_time': '08:00',
            'end_time': '09:00',
            'subject_name': 'คณิตศาสตร์',
            'teacher_id': 'T001',
            'room_no': '101'
        }

        result = db_with_teachers.add_schedule(schedule_data)
        assert result is True

    def test_schedule_end_time_before_start_time(self, db_with_teachers):
        """ทดสอบเวลาสิ้นสุดก่อนเวลาเริ่ม"""
        schedule_data = {
            'class_room': 'ป.1/1',
            'day_of_week': 'จันทร์',
            'period_no': 1,
            'start_time': '10:00',
            'end_time': '09:00',  # ก่อนเวลาเริ่ม
            'subject_name': 'คณิตศาสตร์',
            'teacher_id': 'T001',
            'room_no': '101'
        }

        result = db_with_teachers.add_schedule(schedule_data)
        assert result is True

    def test_get_schedule_empty(self, db_with_teachers):
        """ทดสอบดึงตารางที่ว่าง"""
        schedules = db_with_teachers.get_schedule_by_class('ป.99/99')
        assert len(schedules) == 0

    def test_delete_nonexistent_schedule(self, test_db):
        """ทดสอบลบตารางที่ไม่มี"""
        result = test_db.delete_schedule(99999)
        # ควรสำเร็จ (แต่ไม่มีการเปลี่ยนแปลง)
        assert result is True

    def test_check_conflict_with_exclude_id(self, db_with_teachers):
        """ทดสอบตรวจสอบความขัดแย้งโดยไม่รวม ID ที่กำลังแก้ไข"""
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
        db_with_teachers.add_schedule(schedule_data)

        schedules = db_with_teachers.get_all_schedules()
        schedule_id = schedules[0]['id']

        # ตรวจสอบความขัดแย้ง แต่ไม่รวมตัวเอง
        conflict = db_with_teachers.check_teacher_conflict(
            'T001', 'จันทร์', 1, exclude_id=schedule_id
        )

        # ต้องไม่มีความขัดแย้ง (เพราะไม่รวมตัวเอง)
        assert conflict is None


class TestDatabaseConnection:
    """ทดสอบการเชื่อมต่อฐานข้อมูล"""

    def test_create_db_with_custom_path(self):
        """ทดสอบสร้าง DB ที่ path กำหนดเอง"""
        import os
        from database.db import Database

        custom_path = "custom_test.db"

        # ลบไฟล์เก่าถ้ามี
        if os.path.exists(custom_path):
            os.remove(custom_path)

        db = Database(custom_path)

        # ตรวจสอบว่าไฟล์ถูกสร้าง
        assert os.path.exists(custom_path)

        db.close()
        os.remove(custom_path)

    def test_database_tables_created(self, test_db):
        """ทดสอบว่าตารางทั้งหมดถูกสร้าง"""
        # ตรวจสอบว่าตารางทั้งหมดมีอยู่
        test_db.cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)

        tables = [row[0] for row in test_db.cursor.fetchall()]

        expected_tables = [
            'students',
            'attendance',
            'health_records',
            'grades',
            'teachers',
            'schedule'
        ]

        for table in expected_tables:
            assert table in tables

    def test_database_indexes_created(self, test_db):
        """ทดสอบว่า indexes ถูกสร้าง"""
        test_db.cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index'
            ORDER BY name
        """)

        indexes = [row[0] for row in test_db.cursor.fetchall()]

        expected_indexes = [
            'idx_attendance_date',
            'idx_health_date',
            'idx_grades_year',
            'idx_schedule_class'
        ]

        for index in expected_indexes:
            assert index in indexes
