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

# @app.route('/registration', ['GET', 'POST'])
# def registration():
#     return render_template('registration.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return redirect(url_for('main'))
    return render_template('login.html')

@app.route('/main', methods=['GET'])
def main():
    return render_template('main.html')

@app.route('/logout', methods=['GET'])
def logout():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)