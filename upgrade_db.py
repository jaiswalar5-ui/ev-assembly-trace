import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Optional

def upgrade_db(database_path: Optional[Path] = None):
    if database_path is None:
        database_path = Path(__file__).resolve().parent / 'instance' / 'smart_assembly.db'
    if not database_path.is_file():
        raise FileNotFoundError(f'Database not found: {database_path}')

    with closing(sqlite3.connect(database_path)) as conn:
        with conn:
            migrations = {
                'batches': {'product_type': 'VARCHAR(100)'},
                'products': {
                    'current_station': "VARCHAR(100) DEFAULT 'Registration'",
                    'result': "VARCHAR(50) DEFAULT 'Pending'",
                },
            }

            for table, columns in migrations.items():
                existing_columns = {
                    row[1] for row in conn.execute(f'PRAGMA table_info({table})')
                }
                for column, definition in columns.items():
                    if column not in existing_columns:
                        conn.execute(
                            f'ALTER TABLE {table} ADD COLUMN {column} {definition}'
                        )

            for column in ('status', 'current_station', 'result'):
                conn.execute(
                    f'CREATE INDEX IF NOT EXISTS ix_products_{column} '
                    f'ON products ({column})'
                )

if __name__ == '__main__':
    upgrade_db()
    print("DB upgraded")
