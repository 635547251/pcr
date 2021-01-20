import contextlib
import logging

import pymysql

from .config import DB_DATABASE, DB_HOSTNAME, DB_PASSWORD, DB_USERNAME


@contextlib.contextmanager
def get_connection():
    '''
    建立数据库游标上下文
    '''
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


def get_pcr_team(start_time="2020-04-17"):
    '''
    获取数据库数据
    :param  start_time  开始日期
    '''
    with get_connection() as conn:
        with conn.cursor() as cursor:
            select_sql = '''
                    select ATTACK_TEAM, DEFENSE_TEAM, GOOD_COMMENT, BAD_COMMENT
                    from T_PCR_TEAM
                    where DEFENSE_TEAM in (
                        select DEFENSE_TEAM from T_PCR_TEAM where UPDATE_TIMESTAMP >= '%s' group by DEFENSE_TEAM having count(DEFENSE_TEAM) > 1)
                    and UPDATE_TIMESTAMP >= '%s'
                '''
            try:
                cursor.execute(select_sql % (start_time, start_time))
                return cursor.fetchall()
            except Exception as e:
                print(e)
                raise


def insert_team(params: list[dict[str, str]]):
    '''
    插入数据
    :params  参数列表
    '''
    conn = get_connection()
    with get_connection() as conn:
        with conn.cursor() as cursor:
            insert_sql = '''
                    insert into
                        T_PCR_TEAM (ATTACK_TEAM, DEFENSE_TEAM, GOOD_COMMENT, BAD_COMMENT,
                            CREATE_TIMESTAMP, UPDATE_TIMESTAMP)
                    values
                        (%(ATTACK_TEAM)s, %(DEFENSE_TEAM)s, %(GOOD_COMMENT)s,
                        %(BAD_COMMENT)s, %(CREATE_TIMESTAMP)s, current_timestamp())
                    on duplicate key update
                        GOOD_COMMENT = %(GOOD_COMMENT)s,
                        BAD_COMMENT = %(BAD_COMMENT)s,
                        UPDATE_TIMESTAMP = current_timestamp()
                '''
            try:
                cursor.executemany(insert_sql, params)
                conn.commit()
                logging.info("插入表T_TEAM完成")
            except Exception as e:
                logging.error(e)
                # conn.rollback()
                raise
