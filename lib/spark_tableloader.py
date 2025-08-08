from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from lib.tableconfig import TableConfig
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SparkTableLoader:
    def __init__(self, spark_session=None, db_config=None):
        """
        Инициализация SparkTableLoader
        
        Args:
            spark_session: Сессия Spark (если None, создается новая)
            db_config: Конфигурация подключения к БД
        """
        if spark_session is None:
            master_url = os.getenv("SPARK_MASTER", "local[*]")
            self.spark = (
                SparkSession.builder
                .appName("ETL_Data_Loader")
                .master(master_url)
                .config("spark.sql.adaptive.enabled", "true")
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
                # JDBC драйвер Postgres через Maven-пакет
                .config("spark.jars.packages", os.getenv("SPARK_JARS_PACKAGES", "org.postgresql:postgresql:42.7.3"))
                .config("spark.ui.enabled", os.getenv("SPARK_UI_ENABLED", "false"))
                .getOrCreate()
            )
        else:
            self.spark = spark_session
            
        self.db_config = db_config or {
            "url": "jdbc:postgresql://postgres:5432/postgres",
            "user": "postgres", 
            "password": "postgres",
            "driver": "org.postgresql.Driver"
        }
        
    def load_table(self, config: TableConfig) -> int:
        """
        Загрузка таблицы через Spark
        
        Args:
            config: Конфигурация таблицы
            
        Returns:
            Количество загруженных строк
        """
        logger.info(f"Начата Spark-загрузка {config.name}")
        
        try:
            # Чтение CSV через Spark
            df = self._read_csv_spark(config)
            row_count = df.count()
            logger.info(f"Прочитано {row_count} строк из {config.name} через Spark")
            
            # Трансформация данных
            df = self._transform_dataframe_spark(df, config)
            
            # Применение кастомных трансформаций
            if hasattr(config, 'custom_transform') and config.custom_transform:
                logger.warning(f"Кастомные трансформации для {config.name} пропущены (требуют адаптации для Spark)")
            
            # Очистка таблицы если необходимо
            if config.clear_before_load:
                self._clear_table(config.table_name)
                logger.info(f"Таблица {config.table_name} очищена")
            
            # Запись в PostgreSQL
            final_count = self._write_to_postgres(df, config)
            
            logger.info(f"Spark: {config.name} - загружено {final_count} строк")
            return final_count
            
        except Exception as e:
            logger.error(f"Ошибка при Spark-загрузке {config.name}: {e}")
            raise
    
    def _read_csv_spark(self, config: TableConfig):
        """Чтение CSV файла через Spark"""
        # Базовые опции для чтения CSV
        options = {
            "header": "true",
            "inferSchema": "true", 
            "sep": ";"
        }
        
        # Добавляем encoding только если он указан и не пустой
        if hasattr(config, 'encoding') and config.encoding:
            options["encoding"] = config.encoding
        
        return self.spark.read.options(**options).csv(config.file_path)
    
    def _transform_dataframe_spark(self, df, config: TableConfig):
        """Трансформация DataFrame в Spark"""
        # Преобразование дат
        if hasattr(config, 'date_columns') and config.date_columns:
            for col_name, date_format in config.date_columns.items():
                if col_name in df.columns:
                    # Конвертация формата даты из pandas в Spark
                    spark_format = self._convert_date_format(date_format)
                    try:
                        # Пробуем преобразовать дату
                        df = df.withColumn(col_name, 
                                         to_date(col(col_name), spark_format))
                        logger.info(f"Преобразована дата в колонке {col_name} с форматом {spark_format}")
                    except Exception as e:
                        logger.warning(f"Не удалось преобразовать дату в колонке {col_name}: {e}")
                        # Если не получается, оставляем как есть
                        continue
        
        # Очистка колонок от лишних пробелов
        for col_name in df.columns:
            if dict(df.dtypes)[col_name] == 'string':
                df = df.withColumn(col_name, trim(col(col_name)))
        
        # Проверяем на NULL в критических колонках
        if config.table_name == "ft_balance_f":
            # Убираем строки с NULL в on_date
            null_count = df.filter(col("on_date").isNull()).count()
            if null_count > 0:
                logger.warning(f"Обнаружено {null_count} строк с NULL в on_date, удаляем их")
                df = df.filter(col("on_date").isNotNull())
        
        return df
    
    def _convert_date_format(self, pandas_format):
        """Конвертация формата даты из pandas в Spark"""
        format_mapping = {
            'DD-MM-YYYY': 'dd-MM-yyyy',
            'YYYY-MM-DD': 'yyyy-MM-dd',
            'MM/DD/YYYY': 'MM/dd/yyyy'
        }
        return format_mapping.get(pandas_format, pandas_format)
    
    def _clear_table(self, table_name):
        """Очистка таблицы - заглушка, фактическая очистка будет через mode='overwrite'"""
        logger.info(f"Таблица {table_name} будет очищена при записи (mode=overwrite)")
    
    def _write_to_postgres(self, df, config: TableConfig):
        """Запись DataFrame в PostgreSQL"""
        # Подготовка опций записи
        write_options = {
            **self.db_config,
            "dbtable": f'ds.{config.table_name}',
            "batchsize": 10000,  # Размер batch для вставки
            "isolationLevel": "READ_COMMITTED"
        }
        
        # Определение режима записи
        if config.clear_before_load:
            mode = "overwrite"
            logger.info(f"Используется режим overwrite для {config.name}")
        elif config.conflict_columns:
            # Для upsert нужна более сложная логика
            mode = "append"
            logger.warning(f"UPSERT для {config.name} не реализован, используется append")
        else:
            mode = "append"
        
        # Запись данных
        df.write \
            .format("jdbc") \
            .options(**write_options) \
            .mode(mode) \
            .save()
        
        return df.count()
    
    def close(self):
        """Закрытие Spark сессии"""
        if self.spark:
            self.spark.stop()
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class HybridTableLoader:
    """
    Гибридный загрузчик, который выбирает между pandas и Spark
    в зависимости от размера файла и типа таблицы
    """
    
    def __init__(self, pandas_loader, spark_loader, size_threshold_mb=10):
        """
        Args:
            pandas_loader: Экземпляр обычного TableLoader
            spark_loader: Экземпляр SparkTableLoader  
            size_threshold_mb: Порог размера файла для переключения на Spark (МБ)
        """
        self.pandas_loader = pandas_loader
        self.spark_loader = spark_loader
        self.size_threshold_mb = size_threshold_mb
        
        # Таблицы, которые всегда загружаем через Spark
        self.force_spark_tables = {
            'ft_posting_f',  # Основная таблица проводок
            'ft_balance_f'   # Остатки по счетам
        }
        
        # Справочники всегда через pandas
        self.force_pandas_tables = {
            'md_currency_d',
            'md_account_d', 
            'md_ledger_account_s',
            'md_exchange_rate_d'
        }
    
    def load_table(self, config: TableConfig) -> int:
        """Выбор загрузчика и загрузка таблицы"""
        
        # Проверяем принудительные правила
        if config.table_name in self.force_spark_tables:
            logger.info(f"Принудительная загрузка {config.name} через Spark")
            return self.spark_loader.load_table(config)
            
        if config.table_name in self.force_pandas_tables:
            logger.info(f"Принудительная загрузка {config.name} через pandas")
            return self.pandas_loader.load_table(config)
        
        # Проверяем размер файла
        try:
            import os
            file_size_mb = os.path.getsize(config.file_path) / (1024 * 1024)
            
            if file_size_mb > self.size_threshold_mb:
                logger.info(f"Файл {config.name} ({file_size_mb:.1f}MB) загружается через Spark")
                return self.spark_loader.load_table(config)
            else:
                logger.info(f"Файл {config.name} ({file_size_mb:.1f}MB) загружается через pandas")
                return self.pandas_loader.load_table(config)
                
        except Exception as e:
            logger.warning(f"Ошибка определения размера {config.file_path}: {e}")
            logger.info(f"Загружаем {config.name} через pandas по умолчанию")
            return self.pandas_loader.load_table(config)
