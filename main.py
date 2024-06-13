# main.py

from flask import Flask, render_template, request, redirect, url_for, flash
from google.cloud import bigquery
from google.cloud import storage
from datetime import datetime
import re
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

bigquery_client = bigquery.Client()
storage_client = storage.Client()

dataset_name = 'my-project-sample-425203.dataset'
registration_table = 'registration'
bucket_name = 'txt_submit'
bucket = storage_client.bucket(bucket_name)

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
        if not is_valid_password(password):
            flash('パスワードは4文字以上で、アルファベットと数字が少なくとも1文字以上含まれている必要があります。')
            return redirect(url_for('registration_page'))
        if is_email_registered(email):
            flash('このメールアドレスはすでに登録されています。')
            return redirect(url_for('registration_page'))
        insert_registration_to_bigquery(email, button_time, password)
        flash('登録が完了しました。ログインしてください。')
        return redirect(url_for('login_page'))
    except Exception as e:
        flash(f'エラーが発生しました: {e}', 'error')
        return 'error'

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    if authenticate_user(email, password):
        return render_template('upload.html')
    else:
        flash('メールアドレスかパスワードが異なります。')
        return redirect(url_for('login_page'))

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
    errors = bigquery_client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        raise Exception(f'BigQueryへのデータ挿入中にエラーが発生しました: {errors}')

def is_valid_password(password):
    if len(password) < 4:
        return False
    if not re.search('[A-Za-z]', password):
        return False
    if not re.search('[0-9]', password):
        return False
    return True

def is_email_registered(email):
    query = f"""
    SELECT COUNT(1) as count FROM `{dataset_name}.{registration_table}`
    WHERE id = '{email}'
    """
    query_job = bigquery_client.query(query)
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
    query_job = bigquery_client.query(query)
    results = query_job.result()
    for row in results:
        if row['password'] == password:
            return True
    return False

def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.txt'): #txtファイルに制限
            blob = bucket.blob(file.filename)
            blob.upload_from_string(file.read(), content_type=file.content_type)
            flash(f'File {file.filename} uploaded to {bucket_name}.')
            return redirect(url_for('index'))
        else:
            flash('Only .txt files are allowed.')
            return redirect(url_for('upload_file'))
    return render_template('upload.html')

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    blob = bucket.blob(filename)
    file_content = blob.download_as_string()
    return file_content, 200, {
        'Content-Disposition': f'attachment; filename={filename}',
        'Content-Type': blob.content_type
    }

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)