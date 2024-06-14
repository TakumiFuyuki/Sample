# main.py

from flask import Flask, render_template, request, redirect, url_for, flash, session
from google.cloud import bigquery
from google.cloud import storage
from datetime import datetime
import utils

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

bigquery_client = bigquery.Client()
storage_client = storage.Client()

dataset_name = 'my-project-sample-425203.dataset'
registration_table = 'registration'
file_table = 'user_files'
bucket_name = 'txt_submit'
bucket = storage_client.bucket(bucket_name)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/registration', methods=['GET'])
def registration_page():
    return render_template('registration.html')

@app.route('/registration', methods=['POST'])
def registration():
    try:
        button_time = datetime.now()
        email = request.form['email']
        password = request.form['password']
        if not utils.is_valid_password(password):
            flash('パスワードは4文字以上で、アルファベットと数字が少なくとも1文字以上含まれている必要があります。')
            return redirect(url_for('registration_page'))
        if utils.is_email_registered(email):
            flash('このメールアドレスはすでに登録されています。')
            return redirect(url_for('registration_page'))
        utils.insert_registration_to_bigquery(email, button_time, password)
        flash('登録が完了しました。ログインしてください。')
        return redirect(url_for('login_page'))
    except Exception as e:
        flash(f'エラーが発生しました: {e}', 'error')
        return 'error'

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    if utils.authenticate_user(email, password):
        return redirect(url_for('upload_page'))
    else:
        flash('メールアドレスかパスワードが異なります。')
        return redirect(url_for('login_page'))

@app.route('/upload', methods=['GET'])
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user' not in session:
        return redirect(url_for('login_page'))

    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.txt'):
            user_email = session['user']
            file_name = f'{user_email}_{datetime.now().strftime("%Y%m%d%H%M%S")}_{file.filename}'
            blob = bucket.blob(file_name)
            blob.upload_from_string(file.read(), content_type=file.content_type)
            utils.insert_file_record(user_email, file_name)
            flash(f'File {file.filename} uploaded to {bucket_name}.')
            return redirect(url_for('upload_file'))
        else:
            flash('Only .txt files are allowed.')
            return redirect(url_for('upload_file'))
    return render_template('upload.html')

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    if 'user' not in session:
        return redirect(url_for('login_page'))
    user_email = session['user']
    if not utils.is_user_file(user_email, filename):
        flash('You are not authorized to download this file.')
        return redirect(url_for('list_files'))
    blob = bucket.blob(filename)
    file_content = blob.download_as_string()
    return file_content, 200, {
        'Content-Disposition': f'attachment; filename={filename}',
        'Content-Type': blob.content_type
    }

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/files')
def list_files():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    user_email = session['user']
    files = utils.get_user_files(user_email)
    return render_template('files.html', files=files)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)