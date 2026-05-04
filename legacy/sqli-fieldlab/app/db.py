from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import pymysql
from pymysql.constants import CLIENT
from sqlalchemy import create_engine

from config import Config


def mysql_connection(allow_multi: bool = False) -> pymysql.connections.Connection:
    client_flag = CLIENT.MULTI_STATEMENTS if allow_multi else 0
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        client_flag=client_flag,
    )


@contextmanager
def get_cursor(allow_multi: bool = False):
    connection = mysql_connection(allow_multi=allow_multi)
    cursor = connection.cursor()
    try:
        yield connection, cursor
    finally:
        cursor.close()
        connection.close()


def run_select(sql: str, args: tuple[Any, ...] | None = None, allow_multi: bool = False):
    with get_cursor(allow_multi=allow_multi) as (_connection, cursor):
        cursor.execute(sql, args)
        return cursor.fetchall() if cursor.description else []


def run_statement(sql: str, args: tuple[Any, ...] | None = None, allow_multi: bool = False) -> int:
    with get_cursor(allow_multi=allow_multi) as (_connection, cursor):
        cursor.execute(sql, args)
        return cursor.rowcount


def run_multi_statement(sql: str):
    results: list[Any] = []
    with get_cursor(allow_multi=True) as (_connection, cursor):
        cursor.execute(sql)
        while True:
            if cursor.description:
                results.append(cursor.fetchall())
            else:
                results.append({"affected_rows": cursor.rowcount})
            if not cursor.nextset():
                break
    return results


engine = create_engine(Config.SQLALCHEMY_URI, pool_pre_ping=True, future=True)
