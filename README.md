# ETL Проект с Airflow

Этот проект демонстрирует настройку ETL процесса для загрузки данных из CSV файлов в PostgreSQL с использованием Apache Airflow.

## Запуск

```bash
docker compose up -d --build
```

## Используемый стек

- Docker
- Python
- PostgreSQL
- Airflow

## Структура проекта

- [/dags](/dags/) - папка с python скриптами
- [/dags/etl_all_tables_dag.py](/dags/etl_all_tables_dag.py) - даг для импорта csv файлов в БД
- [/dags/etl_loader_all_tables.py](/dags/etl_loader_all_tables.py) - скрипт для импорта файлов csv в БД
- [/dags/prefill_dm_account_balance_f.py](/dags/prefill_dm_account_balance_f.py) - скрипт для предзаполнения витрины dm_account_balance
- [/dags/fill_dm_account_balance_f.py](/dags/fill_dm_account_balance_f.py) - скрипт для заполнения витрины dm_account_balance
- [/dags/fill_dm_account_turnover_f.py](/dags/fill_dm_account_turnover_f.py) - скрипт для заполнения витрины dm_account_turnover

## Ссылки на видео

[Ссылка на видео по заданию 1.1](https://disk.yandex.ru/i/qnzUkkgsK8BWaw)

Простите за фоновый шум =(