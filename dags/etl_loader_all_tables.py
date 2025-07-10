import os
import time

from lib.database import PostgresDB
from lib.logger import Logger
from lib.tableconfig import TableConfig
from lib.tableloader import TableLoader
from dotenv import load_dotenv

load_dotenv()

PROCESS_NAME = 'ETL_ALL_TABLES'

def clean_currency_code_columns(df):
    for col in ['CURRENCY_CODE', 'CODE_ISO_CHAR']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str[:3]
    return df

def clean_char_type_column(df):
    if 'CHAR_TYPE' in df.columns:
        df['CHAR_TYPE'] = df['CHAR_TYPE'].astype(str).str.strip().str[:1]
    if 'CURRENCY_CODE' in df.columns:
        df['CURRENCY_CODE'] = df['CURRENCY_CODE'].astype(str).str.strip().str[:3]
    return df

def clean_ledger_account_char_columns(df):
    for col in [
        'CHAPTER', 'CHARACTERISTIC', 'MIN_TERM', 'MIN_TERM_MEASURE', 'MAX_TERM', 'MAX_TERM_MEASURE',
        'LEDGER_ACC_FULL_NAME_TRANSLIT', 'IS_REVALUATION', 'IS_CORRECT']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str[:1]
    return df

TABLE_CONFIGS = [
    TableConfig(
        name="MD_CURRENCY_D",
        file_path="/opt/airflow/data/tables/md_currency_d.csv",
        table_name="md_currency_d",
        date_columns={
            'DATA_ACTUAL_DATE': 'standard',
            'DATA_ACTUAL_END_DATE': 'standard'
        },
        conflict_columns=['currency_rk', 'data_actual_date'],
        custom_transform=clean_currency_code_columns
    ),
    
    TableConfig(
        name="MD_EXCHANGE_RATE_D",
        file_path="/opt/airflow/data/tables/md_exchange_rate_d.csv",
        table_name="md_exchange_rate_d",
        date_columns={
            'DATA_ACTUAL_DATE': 'standard',
            'DATA_ACTUAL_END_DATE': 'standard'
        },
        conflict_columns=['data_actual_date', 'currency_rk']
    ),
    
    TableConfig(
        name="MD_LEDGER_ACCOUNT_S",
        file_path="/opt/airflow/data/tables/md_ledger_account_s.csv",
        table_name="md_ledger_account_s",
        date_columns={
            'START_DATE': 'standard',
            'END_DATE': 'standard'
        },
        conflict_columns=['ledger_account', 'start_date'],
        custom_transform=clean_ledger_account_char_columns
    ),
    
    TableConfig(
        name="MD_ACCOUNT_D",
        file_path="/opt/airflow/data/tables/md_account_d.csv",
        table_name="md_account_d",
        date_columns={
            'DATA_ACTUAL_DATE': 'standard',
            'DATA_ACTUAL_END_DATE': 'standard'
        },
        conflict_columns=['data_actual_date', 'account_rk'],
        custom_transform=clean_char_type_column,
        encoding='cp1251'
    ),
    
    TableConfig(
        name="FT_BALANCE_F",
        file_path="/opt/airflow/data/tables/ft_balance_f.csv",
        table_name="ft_balance_f",
        date_columns={
            'ON_DATE': 'DD.MM.YYYY'
        },
        conflict_columns=['on_date', 'account_rk']
    ),
    
    TableConfig(
        name="FT_POSTING_F",
        file_path="/opt/airflow/data/tables/ft_posting_f.csv",
        table_name="ft_posting_f",
        date_columns={
            'OPER_DATE': 'DD-MM-YYYY'
        },
        conflict_columns=[],  # Нет конфликтных колонок, таблица очищается
        clear_before_load=True
    )
]


def load_all_tables():
    db = None
    logger = None
    try:
        with PostgresDB(os.getenv("DB_NAME"), os.getenv("DB_USER"), os.getenv("DB_PASSWORD"), os.getenv("DB_HOST"), os.getenv("DB_PORT")) as db:
            logger = Logger(db, PROCESS_NAME)
            logger.log('start', 'Начата загрузка всех таблиц')

            time.sleep(5)

            total_inserted = 0
            csv_reader = __import__('lib.csvreader', fromlist=['CSVReader']).CSVReader()
            table_loader = TableLoader(db, csv_reader)

            for config in TABLE_CONFIGS:
                try:
                    inserted = table_loader.load_table(config)
                    total_inserted += inserted
                    logger.info(f"{config.name} загружена успешно")
                except Exception as e:
                    logger.error(f"Ошибка загрузки {config.name}: {e}")
                    db.rollback()
                    raise
            logger.log('end', f'Загрузка завершена. Всего загружено строк: {total_inserted}')
    except Exception as e:
        error_msg = f"Ошибка при загрузке данных: {e}"
        if logger:
            logger.log('error', error_msg)
        raise e


if __name__ == '__main__':
    load_all_tables() 