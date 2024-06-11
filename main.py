# main.py

from flask import Flask, render_template, request, redirect, url_for, flash
from google.cloud import bigquery
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

client = bigquery.Client()

dataset_name = 'my-project-sample-425203.dataset'
registration_table = 'registration'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registration')
def registration_page():
    return render_template('registration.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/registration', methods=['POST'])
def registration():
    try:
        button_time = datetime.now()
        email = request.form['email']
        password = request.form['password']
        if is_email_registered(email):
            flash('このメールアドレスはすでに登録されています。')
            return redirect(url_for('registration_page'))
        insert_registration_to_bigquery(email, button_time, password)
        return redirect(url_for('login_page'))
    except Exception as e:
        # flash(f'エラーが発生しました: {e}', 'error')
        return 'error'

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    if authenticate_user(email, password):
        return 'ログインに成功しました'
    else:
        return 'ログインに失敗しました', 401

def insert_registration_to_bigquery(email, button_time, password):
    button_time_iso = button_time.isoformat()
    rows_to_insert = [
        {
            'id': email,
            'datetime': button_time_iso,
            'password': password
        }
    ]
    table_id = f'{dataset_name}.{registration_table}'
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        raise Exception(f'BigQueryへのデータ挿入中にエラーが発生しました: {errors}')

def is_email_registered(email):
    query = f"""
    SELECT COUNT(1) as count FROM `{dataset_name}.{registration_table}`
    WHERE id = '{email}'
    """
    query_job = client.query(query)
    results = query_job.result()
    for row in results:
        if row['count'] > 0:
            return True
    return False

def authenticate_user(email, password):
    query = f"""
    SELECT password FROM `{dataset_name}.{registration_table}`
    WHERE id = '{email}'
    """
    query_job = client.query(query)
    results = query_job.result()
    for row in results:
        if row['password'] == password:
            return True
    return False

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)