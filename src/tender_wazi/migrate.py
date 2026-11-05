import os
import pathlib

import psycopg

MIGRATIONS = pathlib.Path(__file__).resolve().parents[2] / "sql" / "migrations"


def migrate(dsn: str) -> None:
    """Apply every sql/migrations/*.sql file in order, once each."""
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                " filename text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
            )
            conn.commit()
            cur.execute("SELECT filename FROM schema_migrations")
            done = {row[0] for row in cur.fetchall()}
            for path in sorted(MIGRATIONS.glob("*.sql")):
                if path.name in done:
                    continue
                cur.execute(path.read_text())
                cur.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,)
                )
                conn.commit()
                print(f"applied {path.name}")


if __name__ == "__main__":
    migrate(os.environ["DATABASE_URL_DIRECT"])
