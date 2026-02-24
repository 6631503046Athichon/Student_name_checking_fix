"""
test_integration.py
ทดสอบการทำงานร่วมกันของหลายโมดูล (Integration Tests)
"""

import pytest
from datetime import datetime, timedelta


class TestStudentAttendanceFlow:
    """Scenario 1: เพิ่มนักเรียนใหม่ → เช็คชื่อ → ดูสถิติ"""

    def test_complete_student_attendance_workflow(self, test_db):
        """ทดสอบ workflow สมบูรณ์: เพิ่มนักเรียน → บันทึกการเช็คชื่อ → ดูสถิติ"""
        # 1. เพิ่มนักเรียน 5 คน
        students = []
        for i in range(1, 6):
            student_data = {
                'student_id': f'6600{i}',
                'title': 'เด็กชาย' if i % 2 == 1 else 'เด็กหญิง',
                'first_name': f'นักเรียน{i}',
                'last_name': f'ทดสอบ{i}',
                'class_room': 'ป.1/1',
                'class_year': '2567',
                'birth_date': f'2016-0{i}-01',
                'parent_name': f'ผู้ปกครอง{i}',
                'parent_phone': f'08{i}234567{i}',
                'photo_path': None
            }
            result = test_db.add_student(student_data)
            assert result is True
            students.append(student_data)

        # ตรวจสอบว่ามีนักเรียน 5 คน
        all_students = test_db.get_all_students()
        assert len(all_students) == 5

        # 2. เช็คชื่อ 3 วัน
        today = datetime.now()
        attendance_records = []

        for day in range(3):
            date = (today - timedelta(days=day)).strftime('%Y-%m-%d')

            for i, student in enumerate(students):
                # นักเรียนคนที่ 1-3 มา, คนที่ 4 ขาด, คนที่ 5 ลา
                if i < 3:
                    status = 'มา'
                elif i == 3:
                    status = 'ขาด'
                else:
                    status = 'ลา'

                result = test_db.save_attendance(
                    student['student_id'],
                    date,
                    status
                )
                assert result is True
                attendance_records.append((student['student_id'], date, status))

        # ตรวจสอบว่ามีการบันทึก 15 รายการ (5 คน × 3 วัน)
        assert len(attendance_records) == 15

        # 3. ตรวจสอบสถิติของนักเรียนแต่ละคน
        # นักเรียนคนที่ 1-3: มา 3 วัน
        for i in range(1, 4):
            stats = test_db.get_attendance_stats(f'6600{i}')
            assert stats['มา'] == 3
            assert stats['ขาด'] == 0
            assert stats['ลา'] == 0
            assert stats['มาสาย'] == 0

        # นักเรียนคนที่ 4: ขาด 3 วัน
        stats = test_db.get_attendance_stats('66004')
        assert stats['มา'] == 0
        assert stats['ขาด'] == 3
        assert stats['ลา'] == 0

        # นักเรียนคนที่ 5: ลา 3 วัน
        stats = test_db.get_attendance_stats('66005')
        assert stats['มา'] == 0
        assert stats['ขาด'] == 0
        assert stats['ลา'] == 3

        # 4. หานักเรียนที่ขาดเกิน 2 วัน
        absent_students = test_db.get_students_absent_more_than(2)
        assert len(absent_students) == 1
        assert absent_students[0]['student_id'] == '66004'


