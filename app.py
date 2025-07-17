import os
import psycopg2
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='static', static_url_path='')

# Grab the DATABASE_URL that Render set in your env
DATABASE_URL = os.environ['DATABASE_URL']

def get_conn():
    # Connect via SSL (Render requires it)
    return psycopg2.connect(DATABASE_URL, sslmode='require')

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

# Initialize the table on startup
init_db()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/referrals')
def referrals_page():
    return send_from_directory('static', 'referrals.html')

@app.route('/add', methods=['POST'])
def add_referral():
    data = request.get_json()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
      'INSERT INTO referrals (first_name, last_name, referred_by) VALUES (%s, %s, %s)',
      (data['first_name'], data['last_name'], data['referred_by'])
    )
    conn.commit()
    cur.close()
    conn.close()
    return 'Submitted successfully!', 200

@app.route('/get_by_referrer')
def get_by_referrer():
    ref = request.args.get('referred_by', '')
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
      'SELECT first_name, last_name FROM referrals WHERE referred_by = %s',
      (ref,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)

if __name__ == '__main__':
    # Render sets PORT for you; default to 5000 locally
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
