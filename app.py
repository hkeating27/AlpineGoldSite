from flask import (
    Flask, request, jsonify, send_from_directory,
    redirect, url_for, session, abort
)
import os, psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__,
            static_folder='static',
            static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'change_this!')

DATABASE_URL = os.environ['DATABASE_URL']
def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# … your init_db, register, login/logout, add, get_by_referrer …  

#  new endpoint:
@app.route('/whoami')
def whoami():
    # returns the logged‑in username or empty
    return jsonify(username=session.get('username',''))

# catch‑all /redirect logic remains as before
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
