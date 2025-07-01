import psycopg2

class PostgresDB:
    def __init__(self, dbname, user, password, host='localhost', port=5432):
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.cursor = self.conn.cursor()

    def execute(self, query, params=None):
        """Выполнить запрос без возврата результата (INSERT, UPDATE, DELETE)."""
        self.cursor.execute(query, params or ())
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def fetchall(self, query, params=None):
        """Выполнить SELECT и вернуть все строки результата."""
        self.cursor.execute(query, params or ())
        return self.cursor.fetchall()

    def fetchone(self, query, params=None):
        """Выполнить SELECT и вернуть одну строку результата."""
        self.cursor.execute(query, params or ())
        return self.cursor.fetchone()

    def close(self):
        """Закрыть соединение с базой данных."""
        self.cursor.close()
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
