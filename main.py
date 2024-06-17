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
            return redirect(url_for('main'))
    return render_template('login.html')

@app.route('/main', methods=['GET'])
def main():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('main.html')

@app.route('/logout', methods=['GET'])
def logout():
    # デバッグ情報を追加
    print(f"Current session: {session}")
    # session.popの正しい使い方
    session.pop('logged_in', None)
    # デバッグ情報を追加
    print(f"Session after pop: {session}")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)