from lib.tableconfig import TableConfig
from lib.csvreader import CSVReader
from lib.helper import Helper

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class TableLoader:
    def __init__(self, db, csv_reader):
        self.db = db
        self.csv_reader = csv_reader

    def load_table(self, config: TableConfig) -> int:
        logger.info(f"Начата загрузка {config.name}")
        
        if hasattr(config, 'encoding') and config.encoding:
            df = self.csv_reader.read(config.file_path, encoding=config.encoding)
        else:
            df = self.csv_reader.read(config.file_path)
        logger.info(f"Прочитано {len(df)} строк из {config.name}")
        
        df = Helper.transform_dataframe(df, config.date_columns)
        
        if config.custom_transform:
            df = config.custom_transform(df)
        
        if config.clear_before_load:
            self.db.execute(f"DELETE FROM ds.\"{config.table_name}\"")
            logger.info(f"Таблица {config.table_name} очищена")
        
        if config.name == "MD_CURRENCY_D":
            logger.warning(f"Колонки DataFrame: {list(df.columns)}")
            for col in ['CURRENCY_CODE', 'CODE_ISO_CHAR']:
                if col in df.columns:
                    logger.warning(f"Все значения в колонке {col}:")
                    for val in df[col].unique():
                        logger.warning(f"'{val}' (длина: {len(str(val))})")
        
        columns = list(df.columns)
        placeholders = ', '.join(['%s'] * len(columns))
        column_names = ', '.join([col.lower() for col in columns])
        
        if config.conflict_columns:
            conflict_columns_str = ', '.join([col for col in config.conflict_columns])
            update_columns = [col for col in columns if col not in config.conflict_columns]
            if update_columns:
                set_clause = ', '.join([f"{col.lower()} = EXCLUDED.{col.lower()}" for col in update_columns])
                conflict_clause = f"ON CONFLICT ({conflict_columns_str}) DO UPDATE SET {set_clause}"
            else:
                conflict_clause = f"ON CONFLICT ({conflict_columns_str}) DO NOTHING"
        else:
            conflict_clause = ""
        insert_sql = f"""
            INSERT INTO ds.{config.table_name} ({column_names})
            VALUES ({placeholders})
            {conflict_clause}
        """
        
        inserted_count = 0
        try:
            for _, row in df.iterrows():
                values = []
                for col in columns:
                    value = row[col]
                    if pd.isna(value):
                        values.append(None)
                    elif isinstance(value, (int, float, str)):
                        values.append(value)
                    else:
                        values.append(str(value))

                if config.name == "MD_CURRENCY_D":
                    for col, val in zip(columns, values):
                        if col in ['CURRENCY_CODE', 'CODE_ISO_CHAR'] and isinstance(val, str) and len(val) > 3:
                            logger.error(f"Значение для {col}: '{val}' (длина: {len(val)})")
                self.db.cursor.execute(insert_sql, values)
                inserted_count += 1
            self.db.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при вставке строки в {config.name}: {e}")
            self.db.rollback()
            raise
        
        logger.info(f"{config.name}: загружено {inserted_count} строк из {len(df)}")
        return inserted_count