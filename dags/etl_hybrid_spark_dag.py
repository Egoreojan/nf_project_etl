from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from lib.database import PostgresDB
from lib.csvreader import CSVReader
from lib.tableloader import TableLoader
from lib.spark_tableloader import SparkTableLoader, HybridTableLoader
from lib.tableconfig import TableConfig
from lib.logger import Logger
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROCESS_NAME = 'ETL_HYBRID_SPARK_LOAD'

# Функции очистки данных (из оригинального DAG)
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

# Конфигурации таблиц (те же, что и в оригинальном DAG)
TABLE_CONFIGS = [
    TableConfig(
        name="MD_LEDGER_ACCOUNT_S", 
        file_path="/opt/airflow/data/tables/md_ledger_account_s.csv",
        table_name="md_ledger_account_s",
        conflict_columns=['ledger_account', 'start_date'],
        custom_transform=clean_ledger_account_char_columns
    ),
    
    TableConfig(
        name="MD_CURRENCY_D",
        file_path="/opt/airflow/data/tables/md_currency_d.csv", 
        table_name="md_currency_d",
        conflict_columns=['currency_rk', 'data_actual_date'],
        custom_transform=clean_currency_code_columns
    ),
    
    TableConfig(
        name="MD_EXCHANGE_RATE_D",
        file_path="/opt/airflow/data/tables/md_exchange_rate_d.csv",
        table_name="md_exchange_rate_d",
        date_columns={
            'DATA_ACTUAL_DATE': 'DD-MM-YYYY'
        },
        conflict_columns=['data_actual_date', 'currency_rk']
    ),
    
    TableConfig(
        name="MD_ACCOUNT_D",
        file_path="/opt/airflow/data/tables/md_account_d.csv",
        table_name="md_account_d", 
        date_columns={
            'DATA_ACTUAL_DATE': 'DD-MM-YYYY',
            'DATA_ACTUAL_END_DATE': 'DD-MM-YYYY'
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
            'ON_DATE': 'DD-MM-YYYY'
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
        conflict_columns=[],
        clear_before_load=True
    )
]

def load_all_tables_hybrid():
    """Гибридная загрузка таблиц через pandas и Spark"""
    db = None
    etl_logger = None
    spark_loader = None
    
    try:
        # Подключение к БД
        with PostgresDB(
            os.getenv("DB_NAME", "postgres"), 
            os.getenv("DB_USER", "postgres"), 
            os.getenv("DB_PASSWORD", "postgres"), 
            os.getenv("DB_HOST", "postgres"), 
            os.getenv("DB_PORT", "5432")
        ) as db:
            etl_logger = Logger(db, PROCESS_NAME)
            etl_logger.log('start', 'Начата гибридная загрузка всех таблиц (pandas + Spark)')
            
            # Создание загрузчиков
            csv_reader = CSVReader()
            pandas_loader = TableLoader(db, csv_reader)
            
            # Создание Spark загрузчика
            spark_loader = SparkTableLoader()
            
            # Создание гибридного загрузчика
            hybrid_loader = HybridTableLoader(
                pandas_loader=pandas_loader,
                spark_loader=spark_loader,
                size_threshold_mb=5  # Файлы больше 5MB загружаем через Spark
            )
            
            total_inserted = 0
            performance_stats = []
            
            for config in TABLE_CONFIGS:
                try:
                    start_time = datetime.now()
                    
                    # Определяем размер файла для статистики
                    file_size_mb = os.path.getsize(config.file_path) / (1024 * 1024)
                    
                    # Загрузка через гибридный загрузчик
                    inserted = hybrid_loader.load_table(config)
                    
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    # Собираем статистику
                    performance_stats.append({
                        'table': config.name,
                        'size_mb': file_size_mb,
                        'rows': inserted,
                        'duration_sec': duration,
                        'rows_per_sec': inserted / duration if duration > 0 else 0
                    })
                    
                    total_inserted += inserted
                    logger.info(f"{config.name} загружена успешно: {inserted} строк за {duration:.2f}с")
                    
                except Exception as e:
                    logger.error(f"Ошибка загрузки {config.name}: {e}")
                    if etl_logger:
                        etl_logger.log('error', f"Ошибка загрузки {config.name}: {e}")
                    raise
            
            # Логируем статистику производительности
            etl_logger.log('info', f'Статистика производительности:')
            for stat in performance_stats:
                etl_logger.log('info', 
                    f"{stat['table']}: {stat['size_mb']:.1f}MB, "
                    f"{stat['rows']} строк, {stat['duration_sec']:.2f}с, "
                    f"{stat['rows_per_sec']:.0f} строк/сек"
                )
            
            etl_logger.log('end', f'Гибридная загрузка завершена. Всего загружено строк: {total_inserted}')
            
    except Exception as e:
        error_msg = f"Ошибка при гибридной загрузке данных: {e}"
        if etl_logger:
            etl_logger.log('error', error_msg)
        logger.error(error_msg)
        raise e
    finally:
        # Закрываем Spark сессию
        if spark_loader:
            spark_loader.close()

def load_big_tables_spark_only():
    """Загрузка только больших таблиц через Spark (для тестирования)"""
    spark_loader = None
    
    try:
        # Создание Spark загрузчика
        spark_loader = SparkTableLoader()
        
        # Загружаем только большие таблицы
        big_tables = [config for config in TABLE_CONFIGS 
                     if config.table_name in ['ft_posting_f', 'ft_balance_f']]
        
        total_inserted = 0
        
        for config in big_tables:
            try:
                start_time = datetime.now()
                inserted = spark_loader.load_table(config)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                total_inserted += inserted
                logger.info(f"Spark: {config.name} - {inserted} строк за {duration:.2f}с")
                
            except Exception as e:
                logger.error(f"Ошибка Spark-загрузки {config.name}: {e}")
                raise
        
        logger.info(f"Spark-загрузка завершена. Всего: {total_inserted} строк")
        
    except Exception as e:
        logger.error(f"Ошибка при Spark-загрузке: {e}")
        raise e
    finally:
        if spark_loader:
            spark_loader.close()

# Определение DAG
default_args = {
    'owner': 'egor',
    'retries': 1,
    'retry_delay': timedelta(minutes=2)
}

with DAG(
    dag_id='etl_hybrid_spark_dag',
    default_args=default_args,
    description='Гибридная загрузка таблиц: pandas для справочников, Spark для больших таблиц',
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,  # Запуск по требованию
    catchup=False,
    tags=['etl', 'spark', 'hybrid', 'performance']
) as dag:

    # Основная задача - гибридная загрузка
    hybrid_load_task = PythonOperator(
        task_id='hybrid_load_all_tables',
        python_callable=load_all_tables_hybrid,
        doc_md="""
        ## Гибридная загрузка данных
        
        Этот таск использует интеллектуальный выбор между pandas и Spark:
        - **Справочники (маленькие)** → pandas
        - **Фактовые таблицы (большие)** → Spark
        - **Автоматический выбор** по размеру файла (порог 5MB)
        
        ### Преимущества:
        - Оптимальная производительность для каждого типа данных
        - Сбор статистики производительности
        - Совместимость с существующим кодом
        """
    )
    
    # Дополнительная задача - только Spark (для тестирования)
    spark_only_task = PythonOperator(
        task_id='spark_only_big_tables', 
        python_callable=load_big_tables_spark_only,
        doc_md="""
        ## Загрузка только через Spark
        
        Загружает только большие таблицы (ft_posting_f, ft_balance_f) через Spark.
        Используется для:
        - Тестирования производительности Spark
        - Сравнения с pandas
        - Отладки Spark jobs
        """
    )

    # Задачи можно запускать независимо
    [hybrid_load_task, spark_only_task]
