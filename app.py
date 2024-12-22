from flask import Flask, render_template, jsonify, request
import datetime
import requests
import sqlite3
from threading import Lock

app = Flask(__name__)
db_lock = Lock()

# Line Notify configuration
LINE_NOTIFY_TOKEN = 'Kzibk3dddtNx8U5fMGUeU506a1HrfuCk0u2O75NZj3s'
LINE_NOTIFY_API = 'https://notify-api.line.me/api/notify'

def init_db():
    with sqlite3.connect('rfid_system.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                rfid_id TEXT UNIQUE,
                name TEXT,
                status TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_logs (
                id INTEGER PRIMARY KEY,
                rfid_id TEXT,
                timestamp DATETIME,
                action TEXT,
                status TEXT
            )
        ''')

def send_line_notification(message):
    headers = {
        'Authorization': f'Bearer {LINE_NOTIFY_TOKEN}'
    }
    payload = {
        'message': message
    }
    requests.post(LINE_NOTIFY_API, headers=headers, data=payload)

def get_student_by_rfid(rfid_id):
    with sqlite3.connect('rfid_system.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students WHERE rfid_id = ?', (rfid_id,))
        return cursor.fetchone()

def log_scan(rfid_id, action, status):
    with db_lock:
        with sqlite3.connect('rfid_system.db') as conn:
            cursor = conn.cursor()
            timestamp = datetime.datetime.now()
            cursor.execute('''
                INSERT INTO scan_logs (rfid_id, timestamp, action, status)
                VALUES (?, ?, ?, ?)
            ''', (rfid_id, timestamp, action, status))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan_card():
    rfid_id = request.json.get('rfid_id')
    student = get_student_by_rfid(rfid_id)
    
    if not student:
        return jsonify({'status': 'error', 'message': 'บัตรไม่ถูกต้อง'})
    
    current_time = datetime.datetime.now()
    thai_year = current_time.year + 543
    formatted_time = current_time.strftime(f'%d ธันวาคม {thai_year} %H:%M:%S')
    
    # สร้างข้อความแจ้งเตือน
    message = (
        f'\nระบบสแกนบัตร PCSHSL: เช็คการสแกนบัตร\n'
        f'{student[2]}\n'  # student name
        f'ออกจากหอพักเข้าโรงเรียน : {formatted_time}\n'
        f'สถานะ : ออกจากหอพักไปโรงเรียน'
    )
    
    # ส่งการแจ้งเตือนไปยัง Line
    send_line_notification(message)
    
    # บันทึกลงฐานข้อมูล
    log_scan(rfid_id, 'ออกจากหอพัก', 'ไปโรงเรียน')
    
    return jsonify({
        'status': 'success',
        'message': 'บันทึกการสแกนเรียบร้อย',
        'student': student[2],
        'timestamp': formatted_time
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)