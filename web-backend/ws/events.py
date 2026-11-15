# -*- coding: utf-8 -*-
"""WebSocket 事件与广播。

通道约定：
    namespace = "/ws"
    事件名     = "new_data"（服务端 → 客户端，大屏消费）

注意：广播必须用 socketio.emit(...)，不能用 flask_socketio.emit(...)，
后者只会回给当前请求方（HTTP 请求下根本没有请求方）。
"""
from datetime import datetime

from flask import current_app

from extensions import WS_EVENT_NEW_DATA, WS_NAMESPACE, socketio

# 简单的在线连接计数，供 /api/ping 或调试查看
_online = {"count": 0}


def online_clients():
    """当前 /ws 在线连接数。"""
    return _online["count"]


def register_socket_events():
    """注册 /ws 命名空间的连接、断开与心跳事件。"""

    @socketio.on("connect", namespace=WS_NAMESPACE)
    def on_connect(*args, **kwargs):  # noqa: ANN002, ANN003
        _online["count"] += 1
        try:
            current_app.logger.info(
                "WebSocket 客户端接入，当前在线 %s", _online["count"]
            )
        except Exception:  # pragma: no cover - 日志失败不影响连接
            pass
        return True

    @socketio.on("disconnect", namespace=WS_NAMESPACE)
    def on_disconnect(*args, **kwargs):  # noqa: ANN002, ANN003
        _online["count"] = max(0, _online["count"] - 1)
        try:
            current_app.logger.info(
                "WebSocket 客户端断开，当前在线 %s", _online["count"]
            )
        except Exception:  # pragma: no cover
            pass

    @socketio.on("ping", namespace=WS_NAMESPACE)
    def on_ping(*args, **kwargs):  # noqa: ANN002, ANN003
        """心跳，用于前端弱网保活检测。"""
        return {
            "event": "pong",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


def broadcast_new_data(payload):
    """向 /ws 所有客户端广播 new_data。

    广播失败只记录日志，绝不影响 HTTP 接口的返回结果。
    """
    try:
        socketio.emit(WS_EVENT_NEW_DATA, payload, namespace=WS_NAMESPACE)
        return True
    except Exception:  # pragma: no cover - 广播异常不应中断业务
        try:
            current_app.logger.warning("WebSocket 广播失败", exc_info=True)
        except Exception:
            pass
        return False
