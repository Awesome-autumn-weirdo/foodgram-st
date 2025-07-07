import time
import psycopg2
from psycopg2 import OperationalError
import os

DB_HOST = os.getenv('DB_HOST', 'db')
DB_PORT = os.getenv('DB_PORT', 5432)
DB_NAME = os.getenv('POSTGRES_DB', 'db')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'hope120887')

def wait_for_postgres():
    while True:
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
            )
            conn.close()
            print("✅ PostgreSQL is ready!")
            break
        except OperationalError:
            print("⏳ Waiting for PostgreSQL...")
            time.sleep(1)

if __name__ == '__main__':
    wait_for_postgres()
