import contextlib

import pymysql

from .config import DB_DATABASE, DB_HOSTNAME, DB_PASSWORD, DB_USERNAME


@contextlib.contextmanager
def get_connection():
    conn = pymysql.connect(host=DB_HOSTNAME,
                           user=DB_USERNAME,
                           password=DB_PASSWORD,
                           database=DB_DATABASE,
                           charset="utf8")
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
