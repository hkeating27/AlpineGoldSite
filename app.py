import os
import psycopg2
from flask import (
    Flask, request, jsonify,
    send_from_directory, redirect, url_for,
    session, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app via factory
def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')
    app.secret_key = os.environ.get('SECRET_KEY', 'change_this!')
    DATABASE_URL = os.environ.get('DATABASE_URL')

    def get_conn():
        return psycopg2.connect(DATABASE_URL, sslmode='require')

    # Initialize database tables
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('''
          CREATE TABLE IF NOT EXISTS referrals (
            id SERIAL PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            referred_by TEXT NOT NULL
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

    # Home page
    @app.route('/')
    def index():
        return send_from_directory('static', 'index.html')

    # Static and pretty URL catch-all
    @app.route('/<path:filename>')
    def catch_all(filename):
        if filename.startswith('$ref='):
            ref = filename.split('=',1)[1]
            return redirect(url_for('login_page', ref=ref))
        return send_from_directory('static', filename)

    # Registration routes
    @app.route('/register', methods=['GET'])
    def register_page():
        return send_from_directory('static', 'register.html')

    @app.route('/register', methods=['POST'])
    def register():
        data = request.get_json()
        u = data.get('username','').strip().lower()
        p = data.get('password','')
        phash = generate_password_hash(p)
        try:
            with get_conn() as conn:
                cur = conn.cursor()
                cur.execute(
                  'INSERT INTO users (username, password_hash) VALUES (%s, %s)',
                  (u, phash)
                )
                conn.commit()
            return jsonify(success=True), 200
        except psycopg2.IntegrityError:
            return jsonify(success=False, error='Username exists'), 400

    # Login routes
    @app.route('/login', methods=['GET'])
    def login_page():
        return send_from_directory('static', 'login.html')

    @app.route('/login', methods=['POST'])
    def do_login():
        data = request.get_json()
        u = data.get('username','').strip().lower()
        p = data.get('password','')
        # Admin check
        if u == 'admin_dennis' and p == 'metroid_prime':
            session['username'] = u
            session['is_admin'] = True
            return jsonify(success=True, role='admin', username=u)
        # Referrer check
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('SELECT password_hash FROM users WHERE username=%s', (u,))
            row = cur.fetchone()
        if row and check_password_hash(row[0], p):
            session['username'] = u
            session['is_admin'] = False
            return jsonify(success=True, role='referrer', username=u)
        return jsonify(success=False, error='Invalid credentials'), 401

    # Logout
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('index'))

    # Add referral
    @app.route('/add', methods=['POST'])
    def add_referral():
        data = request.get_json()
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
              'INSERT INTO referrals (first_name, last_name, referred_by) VALUES (%s, %s, %s)',
              (data['name'], data['email'], data['referred_by'])
            )
            conn.commit()
        return 'Submitted successfully!', 200

    # Get referrals for user or admin
    @app.route('/get_by_referrer')
    def get_by_referrer():
        if 'username' not in session:
            abort(401)
        ref = request.args.get('referred_by','').strip().lower()
        if not session.get('is_admin') and session.get('username') != ref:
            abort(403)
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
              'SELECT first_name, last_name FROM referrals WHERE referred_by=%s',
              (ref,)
            )
            rows = cur.fetchall()
        return jsonify(rows)

    # Whoami endpoint
    @app.route('/whoami')
    def whoami():
        return jsonify(username=session.get('username',''), is_admin=session.get('is_admin', False))

    # Admin dashboard
    @app.route('/admin')
    def admin_dashboard():
        if not session.get('is_admin'):
            abort(401)
        return send_from_directory('static', 'admin.html')

    @app.route('/admin/users')
    def admin_list_users():
        if not session.get('is_admin'):
            abort(401)
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('SELECT username, referred_by FROM users')
            users = cur.fetchall()
        return jsonify(users)

    return app

# Expose WSGI app for Gunicorn
def_app = create_app()
app = def_app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)












