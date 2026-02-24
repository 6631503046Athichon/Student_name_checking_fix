"""
conftest.py
Pytest fixtures สำหรับการทดสอบ
"""

import pytest
import os
import sqlite3
from datetime import datetime, timedelta
import sys

# เพิ่ม path ให้สามารถ import โปรเจคได้
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db import Database


@pytest.fixture
def test_db():
    """
    สร้างฐานข้อมูลชั่วคราวสำหรับทดสอบ
    จะถูกลบทิ้งหลังการทดสอบเสร็จ
    """
    db_path = "test_school.db"

    # ลบ DB เก่าถ้ามี
    if os.path.exists(db_path):
        os.remove(db_path)

    # สร้าง DB ใหม่
    db = Database(db_path)

    yield db

    # ปิดและลบ DB หลังใช้งาน
    db.close()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def db_with_students(test_db):
    """ฐานข้อมูลที่มีนักเรียนตัวอย่างแล้ว"""
    students = [
        {
            'student_id': '65001',
            'title': 'เด็กชาย',
            'first_name': 'สมชาย',
            'last_name': 'ใจดี',
            'class_room': 'ป.1/1',
            'class_year': '2567',
            'birth_date': '2016-01-15',
            'parent_name': 'นายสมศักดิ์ ใจดี',
            'parent_phone': '0812345678',
            'photo_path': None
        },
        {
            'student_id': '65002',
            'title': 'เด็กหญิง',
            'first_name': 'สมหญิง',
            'last_name': 'รักเรียน',
            'class_room': 'ป.1/1',
            'class_year': '2567',
            'birth_date': '2016-02-20',
            'parent_name': 'นางสมใจ รักเรียน',
            'parent_phone': '0823456789',
            'photo_path': None
        },
        {
            'student_id': '65003',
            'title': 'เด็กชาย',
            'first_name': 'ธนา',
            'last_name': 'มีปัญญา',
            'class_room': 'ป.2/1',
            'class_year': '2567',
            'birth_date': '2015-05-10',
            'parent_name': 'นายธนากร มีปัญญา',
            'parent_phone': '0834567890',
            'photo_path': None
        },
        {
            'student_id': '65004',
            'title': 'เด็กหญิง',
            'first_name': 'วิภา',
            'last_name': 'ฉลาด',
            'class_room': 'ป.2/1',
            'class_year': '2567',
            'birth_date': '2015-08-25',
            'parent_name': 'นางวิมล ฉลาด',
            'parent_phone': '0845678901',
            'photo_path': None
        },
        {
            'student_id': '65005',
            'title': 'เด็กชาย',
            'first_name': 'ชัยวัฒน์',
            'last_name': 'เก่งกาจ',
            'class_room': 'ป.3/1',
            'class_year': '2567',
            'birth_date': '2014-12-05',
            'parent_name': 'นายชัยยุทธ เก่งกาจ',
            'parent_phone': '0856789012',
            'photo_path': None
        }
    ]

    for student in students:
        test_db.add_student(student)

    return test_db


@pytest.fixture
def db_with_teachers(test_db):
    """ฐานข้อมูลที่มีครูตัวอย่างแล้ว"""
    teachers = [
        {
            'teacher_id': 'T001',
            'title': 'นาย',
            'first_name': 'สมศักดิ์',
            'last_name': 'สอนดี',
            'phone': '0891234567'
        },
        {
            'teacher_id': 'T002',
            'title': 'นาง',
            'first_name': 'สมหญิง',
            'last_name': 'รักสอน',
            'phone': '0892345678'
        },
        {
            'teacher_id': 'T003',
            'title': 'นางสาว',
            'first_name': 'วิภา',
            'last_name': 'ใจเย็น',
            'phone': '0893456789'
        }
    ]

    for teacher in teachers:
        test_db.add_teacher(teacher)

    return test_db


@pytest.fixture
def sample_date():
    """วันที่สำหรับทดสอบ"""
    return datetime.now().strftime('%Y-%m-%d')


@pytest.fixture
def date_range():
    """ช่วงวันที่สำหรับทดสอบ"""
    today = datetime.now()
    return {
        'start': (today - timedelta(days=30)).strftime('%Y-%m-%d'),
        'end': today.strftime('%Y-%m-%d')
    }
