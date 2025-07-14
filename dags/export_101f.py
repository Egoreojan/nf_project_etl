import os
import pandas as pd

from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}')

df = pd.read_sql('SELECT * FROM dm.dm_f101_round_f', engine)

df.to_csv('f101_round_f.csv', index=False, encoding='utf-8')
print("Экспорт завершён!")