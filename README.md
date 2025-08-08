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
- [/dags/fill_f101_round_f.py](/dags/fill_f101_round_f.py) - скрипт для заполнения витрины 101 формы
- [/dags/export_101f.py](/dags/export_101f.py) - скрипт для экспорта 101 формы в csv
- [/dags/import_101f.py](/dags/import_101f.py) - скрипт для импорта 101 формы в из csv в БД
- [/data/sql_init/create_dm_tables.sql](/data/sql_init/create_dm_tables.sql) - создание схемы витрин dm
- [/data/sql_init/create_ds_tables.sql](/data/sql_init/create_ds_tables.sql) - создание схемы данных ds
- [/data/sql_init/create_logs_tables.sql](/data/sql_init/create_logs_tables.sql) - создание схемы логов logs
- [/data/sql_init/create_logs_tables.sql](/data/sql_init/create_user.sql) - создание пользователей схем
- [/data/sql_scripts/dm_1.sql](/data/sql_init/dm_1.sql) - создание процедуры для расчета оборотов по лицевым счетам за диапазон дат
- [/data/sql_scripts/dm_2.sql](/data/sql_init/dm_2.sql) - создание процедуры для заполнения таблицы остатков на лицевых счетах за определенную дату
- [/data/sql_scripts/dm_3.sql](/data/sql_init/dm_3.sql) - создание процедуры для расчета остатков на лицевых счетах за диапазон дат
- [/data/sql_scripts/dm_4.sql](/data/sql_init/dm_4.sql) - создание процедуры для расчета 101 формы
- [/lib/csvreader.py](/lib/csvreader.py) - класс для чтения файлов csv
- [/lib/database.py](/lib/database.py) - класс для работы с БД
- [/lib/helper.py](/lib/helper.py) - класс с вспомогательными функциями
- [/lib/logger.py](/lib/logger.py) - класс для работы с таблицей логов
- [/lib/tableconfig.py](/lib/tableconfig.py) - класс для работы с конфигурациями таблиц
- [/lib/tableloader.py](/lib/tableloader.py) - класс для выполнения импорта из данных csv в БД
- [/tables/f101_round_f.csv](/tables/f101_round_f.csv) - таблица импорта для задания 1.4

## Ссылки на видео

[Ссылка на видео по заданию 1.1](https://disk.yandex.ru/i/qnzUkkgsK8BWaw)

[Ссылка на видео по заданию 1.2](https://disk.yandex.ru/i/CT0jA5SyS8rNKw)

[Ссылка на видео по заданию 1.3](https://disk.yandex.ru/i/MH8dxBXvtoBYRg)

[Ссылка на видео по заданию 1.4](https://disk.yandex.ru/i/ZiODPjqDZaGV7g)

Простите за фоновый шум =(


*Версия со Spark

Spark master - localhost:8081
Jupyter - localhost:8888