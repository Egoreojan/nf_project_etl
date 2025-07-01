from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Logger:
    def  __init__(self, db, process_name):
        self.db = db
        self.process_name = process_name

        try:
            self.db.execute("SELECT 1 FROM logs.etl_log LIMIT 1;")
        except Exception as e:
            logger.warning(f"Таблица логов не найдена или недоступна: {e}")

    def log(self, status: str, message: Optional[str] = None):
        try:
            if status == 'start':
                self.db.execute("""
                    INSERT INTO logs.etl_log (process_name, status, message)
                    VALUES (%s, 'start', %s)
                """, (self.process_name, message))
            elif status in ['end', 'error']:
                self.db.execute("""
                    UPDATE logs.etl_log
                    SET status = %s, end_time = CURRENT_TIMESTAMP, message = %s
                    WHERE process_name = %s AND status = 'start'
                    AND id = (SELECT id FROM logs.etl_log 
                            WHERE process_name = %s AND status = 'start' 
                            ORDER BY start_time DESC LIMIT 1)
                """, (status, message, self.process_name, self.process_name))
        except Exception as e:
            logger.error(f"Ошибка при логировании: {e}")

    def info(self, msg):
        logger.info(msg)

    def error(self, msg):
        logger.error(msg)

