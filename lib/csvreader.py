import pandas as pd
import chardet
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CSVReader:
    def __init__(self):
        self.df = None
        self.encodings_to_try = ['cp1251', 'utf-8', 'latin1', 'iso-8859-1', 'windows-1252']

    @staticmethod
    def detect_encoding(file_path: str):
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                confidence = result['confidence']
                logger.info(f"Определена кодировка: {encoding} (уверенность: {confidence:.2f})")
                return encoding
        except Exception as e:
            logger.warning(f"Не удалось определить кодировку автоматически: {e}")
            return None

    def read(self, file_path: str, sep=';'):
        detected_encoding = CSVReader.detect_encoding(file_path)
        if detected_encoding and detected_encoding not in self.encodings_to_try:
            self.encodings_to_try.insert(0, detected_encoding)

        for encoding in self.encodings_to_try:
            try:
                df = pd.read_csv(file_path, sep=sep, encoding=encoding)
                logger.info(f"Файл {file_path} успешно прочитан с кодировкой {encoding}")
                return df
            except UnicodeDecodeError as e:
                logger.warning(f"Ошибка кодировки {encoding} для {file_path}: {e}")
                continue
            except Exception as e:
                logger.error(f"Ошибка чтения файла {file_path} с кодировкой {encoding}: {e}")
                continue

        try:
            df = pd.read_csv(file_path, sep=sep, encoding='utf-8')
            logger.warning(f"Файл {file_path} прочитан с кодировкой utf-8. Возможна потеря данных!")
            return df
        except Exception as e:
            logger.error(f"Критическая ошибка чтения файла {file_path}: {e}")
            raise