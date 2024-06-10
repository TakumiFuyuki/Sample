# main.py

from flask import Flask, render_template, request, redirect, url_for, flash
from google.cloud import bigquery
from datetime import datetime
import re

app = Flask(__name__)

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
        if not validate_password(password):
            return 'パスワードは4文字以上で、アルファベットと数字をそれぞれ少なくとも1文字含む必要があります。', 400
        if is_email_registered(email):
            return 'このメールアドレスは既に登録されています。', 400
        insert_registration_to_bigquery(email, button_time, password)
        flash('登録が完了しました。ログインしてください。', 'success')
        return redirect(url_for('login_page'))
    except Exception as e:
        return f'エラーが発生しました: {e}', 500

def validate_password(password):
    if len(password) < 4:
        return False
    if not re.search("[a-zA-Z]", password):
        return False
    if not re.search("[0-9]", password):
        return False
    return True

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
    SELECT id FROM `{dataset_name}.{registration_table}`
    WHERE id = '{email}'
    """
    query_job = client.query(query)
    results = query_job.result()

    for row in results:
        return True
    return False

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    if authenticate_user(email, password):
        return 'ログインに成功しました'
    else:
        return 'ログインに失敗しました', 401

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