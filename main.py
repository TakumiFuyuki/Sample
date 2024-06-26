# main.py

from flask import Flask, render_template, request, redirect, url_for, flash, session
from google.cloud import bigquery
from google.cloud import storage
from datetime import datetime
import utils

from google.oauth2 import service_account

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# # TODO(developer): Set key_path to the path to the service account key
# #                  file.
# key_path = "C:\\Users\\taku0\\OneDrive - 中央大学\\デスクトップ\\task\\Sample\\auth_app.json"

# credentials = service_account.Credentials.from_service_account_file(
#     key_path,
#     scopes=["https://www.googleapis.com/auth/cloud-platform"],
# )

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

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        button_time = datetime.now()
        email = request.form['email']
        password = request.form['password']
        if not utils.is_valid_password(password):
            flash('パスワードは4文字以上で、アルファベットと数字が少なくとも1文字以上含まれている必要があります。')
            return redirect(url_for('registration'))
        if utils.is_email_registered(email):
            flash('このメールアドレスはすでに登録されています。')
            return redirect(url_for('registration'))
        utils.insert_registration_to_bigquery(email, button_time, password)
        flash('登録が完了しました。ログインしてください。')
        return redirect(url_for('login'))
    return render_template('registration.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if not utils.authenticate_user(email, password):
            flash('メールアドレスかパスワードが異なります。')
            return redirect(url_for('login'))
        else:
            session['logged_in'] = True
            session['email'] = email
            return redirect(url_for('main'))
    return render_template('login.html')

@app.route('/main', methods=['GET'])
def main():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    email = session['email']
    files = utils.get_user_files(email)
    return render_template('main.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    email = session['email']
    file = request.files['file']
    if file.filename == '':
        flash('ファイルが選択されていません。')
        return redirect(url_for('main'))

    filename = f"{email}/{file.filename}"
    blob = bucket.blob(filename)
    blob.upload_from_file(file)

    utils.insert_file_record(email, filename)
    flash('ファイルがアップロードされました。')
    return redirect(url_for('main'))

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('logged_in', None)
    session.pop('email', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)