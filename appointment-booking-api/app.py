from flask import Flask, jsonify, request, render_template, redirect, url_for, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Kunci rahsia untuk membolehkan sistem session berfungsi
app.secret_key = 'kod_rahsia_paling_selamat_123'

# --- DATABASE SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'appointment_booking.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Table untuk Customer
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE)')
    # Table untuk Janji Temu
    conn.execute('''CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    user_id INTEGER, 
                    appointment_date TEXT, 
                    appointment_time TEXT, 
                    status TEXT DEFAULT 'pending', 
                    notes TEXT)''')
    # Table untuk Admin
    conn.execute('CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- ROUTES DASHBOARD ---

@app.route('/')
def home():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    # Check jika admin sudah login
    is_admin = session.get('admin_logged_in', False)
    
    appointments = conn.execute('''
        SELECT a.*, u.name as user_name 
        FROM appointments a 
        JOIN users u ON a.user_id = u.id
    ''').fetchall()
    conn.close()
    return render_template('index.html', users=users, appointments=appointments, is_admin=is_admin)

# --- SISTEM LOGIN & DAFTAR ADMIN ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if admin and check_password_hash(admin['password'], password):
            session['admin_logged_in'] = True
            session['admin_user'] = username
            return redirect(url_for('home'))
        return "Login Gagal! Username atau Password salah."
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/register_admin/<user>/<pwd>')
def register_admin(user, pwd):
    # Link rahsia untuk buat akaun admin pertama kali
    hashed_pwd = generate_password_hash(pwd)
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO admins (username, password) VALUES (?, ?)', (user, hashed_pwd))
        conn.commit()
        conn.close()
        return f"Admin '{user}' berjaya didaftarkan! <a href='/login'>Klik sini untuk Login</a>"
    except Exception as e:
        return f"Error: {e}"

# --- TINDAKAN ADMIN (PROTECTED) ---

@app.route('/confirm_appointment/<int:app_id>')
def confirm_appointment(app_id):
    # Sekatan: Jika bukan admin, tendang ke login
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    conn.execute('UPDATE appointments SET status = ? WHERE id = ?', ('confirmed', app_id))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

# --- FORM HANDLERS ---

@app.route('/add_user_form', methods=['POST'])
def add_user_form():
    name = request.form.get('name')
    email = request.form.get('email')
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO users (name, email) VALUES (?, ?)', (name, email))
        conn.commit()
        conn.close()
    except: pass
    return redirect(url_for('home'))

@app.route('/add_app_form', methods=['POST'])
def add_app_form():
    user_id = request.form.get('user_id')
    date = request.form.get('appointment_date')
    time = request.form.get('appointment_time')
    conn = get_db_connection()
    conn.execute('INSERT INTO appointments (user_id, appointment_date, appointment_time) VALUES (?, ?, ?)', (user_id, date, time))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)