import psycopg2
from psycopg2 import sql

PG_HOST = "127.0.0.1"
PG_PORT = 5432
PG_SUPERUSER = "postgres"
PG_DB = "postgres"
PG_USER = "nexorux"
PG_PASSWORD = "nexorux123"
PG_APP_DB = "nexorux_dev"


def main() -> None:
    print('Connecting to local Postgres as superuser...')
    conn = psycopg2.connect(dbname=PG_DB, user=PG_SUPERUSER, host=PG_HOST, port=PG_PORT)
    conn.autocommit = True

    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (PG_USER,))
        if cur.fetchone() is None:
            print(f"Creating role {PG_USER}")
            cur.execute(sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD %s").format(sql.Identifier(PG_USER)), [PG_PASSWORD])
        else:
            print(f"Altering existing role {PG_USER} password")
            cur.execute(sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD %s").format(sql.Identifier(PG_USER)), [PG_PASSWORD])

        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (PG_APP_DB,))
        if cur.fetchone() is None:
            print(f"Creating database {PG_APP_DB}")
            cur.execute(sql.SQL("CREATE DATABASE {} OWNER {};").format(sql.Identifier(PG_APP_DB), sql.Identifier(PG_USER)))
        else:
            print(f"Database {PG_APP_DB} already exists")

    conn.close()
    print('Postgres setup complete.')


if __name__ == '__main__':
    main()
