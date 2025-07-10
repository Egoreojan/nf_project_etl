import os

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from lib.database import PostgresDB
from dotenv import load_dotenv

from lib.logger import Logger

load_dotenv()

PROCESS_NAME = 'FILL_DM_ACCOUNT_TURNOVER_F'

def fill_turover_for_period(start_date_str, end_date_str):
    db = None
    logger = None
    
    try:
        with PostgresDB(os.getenv("DB_NAME"), os.getenv("DB_USER"), os.getenv("DB_PASSWORD"), os.getenv("DB_HOST"), os.getenv("DB_PORT")) as db:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            current = start_date

            while current <= end_date:
                db.execute("CALL ds.fill_account_turnover_f(%s);", (current,))
                current += timedelta(days=1)

            db.close()
    except Exception as e:
        logger = Logger(db, PROCESS_NAME)
        error_msg = f"Ошибка при создании витрины данных: {e}"
        if logger:
            logger.log('error', error_msg)
        raise e

default_args = {
    'owner': 'egor',
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

with DAG(
    dag_id='fill_account_turnover',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    params={
        "start_date": "2018-01-01",
        "end_date": "2018-01-31"
    },
    tags=['bank', 'turnover']
) as dag:
    fill_turnover = PythonOperator(
        task_id='fill_turnover_for',
        python_callable=fill_turover_for_period,
        op_args=[
            "{{ params.start_date }}", 
            "{{ params.end_date }}"
        ]
    )
