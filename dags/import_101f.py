import os
import pandas as pd

from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}')

df = pd.read_csv('f101_round_f.csv', encoding='utf-8')

df.to_sql('dm_f101_round_f_v2', engine, schema='dm', if_exists='append', index=False)
print("Импорт завершён!")