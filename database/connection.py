import os
import pymysql

from config import (
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_USER,
    MYSQL_DATABASE
)


def get_connection():
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=os.environ["SJB_MYSQL_PASSWORD"],
        database=MYSQL_DATABASE,
        charset="utf8mb4",
        autocommit=False
    )
    return conn
