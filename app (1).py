from flask import Flask, request, jsonify, render_template_string
import time
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ================= DATABASE SETUP =================
def init_db():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  roll TEXT NOT NULL,
                  time TEXT NOT NULL,
                  date TEXT NOT NULL,
                  status TEXT DEFAULT 'Present')''')
    conn.commit()
    conn.close()
    print("✅ Database initialized!")

init_db()

# Global variables
active_qr = ""
active_qr_time = None
QR_VALID_SECONDS = 60  # 1 minute only

# ================= HTML WITH COMPREHENSIVE INTERNAL CSS =================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QROLL - Smart QR Attendance System</title>
    <style>
        /* CSS Reset */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        /* Root Variables for Easy Theming */
        :root {
            --primary-color: #667eea;
            --primary-dark: #5a67d8;
            --secondary-color: #764ba2;
            --success-color: #48bb78;
            --success-light: #c6f6d5;
            --success-dark: #22543d;
            --error-color: #f56565;
            --error-light: #fed7d7;
            --error-dark: #742a2a;
            --warning-color: #ecc94b;
            --text-primary: #333;
            --text-secondary: #666;
            --text-light: #888;
            --white: #ffffff;
            --gray-light: #f8f9fa;
            --gray-border: #e0e0e0;
            --shadow-sm: 0 4px 6px rgba(0,0,0,0.1);
            --shadow-md: 0 6px 12px rgba(0,0,0,0.15);
            --shadow-lg: 0 10px 30px rgba(0,0,0,0.15);
            --border-radius-sm: 8px;
            --border-radius-md: 10px;
            --border-radius-lg: 15px;
            --border-radius-xl: 20px;
            --border-radius-full: 50px;
        }

        /* Base Styles */
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            min-height: 100vh;
            padding: 20px;
            line-height: 1.6;
        }

        /* Container */
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }

        /* Header Styles */
        .header {
            text-align: center;
            color: var(--white);
            margin-bottom: 30px;
            animation: fadeInDown 0.8s ease;
        }

        .header h1 {
            font-size: 48px;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            letter-spacing: -0.5px;
        }

        .header p {
            font-size: 18px;
            opacity: 0.95;
            font-weight: 300;
        }

        /* Navigation Buttons */
        .nav-buttons {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 30px;
            animation: fadeInUp 0.8s ease;
        }

        .nav-btn {
            padding: 12px 40px;
            font-size: 16px;
            font-weight: 600;
            border: none;
            border-radius: var(--border-radius-full);
            cursor: pointer;
            transition: all 0.3s ease;
            background: var(--white);
            color: var(--primary-color);
            box-shadow: var(--shadow-sm);
            position: relative;
            overflow: hidden;
        }

        .nav-btn:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        .nav-btn:active {
            transform: translateY(0);
        }

        .nav-btn.active {
            background: var(--primary-color);
            color: var(--white);
        }

        .nav-btn i {
            margin-right: 8px;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
            animation: fadeInUp 0.8s ease 0.2s both;
        }

        .stat-card {
            background: var(--white);
            padding: 25px;
            border-radius: var(--border-radius-lg);
            text-align: center;
            box-shadow: var(--shadow-sm);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }

        .stat-card i {
            color: var(--primary-color);
            margin-bottom: 15px;
        }

        .stat-value {
            font-size: 42px;
            font-weight: 700;
            color: var(--primary-color);
            margin: 10px 0;
            line-height: 1.2;
        }

        .stat-label {
            font-size: 14px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 500;
        }

        /* Main Cards */
        .main-card {
            background: var(--white);
            border-radius: var(--border-radius-xl);
            padding: 30px;
            box-shadow: var(--shadow-lg);
            margin-bottom: 30px;
            animation: fadeInUp 0.8s ease 0.4s both;
        }

        .card-title {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 25px;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
            padding-bottom: 15px;
            border-bottom: 2px solid var(--gray-border);
        }

        .card-title i {
            color: var(--primary-color);
            font-size: 28px;
        }

        /* Form Elements */
        .input-group {
            margin-bottom: 20px;
            position: relative;
        }

        .password-wrapper {
            position: relative;
            width: 100%;
        }

        .password-wrapper input {
            width: 100%;
            padding: 15px 45px 15px 15px;
            font-size: 16px;
            border: 2px solid var(--gray-border);
            border-radius: var(--border-radius-md);
            transition: all 0.3s ease;
            font-family: inherit;
        }

        .password-wrapper input:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .toggle-password {
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            cursor: pointer;
            color: var(--text-secondary);
            font-size: 18px;
            transition: color 0.3s ease;
        }

        .toggle-password:hover {
            color: var(--primary-color);
        }

        input {
            width: 100%;
            padding: 15px;
            font-size: 16px;
            border: 2px solid var(--gray-border);
            border-radius: var(--border-radius-md);
            transition: all 0.3s ease;
            font-family: inherit;
        }

        input:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        input::placeholder {
            color: var(--text-light);
            opacity: 0.7;
        }

        /* Buttons */
        .btn {
            width: 100%;
            padding: 15px;
            font-size: 16px;
            font-weight: 600;
            border: none;
            border-radius: var(--border-radius-md);
            cursor: pointer;
            transition: all 0.3s ease;
            background: var(--primary-color);
            color: var(--white);
            position: relative;
            overflow: hidden;
        }

        .btn:hover {
            background: var(--primary-dark);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .btn i {
            margin-right: 8px;
        }

        /* QR Display */
        .qr-display {
            background: var(--gray-light);
            padding: 25px;
            border-radius: var(--border-radius-lg);
            text-align: center;
            margin: 20px 0;
            border: 2px dashed var(--primary-color);
            animation: pulse 2s infinite;
        }

        .qr-code {
            font-family: 'Courier New', monospace;
            font-size: 18px;
            color: var(--primary-color);
            background: var(--white);
            padding: 15px;
            border-radius: var(--border-radius-sm);
            margin: 15px 0;
            word-break: break-all;
            border: 1px solid var(--gray-border);
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
        }

        .timer {
            font-size: 14px;
            color: var(--error-color);
            font-weight: 600;
            padding: 8px;
            background: var(--error-light);
            border-radius: var(--border-radius-full);
            display: inline-block;
            margin-top: 10px;
        }

        /* Table Styles */
        .table-container {
            overflow-x: auto;
            margin-top: 20px;
            border-radius: var(--border-radius-md);
            border: 1px solid var(--gray-border);
            background: var(--white);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            min-width: 600px;
        }

        th {
            background: var(--gray-light);
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: var(--text-secondary);
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid var(--gray-border);
        }

        td {
            padding: 12px 15px;
            border-bottom: 1px solid var(--gray-border);
            color: var(--text-secondary);
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:hover {
            background: var(--gray-light);
        }

        /* Badge */
        .badge {
            padding: 5px 12px;
            border-radius: var(--border-radius-full);
            font-size: 12px;
            font-weight: 600;
            background: var(--success-light);
            color: var(--success-dark);
            display: inline-block;
        }

        /* Message Styles */
        .message {
            padding: 15px;
            border-radius: var(--border-radius-md);
            margin: 20px 0 0;
            display: none;
            font-weight: 500;
            animation: slideIn 0.3s ease;
        }

        .message.success {
            background: var(--success-light);
            color: var(--success-dark);
            display: block;
            border-left: 4px solid var(--success-color);
        }

        .message.error {
            background: var(--error-light);
            color: var(--error-dark);
            display: block;
            border-left: 4px solid var(--error-color);
        }

        /* Loading Spinner */
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: var(--white);
            animation: spin 1s linear infinite;
            margin-right: 8px;
        }

        /* Animations */
        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        @keyframes pulse {
            0% {
                box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.4);
            }
            70% {
                box-shadow: 0 0 0 10px rgba(102, 126, 234, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(102, 126, 234, 0);
            }
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: 1fr;
                gap: 15px;
            }
            
            .nav-buttons {
                flex-direction: column;
                gap: 10px;
            }
            
            .header h1 {
                font-size: 36px;
            }
            
            .header p {
                font-size: 16px;
            }
            
            .main-card {
                padding: 20px;
            }
            
            .card-title {
                font-size: 20px;
            }
            
            .stat-value {
                font-size: 32px;
            }
        }

        @media (max-width: 480px) {
            body {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 28px;
            }
            
            .nav-btn {
                padding: 10px 20px;
                font-size: 14px;
            }
            
            .btn {
                padding: 12px;
                font-size: 14px;
            }
            
            input {
                padding: 12px;
                font-size: 14px;
            }
        }

        /* Print Styles */
        @media print {
            body {
                background: var(--white);
                padding: 0;
            }
            
            .nav-buttons,
            .btn,
            .input-group {
                display: none;
            }
            
            .main-card {
                box-shadow: none;
                padding: 0;
            }
            
            table {
                border: 1px solid #000;
            }
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }

        ::-webkit-scrollbar-track {
            background: var(--gray-light);
            border-radius: 5px;
        }

        ::-webkit-scrollbar-thumb {
            background: var(--primary-color);
            border-radius: 5px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary-dark);
        }

        /* Focus Styles for Accessibility */
        *:focus {
            outline: 2px solid var(--primary-color);
            outline-offset: 2px;
        }

        /* Loading State */
        .loading {
            position: relative;
            pointer-events: none;
            opacity: 0.7;
        }

        .loading::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 30px;
            height: 30px;
            border: 3px solid var(--gray-border);
            border-top-color: var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            transform: translate(-50%, -50%);
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <!-- Your existing HTML content remains exactly the same -->
    <div class="container">
        <div class="header">
            <h1>📱 QROLL</h1>
            <p>Smart QR Attendance System</p>
        </div>

        <div class="nav-buttons">
            <button class="nav-btn active" onclick="showSection('teacher')" id="teacherBtn">
                <i class="fas fa-chalkboard-teacher"></i> Teacher Dashboard
            </button>
            <button class="nav-btn" onclick="showSection('student')" id="studentBtn">
                <i class="fas fa-user-graduate"></i> Student Portal
            </button>
        </div>

        <div class="stats-grid" id="statsSection">
            <div class="stat-card">
                <i class="fas fa-users fa-2x"></i>
                <div class="stat-value" id="totalCount">0</div>
                <div class="stat-label">Total Present</div>
            </div>
            <div class="stat-card">
                <i class="fas fa-calendar-check fa-2x"></i>
                <div class="stat-value" id="todayCount">0</div>
                <div class="stat-label">Today's Attendance</div>
            </div>
            <div class="stat-card">
                <i class="fas fa-chart-line fa-2x"></i>
                <div class="stat-value" id="rateCount">0%</div>
                <div class="stat-label">Attendance Rate</div>
            </div>
        </div>

        <div id="teacherSection" class="main-card">
            <div class="card-title">
                <i class="fas fa-chalkboard-teacher"></i>
                Teacher Dashboard
            </div>
            
            <div class="input-group">
                <div class="password-wrapper">
                    <input type="password" id="password" placeholder="Enter admin password">
                    <i class="fas fa-eye toggle-password" onclick="togglePassword()"></i>
                </div>
            </div>
            
            <button class="btn" onclick="generateQR()" id="generateBtn">
                <i class="fas fa-qrcode"></i> Generate QR Code (1 min valid)
            </button>
            
            <div id="qrDisplay" style="display: none;">
                <div class="qr-display">
                    <i class="fas fa-qrcode fa-3x" style="color: #667eea;"></i>
                    <div class="qr-code" id="qrValue"></div>
                    <div class="timer" id="timer">⏱️ Valid for 1:00 minute</div>
                </div>
            </div>

            <h3 style="margin: 30px 0 15px; color: #333;">
                <i class="fas fa-list"></i> Attendance Records
            </h3>
            
            <div class="table-container" id="attendanceTable">
                <table>
                    <tr><th>Name</th><th>Roll No</th><th>Time</th><th>Status</th></tr>
                    <tr><td colspan="4" style="text-align: center;">Loading...</td></tr>
                </table>
            </div>
        </div>

        <div id="studentSection" class="main-card" style="display: none;">
            <div class="card-title">
                <i class="fas fa-user-graduate"></i>
                Student Portal
            </div>
            
            <div class="input-group">
                <input type="text" id="name" placeholder="Enter your full name">
            </div>
            
            <div class="input-group">
                <input type="text" id="roll" placeholder="Enter your roll number">
            </div>
            
            <div class="input-group">
                <input type="text" id="qrInput" placeholder="Enter QR code">
            </div>
            
            <button class="btn" onclick="markAttendance()" id="markBtn">
                <i class="fas fa-check-circle"></i> Mark Attendance
            </button>
            
            <div id="message" class="message"></div>
        </div>
    </div>

    <!-- Your existing JavaScript remains exactly the same -->
    <script>
        let activeQR = "";
        let timerInterval = null;

        // Toggle password visibility
        function togglePassword() {
            let passwordInput = document.getElementById('password');
            let toggleIcon = document.querySelector('.toggle-password');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                toggleIcon.classList.remove('fa-eye');
                toggleIcon.classList.add('fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                toggleIcon.classList.remove('fa-eye-slash');
                toggleIcon.classList.add('fa-eye');
            }
        }

        function showSection(section) {
            if (section === 'teacher') {
                document.getElementById('teacherSection').style.display = 'block';
                document.getElementById('studentSection').style.display = 'none';
                document.getElementById('statsSection').style.display = 'grid'                
                document.getElementById('teacherBtn').classList.add('active');
                document.getElementById('studentBtn').classList.remove('active');
                
                loadAttendance();
                loadStats();
            } else {
                document.getElementById('teacherSection').style.display = 'none';
                document.getElementById('studentSection').style.display = 'block';
                document.getElementById('statsSection').style.display = 'none';
                
                document.getElementById('studentBtn').classList.add('active');
                document.getElementById('teacherBtn').classList.remove('active');
            }
        }

        function generateQR() {
            let pass = document.getElementById('password').value;
            
            if (pass !== 'admin123') {
                alert('❌ Wrong password!');
                return;
            }

            let btn = document.getElementById('generateBtn');
            btn.innerHTML = '<span class="spinner"></span> Generating...';
            btn.disabled = true;

            fetch('/generate_qr')
                .then(res => res.json())
                .then(data => {
                    activeQR = data.qr;
                    document.getElementById('qrValue').innerText = activeQR;
                    document.getElementById('qrDisplay').style.display = 'block';
                    
                    // 60 seconds = 1 minute
                    startTimer(60);
                    
                    showMessage('✅ QR Code generated! Valid for 1 minute', 'success');
                })
                .catch(error => {
                    alert('❌ Error generating QR code');
                })
                .finally(() => {
                    btn.innerHTML = '<i class="fas fa-qrcode"></i> Generate QR Code (1 min valid)';
                    btn.disabled = false;
                });
        }

        function startTimer(duration) {
            if (timerInterval) clearInterval(timerInterval);
            
            let timer = duration;
            timerInterval = setInterval(() => {
                let seconds = timer;
                
                document.getElementById('timer').innerHTML = `⏱️ Valid for 0:${seconds < 10 ? '0' + seconds : seconds}`;
                
                if (--timer < 0) {
                    clearInterval(timerInterval);
                    document.getElementById('timer').innerHTML = '⏱️ QR Code Expired!';
                    activeQR = "";
                }
            }, 1000);
        }

        function markAttendance() {
            let name = document.getElementById('name').value.trim();
            let roll = document.getElementById('roll').value.trim();
            let qr = document.getElementById('qrInput').value.trim();

            if (!name || !roll || !qr) {
                showMessage('❌ Please fill all fields!', 'error');
                return;
            }

            let btn = document.getElementById('markBtn');
            let originalText = btn.innerHTML;
            btn.innerHTML = '<span class="spinner"></span> Processing...';
            btn.disabled = true;

            fetch('/mark', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: name, roll: roll, qr: qr})
            })
            .then(res => res.json())
            .then(data => {
                showMessage(data.msg, data.msg.includes('✅') ? 'success' : 'error');
                
                if (data.msg.includes('✅')) {
                    document.getElementById('name').value = '';
                    document.getElementById('roll').value = '';
                    document.getElementById('qrInput').value = '';
                    
                    if (document.getElementById('teacherSection').style.display === 'block') {
                        loadAttendance();
                        loadStats();
                    }
                }
            })
            .catch(error => {
                showMessage('❌ Error: ' + error, 'error');
            })
            .finally(() => {
                btn.innerHTML = originalText;
                btn.disabled = false;
            });
        }

        function showMessage(msg, type) {
            let msgDiv = document.getElementById('message');
            msgDiv.className = 'message ' + type;
            msgDiv.innerHTML = msg;
            
            setTimeout(() => {
                msgDiv.className = 'message';
            }, 3000);
        }

        function loadAttendance() {
            fetch('/attendance')
                .then(res => res.json())
                .then(data => {
                    let html = '<table><tr><th>Name</th><th>Roll No</th><th>Time</th><th>Status</th></tr>';
                    
                    if (data.length === 0) {
                        html += '<tr><td colspan="4" style="text-align: center; padding: 30px;">📭 No attendance records yet</td></tr>';
                    } else {
                        data.forEach(r => {
                            html += `<tr>
                                <td>${r.name}</td>
                                <td>${r.roll}</td>
                                <td>${r.time}</td>
                                <td><span class="badge">Present</span></td>
                            </tr>`;
                        });
                    }
                    html += '</table>';
                    document.getElementById('attendanceTable').innerHTML = html;
                });
        }

        function loadStats() {
            fetch('/attendance')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('totalCount').innerText = data.length;
                    
                    let today = new Date().toDateString();
                    let todayCount = data.filter(r => new Date(r.time).toDateString() === today).length;
                    document.getElementById('todayCount').innerText = todayCount;
                    
                    let rate = data.length > 0 ? Math.round((todayCount / data.length) * 100) : 0;
                    document.getElementById('rateCount').innerText = rate + '%';
                });
        }

        setInterval(() => {
            if (document.getElementById('teacherSection').style.display === 'block') {
                loadAttendance();
                loadStats();
            }
        }, 5000);

        showSection('teacher');
        loadAttendance();
        loadStats();
    </script>
</body>
</html>
"""

# ================= FLASK ROUTES =================

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/generate_qr")
def generate_qr():
    global active_qr, active_qr_time
    active_qr = "QROLL_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    active_qr_time = time.time()
    return jsonify({"qr": active_qr})

@app.route("/mark", methods=["POST"])
def mark():
    try:
        data = request.json
        print(f"📝 Received: {data}")
        
        current_time = time.time()
        
        # Check QR validity - 60 seconds only
        if data["qr"] == active_qr and (current_time - active_qr_time) < QR_VALID_SECONDS:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            today = datetime.now().strftime("%Y-%m-%d")
            
            conn = sqlite3.connect('attendance.db')
            c = conn.cursor()
            
            # Check if already marked today
            c.execute("SELECT * FROM attendance WHERE roll=? AND date=?", (data["roll"], today))
            if c.fetchone():
                conn.close()
                return jsonify({"msg": "⚠️ Already marked for today!"})
            
            # Insert new record
            c.execute("""INSERT INTO attendance 
                        (name, roll, time, date, status) 
                        VALUES (?,?,?,?,?)""",
                     (data["name"], data["roll"], now, today, "Present"))
            conn.commit()
            conn.close()
            
            print(f"✅ Saved: {data['name']} at {now}")
            return jsonify({"msg": "✅ Attendance Marked Successfully!"})
        else:
            if data["qr"] != active_qr:
                return jsonify({"msg": "❌ Invalid QR Code!"})
            else:
                return jsonify({"msg": "❌ QR Code Expired! (1 minute only)"})
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"msg": f"❌ Error: {str(e)}"})

@app.route("/attendance")
def attendance():
    try:
        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()
        c.execute("SELECT name, roll, time FROM attendance ORDER BY time DESC")
        rows = c.fetchall()
        conn.close()
        
        attendance_list = []
        for row in rows:
            attendance_list.append({
                "name": row[0],
                "roll": row[1],
                "time": row[2]
            })
        return jsonify(attendance_list)
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify([])

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║                                                      ║
    ║     ██████╗  ██████╗  ██████╗ ██╗     ██╗         ║
    ║    ██╔═══██╗██╔═══██╗██╔═══██╗██║     ██║         ║
    ║    ██║   ██║██║   ██║██║   ██║██║     ██║         ║
    ║    ██║▄▄ ██║██║   ██║██║   ██║██║     ██║         ║
    ║    ╚██████╔╝╚██████╔╝╚██████╔╝███████╗███████╗    ║
    ║     ╚══▀▀═╝  ╚═════╝  ╚═════╝ ╚══════╝╚══════╝    ║
    ║                                                      ║
    ║         ✨ QROLL Attendance System ✨               ║
    ║         ============================                 ║
    ║                                                      ║
    ║    🚀 Server: http://localhost:5000                 ║
    ║    🔑 Password: admin123                             ║
    ║    ⏱️  QR Expiry: 1 MINUTE ONLY!                    ║
    ║    📍 GPS: No permission required                   ║
    ║                                                      ║
    ║    ✅ Added comprehensive internal CSS              ║
    ║    ✅ Responsive design for all devices             ║
    ║    ✅ Smooth animations and transitions              ║
    ║    ✅ Custom scrollbar and accessibility            ║
    ║                                                      ║
    ╚══════════════════════════════════════════════════════╝
    """)
    app.run(host="0.0.0.0", port=5000, debug=True)