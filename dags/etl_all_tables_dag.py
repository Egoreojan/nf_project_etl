from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from etl_loader_all_tables import load_all_tables

default_args = {
    'owner': 'egor',
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

with DAG(
    dag_id='etl_all_tables_dag',
    default_args=default_args,
    description='Загрузка всех таблиц из CSV файлов в базу данных',
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['etl', 'bank', 'all_tables']
) as dag:
    load_all_task = PythonOperator(
        task_id='load_all_tables',
        python_callable=load_all_tables
    )

    load_all_task 