import asyncio
import asyncpg
import psycopg2

creds = [
    ("nexorux", "nexorux123"),
    ("postgres", "postgres"),
    ("postgres", ""),
    ("postgres", "root"),
    ("postgres", "admin"),
    ("postgres", None),
    ("nexorux", "password"),
]

for user, password in creds:
    print(f"Testing psycopg2 user={user!r} password={password!r}")
    try:
        dsn = {
            'dbname': 'postgres',
            'user': user,
            'host': '127.0.0.1',
            'port': 5432,
        }
        if password is not None:
            dsn['password'] = password
        conn = psycopg2.connect(**dsn)
        print('  psycopg2 ok')
        conn.close()
    except Exception as exc:
        print('  psycopg2 failed:', repr(exc))

async def test_async():
    for user, password in creds:
        print(f"Testing asyncpg user={user!r} password={password!r}")
        try:
            conn = await asyncpg.connect(user=user, password=password or '', database='postgres', host='127.0.0.1', port=5432)
            print('  asyncpg ok')
            await conn.close()
        except Exception as exc:
            print('  asyncpg failed:', repr(exc))

asyncio.run(test_async())
