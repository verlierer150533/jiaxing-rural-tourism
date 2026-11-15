# -*- coding: utf-8 -*-
"""项目全局配置：Flask + SQLAlchemy + JWT + SocketIO + MySQL + Redis。

所有配置项均支持环境变量覆盖，默认值对应本地开发环境：
    MySQL  root / 空密码 / 127.0.0.1:3306 / jiaxing_rural
    Redis  127.0.0.1:6379 / db0
"""
import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """基础配置。"""

    # ---------------- 基础 ----------------
    SECRET_KEY = os.getenv("SECRET_KEY", "jiaxing-rural-tourism-secret-key-2027")
    JSON_AS_ASCII = False  # 中文直接输出，不转成 \uXXXX

    # ---------------- MySQL ----------------
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "jiaxing_rural")

    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}?charset=utf8mb4".format(
            user=MYSQL_USER,
            pwd=MYSQL_PASSWORD,
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            db=MYSQL_DATABASE,
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,   # 取连接前探活，避免 MySQL 8 空闲 8h 断连
        "pool_recycle": 280,
        "pool_size": 10,
        "max_overflow": 20,
    }

    # ---------------- Redis ----------------
    REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None
    REDIS_URL = "redis://{host}:{port}/{db}".format(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB
    )

    # ---------------- JWT ----------------
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY", "jiaxing-rural-tourism-jwt-secret-2027"
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_ERROR_MESSAGE_KEY = "message"

    # ---------------- SocketIO ----------------
    SOCKETIO_ASYNC_MODE = os.getenv("SOCKETIO_ASYNC_MODE", "eventlet")
    SOCKETIO_CORS_ORIGINS = "*"

    # ---------------- 上传 ----------------
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # ---------------- 分页 ----------------
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100


class DevelopmentConfig(Config):
    """开发环境。"""

    DEBUG = True


class ProductionConfig(Config):
    """生产环境。"""

    DEBUG = False


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(name=None):
    """按名称取配置类，默认 development。"""
    name = name or os.getenv("FLASK_ENV", "development")
    return CONFIG_MAP.get(name, DevelopmentConfig)
