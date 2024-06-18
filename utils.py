# utils.py

from google.cloud import bigquery
from google.cloud import storage
from datetime import datetime
import re

bigquery_client = bigquery.Client()
storage_client = storage.Client()

dataset_name = 'my-project-sample-425203.dataset'
registration_table = 'registration'
file_table = 'user_files'
bucket_name = 'txt_submit'
bucket = storage_client.bucket(bucket_name)

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

def insert_file_record(email, file_name):
    rows_to_insert = [
        {
            'user_email': email,
            'file_name': file_name,
            'upload_time': datetime.now().isoformat()
        }
    ]
    table_id = f'{dataset_name}.{file_table}'
    errors = bigquery_client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        raise Exception(f'BigQueryへのファイル情報挿入中にエラーが発生しました: {errors}')

def is_user_file(email, file_name):
    query = f"""
    SELECT COUNT(1) as count FROM `{dataset_name}.{file_table}`
    WHERE user_email = '{email}' AND file_name = '{file_name}'
    """
    query_job = bigquery_client.query(query)
    results = query_job.result()
    for row in results:
        if row['count'] > 0:
            return True
    return False

def get_user_files(email):
    query = f"""
    SELECT file_name, upload_time FROM `{dataset_name}.{file_table}`
    WHERE user_email = '{email}'
    ORDER BY upload_time DESC
    """
    query_job = bigquery_client.query(query)
    results = query_job.result()
    return [{'file_name': row['file_name'], 'upload_time': row['upload_time']} for row in results]