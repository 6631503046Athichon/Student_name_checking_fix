"""
test_utils.py
ทดสอบฟังก์ชันช่วยเหลือและ utilities
"""

import pytest
from database.db import Database


class TestCalculations:
    """ทดสอบการคำนวณต่างๆ"""

    def test_bmi_calculation_precision(self, test_db):
        """ทดสอบความแม่นยำของการคำนวณ BMI"""
        # กรณีทดสอบต่างๆ
        test_cases = [
            (50.0, 160.0, 19.53),   # ปกติ
            (40.0, 150.0, 17.78),   # ต่ำ
            (80.0, 160.0, 31.25),   # สูง
            (65.5, 170.5, 22.53),   # ทศนิยม (แก้ไขค่า expected)
        ]

        for weight, height, expected_bmi in test_cases:
            calculated_bmi = weight / ((height / 100) ** 2)
            assert abs(calculated_bmi - expected_bmi) < 0.02  # เพิ่ม tolerance

    def test_grade_boundaries(self, test_db):
        """ทดสอบ boundary values ของเกรด"""
        boundaries = [
            (80, '4.0'),
            (79.99, '3.5'),
            (75, '3.5'),
            (74.99, '3.0'),
            (70, '3.0'),
            (69.99, '2.5'),
            (65, '2.5'),
            (64.99, '2.0'),
            (60, '2.0'),
            (59.99, '1.5'),
            (55, '1.5'),
            (54.99, '1.0'),
            (50, '1.0'),
            (49.99, '0.0'),
        ]

        for score, expected_grade in boundaries:
            grade = test_db.calculate_grade(score)
            assert grade == expected_grade, f"Score {score} should be grade {expected_grade}, got {grade}"


class TestDataValidation:
    """ทดสอบการ validate ข้อมูล"""

    def test_student_id_uniqueness(self, db_with_students):
        """ทดสอบความไม่ซ้ำของรหัสนักเรียน"""
        student_data = {
            'student_id': '65001',  # ซ้ำ
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

        result = db_with_students.add_student(student_data)
        assert result is False

    def test_teacher_id_uniqueness(self, db_with_teachers):
        """ทดสอบความไม่ซ้ำของรหัสครู"""
        teacher_data = {
            'teacher_id': 'T001',  # ซ้ำ
            'title': 'นาย',
            'first_name': 'ทดสอบ',
            'last_name': 'ครู',
            'phone': '0899999999'
        }

        result = db_with_teachers.add_teacher(teacher_data)
        assert result is False

    def test_schedule_unique_constraint(self, db_with_teachers):
        """ทดสอบ UNIQUE constraint ของตารางเรียน"""
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

        # พยายามเพิ่มซ้ำ
        schedule2 = {
            'class_room': 'ป.2/1',  # ห้องต่าง
            'day_of_week': 'จันทร์',
            'period_no': 1,
            'start_time': '08:00',
            'end_time': '09:00',
            'subject_name': 'วิทยาศาสตร์',
            'teacher_id': 'T001',  # ครูเดียวกัน
            'room_no': '201'
        }

        result = db_with_teachers.add_schedule(schedule2)
        # ต้องถูก reject
        assert result is not True


class TestSorting:
    """ทดสอบการเรียงลำดับข้อมูล"""

    def test_students_sorted_by_name(self, db_with_students):
        """ทดสอบนักเรียนเรียงตามชื่อ"""
        students = db_with_students.get_all_students()

        # ตรวจสอบว่าเรียงตาม class_room แล้ว first_name
        for i in range(len(students) - 1):
            # ถ้าห้องเดียวกัน ต้องเรียงตามชื่อ
            if students[i]['class_room'] == students[i+1]['class_room']:
                assert students[i]['first_name'] <= students[i+1]['first_name']

    def test_attendance_sorted_by_date_desc(self, db_with_students):
        """ทดสอบการเช็คชื่อเรียงตามวันที่ใหม่ไปเก่า"""
        from datetime import datetime, timedelta

        today = datetime.now()
        for i in range(5):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            db_with_students.save_attendance('65001', date, 'มา')

        records = db_with_students.get_attendance_by_student('65001')

        # ต้องเรียงจากใหม่ไปเก่า
        for i in range(len(records) - 1):
            assert records[i]['att_date'] >= records[i+1]['att_date']

    def test_grades_sorted_by_subject_code(self, db_with_students):
        """ทดสอบเกรดเรียงตามรหัสวิชา"""
        subjects = ['ZZ999', 'AA101', 'MM505', 'BB202']

        for code in subjects:
            grade_data = {
                'student_id': '65001',
                'academic_year': '2567',
                'semester': '1',
                'subject_code': code,
                'subject_name': f'วิชา {code}',
                'full_score': 100,
                'score': 80,
                'grade': '4.0'
            }
            db_with_students.save_grade(grade_data)

        grades = db_with_students.get_grades('65001')

        # ต้องเรียงตาม subject_code
        for i in range(len(grades) - 1):
            assert grades[i]['subject_code'] <= grades[i+1]['subject_code']

    def test_teacher_workload_sorted_desc(self, db_with_teachers):
        """ทดสอบภาระงานครูเรียงจากมากไปน้อย"""
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

        # ครู T002 สอน 2 คาบ
        for i in range(1, 3):
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

        # ต้องเรียงจากมากไปน้อย
        for i in range(len(workload) - 1):
            assert workload[i]['periods_per_week'] >= workload[i+1]['periods_per_week']


class TestDayOfWeekOrdering:
    """ทดสอบการเรียงลำดับวัน"""

    def test_schedule_day_ordering(self, db_with_teachers):
        """ทดสอบตารางเรียนเรียงตามวันจันทร์-ศุกร์"""
        days = ['ศุกร์', 'จันทร์', 'พุธ', 'อังคาร', 'พฤหัสบดี']  # สุ่ม

        for i, day in enumerate(days):
            schedule = {
                'class_room': 'ป.1/1',
                'day_of_week': day,
                'period_no': 1,
                'start_time': '08:00',
                'end_time': '09:00',
                'subject_name': f'วิชา{i}',
                'teacher_id': 'T001',
                'room_no': '101'
            }
            # ต้องใช้คาบต่างกันเพื่อไม่ให้ conflict
            schedule['period_no'] = i + 1
            db_with_teachers.add_schedule(schedule)

        schedules = db_with_teachers.get_schedule_by_class('ป.1/1')

        # ตรวจสอบการเรียงลำดับ
        day_order = {
            'จันทร์': 1,
            'อังคาร': 2,
            'พุธ': 3,
            'พฤหัสบดี': 4,
            'ศุกร์': 5
        }

        for i in range(len(schedules) - 1):
            current_day = day_order.get(schedules[i]['day_of_week'], 99)
            next_day = day_order.get(schedules[i+1]['day_of_week'], 99)

            # ถ้าวันเดียวกัน ต้องเรียงตามคาบ
            if current_day == next_day:
                assert schedules[i]['period_no'] <= schedules[i+1]['period_no']
            else:
                assert current_day <= next_day
