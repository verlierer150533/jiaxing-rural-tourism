# -*- coding: utf-8 -*-
"""Redis 缓存工具。

设计原则：
    1. Redis 不可用时**绝不阻断业务**——所有读写失败都退化为“未命中”。
    2. 只缓存读多写少的数据（地图点位、筛选元数据），写操作后主动失效。
"""
import json
import time

import redis
from flask import current_app

_client = None
_last_attempt = 0.0
RETRY_INTERVAL = 5.0  # 连接失败后 5 秒内不再重试，避免每次请求都卡在超时上

KEY_MAP = "jrt:attraction:map"
KEY_META = "jrt:attraction:meta"
KEY_OVERVIEW = "jrt:stats:overview"


def get_redis():
    """惰性创建连接；不可用返回 None（带失败重试间隔）。"""
    global _client, _last_attempt

    if _client is not None:
        return _client

    now = time.time()
    if _last_attempt and (now - _last_attempt) < RETRY_INTERVAL:
        return None

    _last_attempt = now
    try:
        client = redis.Redis(
            host=current_app.config["REDIS_HOST"],
            port=current_app.config["REDIS_PORT"],
            db=current_app.config["REDIS_DB"],
            password=current_app.config["REDIS_PASSWORD"],
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
            protocol=2,  # 兼容 Redis 5.x（不支持 RESP3 的 HELLO 握手）
        )
        client.ping()
        _client = client
        current_app.logger.info("Redis 已连接：%s", current_app.config["REDIS_URL"])
    except Exception as exc:  # pragma: no cover - 依赖外部服务
        current_app.logger.warning("Redis 不可用，缓存降级：%s", exc)
        _client = None
    return _client


def redis_alive():
    """健康检查：真发一次 PING，失败则丢弃单例等待下一轮重连。"""
    global _client, _last_attempt

    client = get_redis()
    if client is None:
        return False
    try:
        return bool(client.ping())
    except Exception:
        _client = None
        _last_attempt = time.time()
        return False


def cache_get(key):
    """读缓存，未命中或异常返回 None。"""
    client = get_redis()
    if client is None:
        return None
    try:
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except Exception:  # pragma: no cover
        return None


def cache_set(key, value, ttl=60):
    """写缓存，失败忽略。"""
    client = get_redis()
    if client is None:
        return False
    try:
        client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
        return True
    except Exception:  # pragma: no cover
        return False


def cache_delete(*keys):
    """删除指定缓存键。"""
    client = get_redis()
    if client is None:
        return 0
    try:
        return client.delete(*keys)
    except Exception:  # pragma: no cover
        return 0


def invalidate_attraction_cache():
    """资源数据变更后失效相关缓存。"""
    return cache_delete(KEY_MAP, KEY_META, KEY_OVERVIEW)
