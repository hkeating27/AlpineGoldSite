from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

def init_db():
    conn = sqlite3.connect('referrals.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            referred_by TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/add', methods=['POST'])
def add_referral():
    data = request.get_json()
    first = data.get('first_name')
    last = data.get('last_name')
    referred_by = data.get('referred_by')

    conn = sqlite3.connect('referrals.db')
    c = conn.cursor()
    c.execute('INSERT INTO referrals (first_name, last_name, referred_by) VALUES (?, ?, ?)',
              (first, last, referred_by))
    conn.commit()
    conn.close()

    return 'Submitted successfully!', 200

@app.route('/get_by_referrer', methods=['GET'])
def get_by_referrer():
    referrer = request.args.get('referred_by')

    conn = sqlite3.connect('referrals.db')
    c = conn.cursor()
    c.execute('SELECT first_name, last_name FROM referrals WHERE referred_by = ?', (referrer,))
    rows = c.fetchall()
    conn.close()

    return jsonify(rows)

if __name__ == '__main__':
    app.run(debug=True)