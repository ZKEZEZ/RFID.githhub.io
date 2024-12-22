from flask import Flask, render_template, jsonify, request
import datetime
import requests
import sqlite3
from threading import Lock
import sys

# กำหนด encoding เป็น UTF-8
import locale
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer)

app = Flask(__name__)
db_lock = Lock()

# Line Notify configuration
LINE_NOTIFY_TOKEN = 'pbMYCHb3xMqzAGdumhEsQQj4VvaT4KW9sVJ9cWk7vaf'
LINE_NOTIFY_API = 'https://notify-api.line.me/api/notify'

def init_db():
    with sqlite3.connect('rfid_system.db') as conn:
        conn.text_factory = str  # รองรับ UTF-8
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
        try:
            cursor.execute('INSERT OR IGNORE INTO students (rfid_id, name, status) VALUES (?, ?, ?)',
                         ('1234567890', 'นายณัฐรัตน์ สำเภา', 'active'))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error adding sample data: {str(e)}")

def send_line_notification(message):
    try:
        headers = {
            'Authorization': f'Bearer {LINE_NOTIFY_TOKEN}'
        }
        payload = {
            'message': message.encode('utf-8').decode('utf-8')
        }
        response = requests.post(LINE_NOTIFY_API, headers=headers, data=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Line Notification Error: {str(e)}")
        return False

def get_student_by_rfid(rfid_id):
    try:
        with sqlite3.connect('rfid_system.db') as conn:
            conn.text_factory = str  # รองรับ UTF-8
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students WHERE rfid_id = ?', (rfid_id,))
            return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Database Error: {str(e)}")
        return None

def log_scan(rfid_id, action, status):
    try:
        with db_lock:
            with sqlite3.connect('rfid_system.db') as conn:
                conn.text_factory = str  # รองรับ UTF-8
                cursor = conn.cursor()
                timestamp = datetime.datetime.now()
                cursor.execute('''
                    INSERT INTO scan_logs (rfid_id, timestamp, action, status)
                    VALUES (?, ?, ?, ?)
                ''', (rfid_id, timestamp, action.encode('utf-8').decode('utf-8'), 
                     status.encode('utf-8').decode('utf-8')))
                conn.commit()
        return True
    except Exception as e:
        print(f"Log Scan Error: {str(e)}")
        return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan_card():
    try:
        rfid_id = request.json.get('rfid_id')
        if not rfid_id:
            return jsonify({'status': 'error', 'message': 'กรุณาสแกนบัตร'})

        student = get_student_by_rfid(rfid_id)
        if not student:
            return jsonify({'status': 'error', 'message': 'ไม่พบข้อมูลบัตรในระบบ'})

        current_time = datetime.datetime.now()
        thai_year = current_time.year + 543
        formatted_time = current_time.strftime(f'%d ธันวาคม {thai_year} %H:%M:%S')

        # สร้างข้อความแจ้งเตือน
        message = (
            f'\nระบบสแกนบัตร PCSHSL: เช็คการสแกนบัตร\n'
            f'{student[2]}\n'
            f'ออกจากหอพักเข้าโรงเรียน : {formatted_time}\n'
            f'สถานะ : ออกจากหอพักไปโรงเรียน'
        )

        # ส่งการแจ้งเตือนไปยัง Line
        line_sent = send_line_notification(message)
        
        # บันทึกลงฐานข้อมูล
        log_success = log_scan(rfid_id, 'ออกจากหอพัก', 'ไปโรงเรียน')

        response_data = {
            'status': 'success' if line_sent else 'warning',
            'message': 'บันทึกการสแกนเรียบร้อย' if line_sent else 'บันทึกการสแกนแล้ว แต่ไม่สามารถส่งไลน์ได้',
            'student': student[2],
            'timestamp': formatted_time
        }

        return jsonify(response_data)

    except Exception as e:
        print(f"Scan Error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'เกิดข้อผิดพลาดในระบบ กรุณาลองใหม่อีกครั้ง'
        })

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)