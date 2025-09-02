import sqlite3
from sqlite3 import Connection

db_path = "alarm_data.db"


def create_table(conn: Connection, table_name: str) -> None:
    with conn:
        conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS f{table_name}(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag TEXT NOT NULL,
                    lv TEXT NOT NULL,
                    en TEXT NOT NULL
                    )
                    """)


def close_db(conn: Connection) -> None:
    conn.close()


def get_db(db_path: str) -> Connection:
    # Connect to the database (creates if it doesn't exist)
    return sqlite3.connect(db_path)
