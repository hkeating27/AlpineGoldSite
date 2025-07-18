import os
import psycopg2
from flask import Flask, request, jsonify, redirect, url_for, send_from_directory

app = Flask(__name__)
DB_URL = os.environ.get('DATABASE_URL')

def get_conn():
    return psycopg2.connect(DB_URL, sslmode='require')

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
      CREATE TABLE IF NOT EXISTS referrals (
        id SERIAL PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        referred_by TEXT
      );
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

# 1) Splash page
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# 2) Referrals list page
@app.route('/referrals')
def referrals_page():
    return send_from_directory('static', 'referrals.html')

# 3) API endpoints
@app.route('/add', methods=['POST'])
def add_referral():
    data = request.get_json()
    conn = get_conn(); cur = conn.cursor()
    cur.execute(
      'INSERT INTO referrals (first_name, last_name, referred_by) VALUES (%s, %s, %s)',
      (data['first_name'], data['last_name'], data['referred_by'])
    )
    conn.commit(); cur.close(); conn.close()
    return 'Submitted successfully!', 200

@app.route('/get_by_referrer')
def get_by_referrer():
    ref = request.args.get('referred_by', '')
    conn = get_conn(); cur = conn.cursor()
    cur.execute(
      'SELECT first_name, last_name FROM referrals WHERE referred_by = %s',
      (ref,)
    )
    rows = cur.fetchall(); cur.close(); conn.close()
    return jsonify(rows)

# 4) Catch‑all for pretty‑URL QR codes and static files
@app.route('/<path:filename>')
def catch_all(filename):
    # If the path starts with "$ref=", redirect to "/?ref=..."
    if filename.startswith('$ref='):
        ref = filename.split('=', 1)[1]
        return redirect(url_for('index', ref=ref))
    # Otherwise serve it out of the static/ folder:
    return send_from_directory('static', filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
