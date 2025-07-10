import os

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta
from lib.database import PostgresDB
from dotenv import load_dotenv

from lib.logger import Logger

load_dotenv()

PROCESS_NAME = 'PREFILL_DM_ACCOUNT_BALANCE_F'

def prefill_account_balance_for_date(date_str):
    db = None
    logger = None

    try:
        with PostgresDB(os.getenv("DB_NAME"), os.getenv("DB_USER"), os.getenv("DB_PASSWORD"), os.getenv("DB_HOST"), os.getenv("DB_PORT")) as db:
            current = datetime.strptime(date_str, "%Y-%m-%d").date()

            db.execute("CALL dm.fill_account_balance_f(%s);", (current,))
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
    dag_id='prefill_account_balance',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    params={
        "date": "2017-12-31"
    },
    tags=['bank', 'pre balance']
) as dag:
    fill_turnover = PythonOperator(
        task_id='prefill_account_balance_for',
        python_callable=prefill_account_balance_for_date,
        op_args=[
            "{{ params.date }}"
        ]
    )