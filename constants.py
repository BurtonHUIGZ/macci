# -*- encoding: utf-8 -*-
"""
@File    : constants.py
@Time    : 2020/9/18 10:38
@Author  : macci
@Site   : 
@Software: PyCharm
"""

import os
import socket
DEBUG = False
ABS_PATH = os.path.dirname(os.path.abspath(__file__))

LOG_DIR = os.path.join(ABS_PATH, "logger")

MASTER_DATABASE_ENGINE = "django.db.backends.mysql"
MASTER_DATABASE_NAME = "macci"
MASTER_DATABASE_USER = "root"
MASTER_DATABASE_HOST = "localhost"
MASTER_DATABASE_PORT = 3306
MASTER_DATABASE_CONN_MAX_AGE = 0
LOG_DB_NAME = "maccilog"
MASTER_DATABASE_HOST_READ = "localhost"
MASTER_DATABASE_HOST_READ_SPECIAL = "localhost"
MASTER_DATABASE_HOST_WRITE = "localhost"
MASTER_DATABASE_PASSWORD = "123456"

CACHE_HOST = "localhost"
CACHE_PORT = 6379
CACHE_DB = 1
CACHE_PASSWORD = ""
CACHE_EXPIRE = 120
COOKIE_EXPIRE = 10 * 24 * 3600