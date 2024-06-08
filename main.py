# main.py

from flask import Flask, render_template, request
from google.cloud import bigquery
from datetime import datetime

app = Flask(__name__)

client = bigquery.Client()

dataset_name = 'my-project-sample-425203.dataset'
registration_table = 'registration'

@app.route('/')
def index():
    return render_template('registration.html')

@app.route('/registration', methods=['POST'])
def registration():
    try:
        button_time = datetime.now()
        id = request.form['email']
        password = request.form['password']
        insert_registration_to_bigquery(button_time, id, password)
        return '登録が完了しました'
    except Exception as e:
        return f'エラーが発生しました: {e}', 500


def insert_registration_to_bigquery(id, button_time, password):
    button_time_iso = button_time.isoformat()
    rows_to_insert = [
        {
            'id': id,
            'datetime': button_time_iso,
            'pass': password
        }
    ]
    table_id = f'{dataset_name}.{registration_table}'
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        raise Exception(f'BigQueryへのデータ挿入中にエラーが発生しました: {errors}')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)