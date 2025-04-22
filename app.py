import os
import random
import sqlite3
from flask import Flask, render_template, request, redirect, session, flash, send_from_directory, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Replace with your Fernet key (keep it secret!)
FERNET_KEY = b'5T4NnlfZz4dtU1q0Vd_DSOPMNqSqloceb8Lf7SQBkbs='
fernet = Fernet(FERNET_KEY)

# Auto-create database
def init_db():
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, surname TEXT,
            phone TEXT, password TEXT,
            email TEXT UNIQUE, photo TEXT, user_id TEXT
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT, recipient TEXT,
            subject TEXT, body TEXT,
            attachment TEXT
        )''')
init_db()

@app.route('/')
def index():
    if 'user' in session:
        return redirect('/dashboard')
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        phone = fernet.encrypt(request.form['phone'].encode()).decode()
        password = generate_password_hash(request.form['password'])
        email = f"{name[0].lower()}{surname.lower()}@sherwinlifescience.com"
        photo = request.files['photo']
        photo_filename = secure_filename(photo.filename)
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
        user_id = ''.join(random.choices('0123456789', k=6))

        try:
            with sqlite3.connect('database.db') as conn:
                cur = conn.cursor()
                cur.execute('''INSERT INTO users (name, surname, phone, password, email, photo, user_id)
                               VALUES (?, ?, ?, ?, ?, ?, ?)''',
                            (name, surname, phone, password, email, photo_filename, user_id))
                conn.commit()
                flash("Registration successful! Please log in.")
        except sqlite3.IntegrityError:
            flash("User already exists!")
        return redirect('/')
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    if 'user' in session:
        return redirect('/dashboard')

    email = request.form['email']
    password = request.form['password']

    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cur.fetchone()
        if user and check_password_hash(user[4], password):
            session['user'] = user[5]
            session['name'] = f"{user[1]} {user[2]}"
            session['user_id'] = user[7]
            session['photo'] = user[6]
            return redirect('/dashboard')
        else:
            flash("Invalid Credentials")
            return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM emails WHERE recipient = ?', (session['user'],))
        inbox_emails = cur.fetchall()
        cur.execute('SELECT * FROM emails WHERE sender = ?', (session['user'],))
        composed_emails = cur.fetchall()
    return render_template('dashboard.html', emails=inbox_emails, composed=composed_emails)



@app.route('/compose', methods=['POST'])
def compose():
    if 'user' not in session:
        return redirect('/')
    to = request.form['to']
    subject = request.form['subject']
    body = request.form['body']
    file = request.files['attachment']
    filename = ''
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('''INSERT INTO emails (sender, recipient, subject, body, attachment)
                       VALUES (?, ?, ?, ?, ?)''',
                    (session['user'], to, subject, body, filename))
        conn.commit()
    flash("Email sent successfully!")
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/account')
def account():
    if 'user' not in session:
        return redirect('/')
    return render_template('acc_det.html')

@app.route('/update_photo', methods=['POST'])
def update_photo():
    if 'user' not in session:
        return redirect('/')
    photo = request.files['photo']
    filename = secure_filename(photo.filename)
    photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('UPDATE users SET photo = ? WHERE email = ?', (filename, session['user']))
        conn.commit()
        session['photo'] = filename
    flash("Profile photo updated!")
    return redirect('/account')

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user' not in session:
        return redirect('/')
    old = request.form['old_password']
    new = request.form['new_password']
    repeat = request.form['repeat_password']
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT password FROM users WHERE email = ?', (session['user'],))
        current_hashed = cur.fetchone()[0]
        if not check_password_hash(current_hashed, old):
            flash("Old password is incorrect")
            return redirect('/account')
        if new != repeat:
            flash("New passwords do not match")
            return redirect('/account')
        new_hashed = generate_password_hash(new)
        cur.execute('UPDATE users SET password = ? WHERE email = ?', (new_hashed, session['user']))
        conn.commit()
        flash("Password changed successfully")
    return redirect('/account')

@app.route('/mail/<int:mail_id>')
def view_mail(mail_id):
    if 'user' not in session:
        return redirect('/')
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, sender, recipient, subject, body, attachment FROM emails WHERE id = ? AND recipient = ?', (mail_id, session['user']))
        row = cur.fetchone()
        if row:
            mail = {
                'id': row[0],
                'sender': row[1],
                'recipient': row[2],
                'subject': row[3],
                'body': row[4],
                'attachment': row[5]
            }
            return render_template('mail.html', mail=mail)
        else:
            flash("Email not found.")
            return redirect('/dashboard')
        
@app.route('/composed-and-sent')
def composed_and_sent():
    if 'user' not in session:
        return redirect('/')
    
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute('SELECT * FROM emails WHERE sender = ?', (session['user'],))
    sent_emails = cur.fetchall()
    conn.close()

    return render_template('com&sent.html', sent_emails=sent_emails, name=session['name'], photo=session['photo'])

@app.route('/unsend-email', methods=['POST'])
def unsend_email():
    if 'user' not in session:
        return redirect('/')

    email_id = request.form['email_id']
    
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('DELETE FROM emails WHERE id = ? AND sender = ?', (email_id, session['user']))
    conn.commit()
    conn.close()

    return redirect(url_for('composed_and_sent'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='2021')