class TestHealthBMITracking:
    """Scenario 4: สุขภาพ - BMI Calculation และการติดตาม"""

    def test_bmi_calculation_and_tracking(self, db_with_students):
        """ทดสอบคำนวณ BMI และติดตามการเปลี่ยนแปลง"""
        student_id = '65001'
        today = datetime.now()

        # 1. บันทึก BMI ต่ำกว่าเกณฑ์
        date1 = (today - timedelta(days=60)).strftime('%Y-%m-%d')
        health1 = {
            'student_id': student_id,
            'record_date': date1,
            'brushed_teeth': 1,
            'drank_milk': 1,
            'weight_kg': 40.0,
            'height_cm': 150.0,
            'bmi': 40.0 / ((150.0 / 100) ** 2)  # 17.78
        }
        result = db_with_students.save_health_record(health1)
        assert result is True
        assert health1['bmi'] < 18.5  # ต่ำกว่าเกณฑ์

        # 2. บันทึก BMI ปกติ
        date2 = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        health2 = {
            'student_id': student_id,
            'record_date': date2,
            'brushed_teeth': 1,
            'drank_milk': 1,
            'weight_kg': 60.0,
            'height_cm': 160.0,
            'bmi': 60.0 / ((160.0 / 100) ** 2)  # 23.44
        }
        result = db_with_students.save_health_record(health2)
        assert result is True
        assert 18.5 <= health2['bmi'] < 25.0  # ปกติ

        # 3. บันทึก BMI เกินเกณฑ์
        date3 = today.strftime('%Y-%m-%d')
        health3 = {
            'student_id': student_id,
            'record_date': date3,
            'brushed_teeth': 1,
            'drank_milk': 1,
            'weight_kg': 80.0,
            'height_cm': 160.0,
            'bmi': 80.0 / ((160.0 / 100) ** 2)  # 31.25
        }
        result = db_with_students.save_health_record(health3)
        assert result is True
        assert health3['bmi'] >= 25.0  # เกินเกณฑ์

        # 4. ตรวจสอบประวัติสุขภาพทั้งหมด
        health_records = db_with_students.get_health_records(student_id)
        assert len(health_records) == 3

        # เรียงลำดับจากใหม่ไปเก่า
        assert health_records[0]['weight_kg'] == 80.0  # ล่าสุด
        assert health_records[1]['weight_kg'] == 60.0
        assert health_records[2]['weight_kg'] == 40.0

        # 5. ดึงข้อมูลล่าสุด
        latest = db_with_students.get_latest_health(student_id)
        assert latest['weight_kg'] == 80.0
        assert latest['bmi'] >= 25.0


class TestGradeAutoCalculation:
    """Scenario 5: เกรด - Auto Calculation และ Transcript"""

    def test_grade_auto_calculation_transcript(self, db_with_students):
        """ทดสอบคำนวณเกรดอัตโนมัติและแสดง Transcript"""
        student_id = '65001'

        # 1. บันทึกคะแนนหลายวิชาและคำนวณเกรดอัตโนมัติ
        subjects = [
            ('TH101', 'ภาษาไทย', 85),      # 4.0
            ('MA101', 'คณิตศาสตร์', 77),   # 3.5
            ('EN101', 'ภาษาอังกฤษ', 72),   # 3.0
            ('SC101', 'วิทยาศาสตร์', 68),  # 2.5
            ('SO101', 'สังคมศึกษา', 62),   # 2.0
            ('PE101', 'พลศึกษา', 57),      # 1.5
            ('AR101', 'ศิลปะ', 52),        # 1.0
            ('MU101', 'ดนตรี', 45)         # 0.0
        ]

        for code, name, score in subjects:
            # คำนวณเกรดอัตโนมัติ
            grade = db_with_students.calculate_grade(score)

            grade_data = {
                'student_id': student_id,
                'academic_year': '2567',
                'semester': '1',
                'subject_code': code,
                'subject_name': name,
                'full_score': 100,
                'score': score,
                'grade': grade
            }

            result = db_with_students.save_grade(grade_data)
            assert result is True

        # 2. ตรวจสอบเกรดที่คำนวณได้ถูกต้อง
        grades = db_with_students.get_grades(student_id, academic_year='2567', semester='1')
        assert len(grades) == 8

        # ตรวจสอบเกรดแต่ละวิชา
        grade_map = {g['subject_code']: g['grade'] for g in grades}
        assert grade_map['TH101'] == '4.0'
        assert grade_map['MA101'] == '3.5'
        assert grade_map['EN101'] == '3.0'
        assert grade_map['SC101'] == '2.5'
        assert grade_map['SO101'] == '2.0'
        assert grade_map['PE101'] == '1.5'
        assert grade_map['AR101'] == '1.0'
        assert grade_map['MU101'] == '0.0'

        # 3. ดู Transcript
        transcript = db_with_students.get_transcript(student_id)
        assert len(transcript) == 8

        # Transcript ต้องเรียงตาม subject_code
        assert transcript[0]['subject_code'] == 'AR101'
        assert transcript[-1]['subject_code'] == 'TH101'

    def test_update_grade_recalculation(self, db_with_students):
        """ทดสอบแก้ไขคะแนนและคำนวณเกรดใหม่"""
        student_id = '65001'

        # บันทึกครั้งแรก
        grade_data = {
            'student_id': student_id,
            'academic_year': '2567',
            'semester': '1',
            'subject_code': 'TH101',
            'subject_name': 'ภาษาไทย',
            'full_score': 100,
            'score': 65,
            'grade': db_with_students.calculate_grade(65)
        }
        db_with_students.save_grade(grade_data)

        # ตรวจสอบเกรดแรก
        grades = db_with_students.get_grades(student_id)
        assert len(grades) == 1
        assert grades[0]['grade'] == '2.5'

        # แก้ไขคะแนนและคำนวณใหม่
        grade_data['score'] = 85
        grade_data['grade'] = db_with_students.calculate_grade(85)
        db_with_students.save_grade(grade_data)

        # ตรวจสอบเกรดใหม่
        grades = db_with_students.get_grades(student_id)
        assert len(grades) == 1  # ยังคงมีแค่ 1 รายการ
        assert grades[0]['score'] == 85
        assert grades[0]['grade'] == '4.0'


