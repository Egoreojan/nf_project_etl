from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'egor',
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
    'start_date': datetime(2024, 1, 1)
}

with DAG(
    dag_id='unzip_files',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=['unzip', 'file processing']
) as dag:
    unzip_file = BashOperator(
        task_id='unzip_test_file',
        bash_command='''
            # Проверяем, где мы находимся
            pwd
            ls -la
            
            # Создаем директорию для разархивирования с правильными правами
            mkdir -p /tmp/extracted_files
            chmod 755 /tmp/extracted_files
            
            # Проверяем существование файла в правильном месте
            if [ -f /opt/airflow/data/test.zip ]; then
                echo "Файл test.zip найден в /opt/airflow/data/"
                cd /tmp/extracted_files
                unzip /opt/airflow/data/test.zip
                echo "Файл успешно разархивирован в /tmp/extracted_files/"
                ls -la
            elif [ -f /opt/airflow/test.zip ]; then
                echo "Файл test.zip найден в /opt/airflow/"
                cd /tmp/extracted_files
                unzip /opt/airflow/test.zip
                echo "Файл успешно разархивирован в /tmp/extracted_files/"
                ls -la
            else
                echo "Файл test.zip не найден"
                echo "Ищем файл в других местах..."
                find /opt/airflow -name "test.zip" 2>/dev/null || echo "Файл не найден"
                exit 1
            fi
        '''
    )
