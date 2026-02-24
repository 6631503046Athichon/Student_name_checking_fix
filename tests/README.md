# Test Suite - Student Management System

ชุดทดสอบอัตโนมัติสำหรับระบบบริหารจัดการโรงเรียน

## โครงสร้างไฟล์ทดสอบ

```
tests/
├── __init__.py              # Package marker
├── conftest.py              # Pytest fixtures ที่ใช้ร่วมกัน
├── test_db.py               # ทดสอบ Database CRUD operations
├── test_integration.py      # ทดสอบการทำงานร่วมกันของหลายโมดูล
├── test_edge_cases.py       # ทดสอบกรณีพิเศษและ error handling
├── test_utils.py            # ทดสอบ utilities และ calculations
├── sample_data/             # ข้อมูลตัวอย่างสำหรับทดสอบ
│   ├── create_sample_excel.py
│   ├── students.xlsx
│   ├── teachers.xlsx
│   └── students_invalid.xlsx
└── README.md                # เอกสารนี้
```

## การติดตั้ง

```bash
# ติดตั้ง dependencies
pip install -r requirements.txt
```

## วิธีรันทดสอบ

### รันทดสอบทั้งหมด
```bash
pytest tests/ -v
```

### รันเฉพาะไฟล์ทดสอบ
```bash
pytest tests/test_db.py -v
pytest tests/test_integration.py -v
pytest tests/test_edge_cases.py -v
pytest tests/test_utils.py -v
```

### รันเฉพาะคลาสทดสอบ
```bash
pytest tests/test_db.py::TestStudents -v
pytest tests/test_db.py::TestSchedule -v
```

### รันเฉพาะฟังก์ชันทดสอบ
```bash
pytest tests/test_db.py::TestSchedule::test_add_schedule_teacher_conflict -v
```

### รันพร้อมแสดง coverage
```bash
pytest tests/ -v --cov=database --cov=modules --cov-report=html
```

### รันแบบ verbose พร้อมแสดงรายละเอียด
```bash
pytest tests/ -vv -s
```

## Coverage รายละเอียด

ชุดทดสอบนี้ครอบคลุม:

### 1. Database Operations (test_db.py)
- ✓ Students CRUD (เพิ่ม/แก้ไข/ลบ/ค้นหา)
- ✓ Attendance (บันทึก/ดึงข้อมูล/สถิติ)
- ✓ Health Records (BMI calculation, แปรงฟัน/ดื่มนม)
- ✓ Grades (คำนวณเกรด, Transcript)
- ✓ Teachers CRUD
- ✓ Schedule (ตรวจจับความขัดแย้งครู)

### 2. Integration Tests (test_integration.py)
- ✓ Student → Attendance → Stats workflow
- ✓ BMI tracking across time
- ✓ Grade auto-calculation
- ✓ Schedule conflict detection
- ✓ Teacher workload calculation
- ✓ Multi-module data filtering

### 3. Edge Cases (test_edge_cases.py)
- ✓ Empty/null fields
- ✓ Special characters
- ✓ SQL injection prevention
- ✓ Invalid data handling
- ✓ Boundary values
- ✓ Database constraints

### 4. Utilities (test_utils.py)
- ✓ BMI calculation precision
- ✓ Grade boundary values
- ✓ Data uniqueness validation
- ✓ Sorting and ordering
- ✓ Day of week ordering

## ฟีเจอร์สำคัญที่ทดสอบ

### 🎯 Teacher Conflict Detection (ความขัดแย้งครู)
ระบบตรวจจับครูสอนซ้ำในเวลาเดียวกัน:
- UNIQUE constraint: (teacher_id + day_of_week + period_no)
- แสดงข้อความเตือน: "ครู [ชื่อ] มีคาบสอนอยู่แล้วในวัน [วัน] คาบที่ [N] ที่ห้อง [ห้องเดิม]"

### 📊 BMI Calculation
- ต่ำกว่าเกณฑ์: BMI < 18.5
- ปกติ: 18.5 ≤ BMI < 25.0
- เกินเกณฑ์: BMI ≥ 25.0

### 📝 Grade Calculation
- 80+ → 4.0
- 75+ → 3.5
- 70+ → 3.0
- 65+ → 2.5
- 60+ → 2.0
- 55+ → 1.5
- 50+ → 1.0
- <50 → 0.0

## Test Fixtures

### test_db
ฐานข้อมูล SQLite ชั่วคราว (ถูกลบหลังทดสอบเสร็จ)

### db_with_students
ฐานข้อมูลพร้อมนักเรียน 5 คน (ป.1/1, ป.2/1, ป.3/1)

### db_with_teachers
ฐานข้อมูลพร้อมครู 3 คน (T001, T002, T003)

### sample_date
วันที่ปัจจุบันสำหรับทดสอบ

### date_range
ช่วงวันที่ 30 วันย้อนหลัง

## ตัวอย่างผลลัพธ์

```
tests/test_db.py::TestStudents::test_add_student_success PASSED                    [ 1%]
tests/test_db.py::TestSchedule::test_add_schedule_teacher_conflict PASSED          [ 2%]
tests/test_integration.py::TestScheduleConflictDetection PASSED                    [ 3%]
...

======================== 120 passed in 5.23s ========================
```

## หมายเหตุ

- ทดสอบทั้งหมดใช้ฐานข้อมูล SQLite ชั่วคราว
- ไม่มีผลกระทบต่อฐานข้อมูลจริง
- Fixtures ถูก cleanup อัตโนมัติหลังการทดสอบ
- รองรับการ run แบบ parallel ด้วย pytest-xdist

## การเพิ่มทดสอบใหม่

1. สร้างฟังก์ชันที่ขึ้นต้นด้วย `test_`
2. ใช้ fixtures จาก conftest.py
3. ใช้ assert เพื่อตรวจสอบผลลัพธ์
4. เพิ่ม docstring อธิบายว่าทดสอบอะไร

```python
def test_my_new_feature(db_with_students):
    """ทดสอบฟีเจอร์ใหม่"""
    result = db_with_students.my_function()
    assert result is True
```

## Troubleshooting

### ถ้าทดสอบล้มเหลว
1. ตรวจสอบข้อความ error
2. รัน pytest ด้วย `-vv -s` เพื่อดูรายละเอียด
3. ตรวจสอบฐานข้อมูลชั่วคราว
4. ตรวจสอบ fixtures

### ถ้าต้องการ debug
```bash
pytest tests/test_db.py::TestStudents::test_add_student_success -vv -s --pdb
```