class TestScheduleConflictDetection:
    """Scenario 3: ตารางเรียน - ทดสอบความขัดแย้ง (สำคัญมาก)"""

    def test_schedule_conflict_complete_scenario(self, db_with_teachers):
        """ทดสอบสถานการณ์ความขัดแย้งตารางเรียนแบบครบวงจร"""
        # 1. เพิ่มครู 2 คน (T001, T002 มีอยู่แล้วจาก fixture)

        # 2. จัดตารางปกติ (ไม่ซ้ำ) → ต้อง OK
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
        result = db_with_teachers.add_schedule(schedule1)
        assert result is True

        schedule2 = {
            'class_room': 'ป.2/1',
            'day_of_week': 'จันทร์',
            'period_no': 1,
            'start_time': '08:00',
            'end_time': '09:00',
            'subject_name': 'วิทยาศาสตร์',
            'teacher_id': 'T002',  # ครูคนอื่น
            'room_no': '201'
        }
        result = db_with_teachers.add_schedule(schedule2)
        assert result is True

        # 3. พยายามจัดครูคนเดียวสอน 2 ห้องพร้อมกัน → ต้อง REJECT + แสดง popup
        schedule_conflict = {
            'class_room': 'ป.3/1',
            'day_of_week': 'จันทร์',  # วันเดียวกัน
            'period_no': 1,           # คาบเดียวกัน
            'start_time': '08:00',
            'end_time': '09:00',
            'subject_name': 'ภาษาไทย',
            'teacher_id': 'T001',     # ครูคนเดียวกัน
            'room_no': '301'
        }
        result = db_with_teachers.add_schedule(schedule_conflict)

        # ต้องถูก REJECT
        assert result is not True
        assert isinstance(result, str)
        assert 'มีคาบสอนอยู่แล้ว' in result
        assert 'นายสมศักดิ์ สอนดี' in result
        assert 'จันทร์' in result
        assert 'คาบที่ 1' in result
        assert 'ป.1/1' in result  # ห้องเดิม

        # 4. ตรวจสอบว่าข้อมูลไม่ถูกบันทึก
        schedules = db_with_teachers.get_all_schedules()
        assert len(schedules) == 2  # มีเฉพาะ 2 ตารางแรก

        # 5. ทดสอบว่าครูสามารถสอนคาบอื่นได้ (ไม่ซ้ำ)
        schedule_ok = {
            'class_room': 'ป.3/1',
            'day_of_week': 'จันทร์',
            'period_no': 2,        # คาบต่างกัน
            'start_time': '09:00',
            'end_time': '10:00',
            'subject_name': 'ภาษาไทย',
            'teacher_id': 'T001',
            'room_no': '301'
        }
        result = db_with_teachers.add_schedule(schedule_ok)
        assert result is True

        schedules = db_with_teachers.get_all_schedules()
        assert len(schedules) == 3

    def test_teacher_workload_calculation(self, db_with_teachers):
        """ทดสอบคำนวณภาระงานครูหลังจัดตาราง"""
        # ครู T001 สอน 10 คาบ
        days = ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์']
        for i, day in enumerate(days):
            for period in range(1, 3):  # 2 คาบต่อวัน
                schedule = {
                    'class_room': 'ป.1/1',
                    'day_of_week': day,
                    'period_no': period,
                    'start_time': f'{7+period}:00',
                    'end_time': f'{8+period}:00',
                    'subject_name': f'วิชา{period}',
                    'teacher_id': 'T001',
                    'room_no': '101'
                }
                db_with_teachers.add_schedule(schedule)

        # ครู T002 สอน 5 คาบ
        for period in range(1, 6):
            schedule = {
                'class_room': 'ป.2/1',
                'day_of_week': 'จันทร์',
                'period_no': period,
                'start_time': f'{7+period}:00',
                'end_time': f'{8+period}:00',
                'subject_name': f'วิชา{period}',
                'teacher_id': 'T002',
                'room_no': '201'
            }
            db_with_teachers.add_schedule(schedule)

        # คำนวณภาระงาน
        workload = db_with_teachers.get_teacher_workload()

        # T001 ต้องมี 10 คาบ
        t001 = next(w for w in workload if w['teacher_id'] == 'T001')
        assert t001['periods_per_week'] == 10

        # T002 ต้องมี 5 คาบ
        t002 = next(w for w in workload if w['teacher_id'] == 'T002')
        assert t002['periods_per_week'] == 5

        # T003 ไม่สอน ต้องมี 0 คาบ
        t003 = next(w for w in workload if w['teacher_id'] == 'T003')
        assert t003['periods_per_week'] == 0


