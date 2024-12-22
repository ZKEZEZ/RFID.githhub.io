# student_manager.py
import sqlite3

def add_student(rfid_id, name, status='active'):
    """เพิ่มข้อมูลนักเรียนใหม่"""
    with sqlite3.connect('rfid_system.db') as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO students (rfid_id, name, status)
                VALUES (?, ?, ?)
            ''', (rfid_id, name, status))
            conn.commit()
            print(f"เพิ่มข้อมูลนักเรียน {name} เรียบร้อยแล้ว")
        except sqlite3.IntegrityError:
            print(f"รหัสบัตร {rfid_id} มีอยู่ในระบบแล้ว")

def list_students():
    """แสดงรายชื่อนักเรียนทั้งหมด"""
    with sqlite3.connect('rfid_system.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students')
        students = cursor.fetchall()
        print("\nรายชื่อนักเรียนทั้งหมด:")
        for student in students:
            print(f"RFID: {student[1]}, ชื่อ: {student[2]}, สถานะ: {student[3]}")

def delete_student(rfid_id):
    """ลบข้อมูลนักเรียน"""
    with sqlite3.connect('rfid_system.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM students WHERE rfid_id = ?', (rfid_id,))
        if cursor.rowcount > 0:
            print(f"ลบข้อมูลนักเรียนที่มีรหัสบัตร {rfid_id} เรียบร้อยแล้ว")
        else:
            print(f"ไม่พบข้อมูลนักเรียนที่มีรหัสบัตร {rfid_id}")
        conn.commit()

if __name__ == '__main__':
    while True:
        print("\n=== ระบบจัดการข้อมูลนักเรียน ===")
        print("1. เพิ่มนักเรียน")
        print("2. แสดงรายชื่อนักเรียน")
        print("3. ลบข้อมูลนักเรียน")
        print("4. ออกจากโปรแกรม")
        
        choice = input("\nเลือกเมนู (1-4): ")
        
        if choice == '1':
            rfid = input("ใส่รหัสบัตร RFID: ")
            name = input("ใส่ชื่อ-นามสกุล: ")
            add_student(rfid, name)
        elif choice == '2':
            list_students()
        elif choice == '3':
            rfid = input("ใส่รหัสบัตร RFID ที่ต้องการลบ: ")
            delete_student(rfid)
        elif choice == '4':
            print("ออกจากโปรแกรม")
            break
        else:
            print("กรุณาเลือกเมนู 1-4 เท่านั้น")