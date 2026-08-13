import os
import sys

print('cwd', os.getcwd())
print('python', sys.executable)
print('default encoding', sys.getdefaultencoding())
print('filesystem encoding', sys.getfilesystemencoding())

try:
    import psycopg2
    print('psycopg2 version', psycopg2.__version__)
except Exception as exc:
    print('psycopg2 import failed:', exc)
    raise

try:
    conn = psycopg2.connect(dbname='nexorux_dev', user='nexorux', password='nexorux123', host='127.0.0.1', port=5432)
    print('psycopg2 connected')
    conn.close()
except Exception as exc:
    print('psycopg2 connect failed:', repr(exc))

try:
    import asyncpg
    print('asyncpg version', asyncpg.__version__)
except Exception as exc:
    print('asyncpg import failed:', exc)
    raise

import asyncio

async def test_asyncpg():
    try:
        conn = await asyncpg.connect(user='nexorux', password='nexorux123', database='nexorux_dev', host='127.0.0.1', port=5432)
        print('asyncpg connected')
        await conn.close()
    except Exception as exc:
        print('asyncpg connect failed:', repr(exc))

asyncio.run(test_asyncpg())