class TestMultiModuleIntegration:
    """ทดสอบการทำงานร่วมกันของหลายโมดูล"""

    def test_student_lifecycle(self, test_db):
        """ทดสอบวงจรชีวิตนักเรียนตั้งแต่เพิ่ม-ลบ พร้อมข้อมูลที่เกี่ยวข้อง"""
        today = datetime.now().strftime('%Y-%m-%d')

        # 1. เพิ่มนักเรียน
        student_data = {
            'student_id': '67001',
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
        test_db.add_student(student_data)

        # 2. บันทึกการเช็คชื่อ
        test_db.save_attendance('67001', today, 'มา')

        # 3. บันทึกสุขภาพ
        health_data = {
            'student_id': '67001',
            'record_date': today,
            'brushed_teeth': 1,
            'drank_milk': 1,
            'weight_kg': 40.0,
            'height_cm': 150.0,
            'bmi': 17.78
        }
        test_db.save_health_record(health_data)

        # 4. บันทึกเกรด
        grade_data = {
            'student_id': '67001',
            'academic_year': '2567',
            'semester': '1',
            'subject_code': 'TH101',
            'subject_name': 'ภาษาไทย',
            'full_score': 100,
            'score': 85,
            'grade': '4.0'
        }
        test_db.save_grade(grade_data)

        # 5. ตรวจสอบว่าข้อมูลทั้งหมดถูกบันทึก
        student = test_db.get_student_by_id('67001')
        assert student is not None

        attendance = test_db.get_attendance_by_student('67001')
        assert len(attendance) == 1

        health = test_db.get_health_records('67001')
        assert len(health) == 1

        grades = test_db.get_grades('67001')
        assert len(grades) == 1

        # 6. ลบนักเรียน (soft delete)
        test_db.delete_student('67001')

        # 7. ตรวจสอบว่านักเรียนถูก soft delete
        student = test_db.get_student_by_id('67001')
        assert student['is_active'] == 0

        # 8. ข้อมูลที่เกี่ยวข้องยังคงอยู่ (ไม่ถูกลบ)
        attendance = test_db.get_attendance_by_student('67001')
        assert len(attendance) == 1

        health = test_db.get_health_records('67001')
        assert len(health) == 1

        grades = test_db.get_grades('67001')
        assert len(grades) == 1

    def test_class_room_filter_across_modules(self, db_with_students):
        """ทดสอบการกรองตามห้องเรียนในทุกโมดูล"""
        today = datetime.now().strftime('%Y-%m-%d')

        # บันทึกข้อมูลหลายโมดูล
        students = db_with_students.get_all_students()
        for student in students:
            # เช็คชื่อ
            db_with_students.save_attendance(student['student_id'], today, 'มา')

            # สุขภาพ
            health_data = {
                'student_id': student['student_id'],
                'record_date': today,
                'brushed_teeth': 1,
                'drank_milk': 1,
                'weight_kg': 40.0,
                'height_cm': 150.0,
                'bmi': 17.78
            }
            db_with_students.save_health_record(health_data)

        # กรองตามห้อง ป.1/1
        students_p11 = db_with_students.get_all_students(class_room='ป.1/1')
        attendance_p11 = db_with_students.get_attendance_by_date(today, class_room='ป.1/1')
        health_p11 = db_with_students.get_health_by_date(today, class_room='ป.1/1')

        # ต้องได้จำนวนเท่ากัน
        assert len(students_p11) == 2
        assert len(attendance_p11) == 2
        assert len(health_p11) == 2

        # กรองตามห้อง ป.2/1
        students_p21 = db_with_students.get_all_students(class_room='ป.2/1')
        attendance_p21 = db_with_students.get_attendance_by_date(today, class_room='ป.2/1')
        health_p21 = db_with_students.get_health_by_date(today, class_room='ป.2/1')

        assert len(students_p21) == 2
        assert len(attendance_p21) == 2
        assert len(health_p21) == 2
