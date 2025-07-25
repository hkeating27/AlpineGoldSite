import os
import psycopg2
from flask import (
    Flask, request, jsonify,
    send_from_directory, redirect, url_for,
    session, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'change_this!')
DATABASE_URL = os.environ['DATABASE_URL']

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# Initialize tables
with get_conn() as conn:
    cur = conn.cursor()
    cur.execute('''
      CREATE TABLE IF NOT EXISTS referrals (
        id SERIAL PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        referred_by TEXT
      );
    ''')
    cur.execute('''
      CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
      );
    ''')
    conn.commit()

# Serve splash page
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# Redirect pretty‑URL /$ref=Name → login
@app.route('/<path:filename>')
def catch_all(filename):
    if filename.startswith('$ref='):
        ref = filename.split('=',1)[1]
        return redirect(url_for('login_page', ref=ref))
    return send_from_directory('static', filename)

# Authentication and account pages
@app.route('/login', methods=['GET'])
def login_page():
    return send_from_directory('static', 'login.html')

@app.route('/register', methods=['GET'])
def register_page():
    return send_from_directory('static', 'register.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    u = data.get('username','').strip()
    p = data.get('password','')
    if not u or not p:
        return 'Missing username or password', 400
    phash = generate_password_hash(p)
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO users (username, password_hash) VALUES (%s, %s)',
                (u, phash)
            )
            conn.commit()
    except psycopg2.IntegrityError:
        return 'Username exists', 400
    return 'Registered', 200

@app.route('/login', methods=['POST'])
def do_login():
    data = request.get_json()
    u = data.get('username','').strip().lower()
    p = data.get('password','')
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT password_hash FROM users WHERE username=%s', (u,))
        row = cur.fetchone()
    if row and check_password_hash(row[0], p):
        session['username'] = u
        return 'OK', 200
    return 'Invalid', 401

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login_page'))

# API endpoints
@app.route('/add', methods=['POST'])
def add_referral():
    data = request.get_json()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO referrals (first_name, last_name, referred_by) VALUES (%s, %s, %s)',
            (data['first_name'], data['last_name'], data['referred_by'])
        )
        conn.commit()
    return 'Submitted', 200

@app.route('/get_by_referrer')
def get_by_referrer():
    if 'username' not in session:
        abort(401)
    ref = request.args.get('referred_by','').strip().lower()
    if session['username'] != ref:
        abort(403)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT first_name, last_name FROM referrals WHERE referred_by=%s',
            (ref,)
        )
        rows = cur.fetchall()
    return jsonify(rows)

@app.route('/whoami')
def whoami():
    return jsonify(username=session.get('username',''))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
