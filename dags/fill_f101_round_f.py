import os

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from lib.database import PostgresDB
from dotenv import load_dotenv

from lib.logger import Logger

load_dotenv()

PROCESS_NAME = 'FILL_DM_F101_ROUND_F'

def fill_turover_for_period(date_str):
    db = None
    logger = None
    
    try:
        with PostgresDB(os.getenv("DB_NAME"), os.getenv("DB_USER"), os.getenv("DB_PASSWORD"), os.getenv("DB_HOST"), os.getenv("DB_PORT")) as db:
            current = datetime.strptime(date_str, "%Y-%m-%d").date()

            db.execute("CALL dm.fill_f101_round_f(%s);", (current,))
            db.close()
    except Exception as e:
        logger = Logger(db, PROCESS_NAME)
        error_msg = f"Ошибка при создании витрины данных: {e}"
        if logger:
            logger.log('error', error_msg)
        raise e

default_args = {
    'owner': 'etl',
    'depends_on_past': False,
    'retries': 1,
}

with DAG(
    dag_id='dm_fill_f101_round_f',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    params={
        "date": "2018-02-01"
    },
    tags=['dm', 'f101'],
) as dag:
    run_fill_f101_round_f = PythonOperator(
        task_id='run_fill_f101_round_f',
        python_callable=fill_turover_for_period,
        op_args=[
            "{{ params.date }}"
        ]
    )