# -*- coding: utf-8 -*-
"""Flask 应用入口。

启动：
    python app.py
健康检查：
    GET  http://127.0.0.1:5000/api/ping
实时通道：
    WebSocket ws://127.0.0.1:5000/ws ，事件 new_data
"""
import os

# ---- eventlet 必须在任何网络相关库导入之前完成 monkey patch ----
ASYNC_MODE_FALLBACK = None
try:
    import eventlet  # noqa: E402

    eventlet.monkey_patch()
except Exception as _exc:  # pragma: no cover - 环境降级分支
    ASYNC_MODE_FALLBACK = "threading"
    print("[WARN] eventlet 不可用（{0}），SocketIO 降级为 threading 模式".format(_exc))

from datetime import datetime  # noqa: E402

from flask import Flask, jsonify  # noqa: E402
from flask_cors import CORS  # noqa: E402
from werkzeug.exceptions import HTTPException  # noqa: E402

from api import register_blueprints  # noqa: E402
from config import get_config  # noqa: E402
from extensions import WS_NAMESPACE, jwt, socketio  # noqa: E402
from models import db  # noqa: E402
from utils.response import fail, ok  # noqa: E402
from ws.events import online_clients, register_socket_events  # noqa: E402

VERSION = "0.2.0"


def register_error_handlers(app):
    """任何异常都返回 JSON，避免前端收到 HTML 错误页。"""

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc):
        return (
            jsonify(
                {
                    "code": exc.code,
                    "message": exc.description or exc.name,
                    "data": None,
                }
            ),
            exc.code,
        )

    @app.errorhandler(Exception)
    def handle_exception(exc):
        app.logger.exception("未捕获异常: %s", exc)
        return jsonify({"code": 500, "message": "服务器内部错误", "data": None}), 500


def register_jwt_handlers(app):
    """JWT 异常统一转成 {code:401} 响应。"""

    @jwt.unauthorized_loader
    def handle_missing_token(reason):
        return fail("未登录或登录已过期", 401, 401)

    @jwt.invalid_token_loader
    def handle_invalid_token(reason):
        return fail("登录凭证无效", 401, 401)

    @jwt.expired_token_loader
    def handle_expired_token(jwt_header, jwt_payload):
        return fail("登录已过期，请重新登录", 401, 401)

    @jwt.revoked_token_loader
    def handle_revoked_token(jwt_header, jwt_payload):
        return fail("登录凭证已失效", 401, 401)


def register_routes(app):
    """基础路由。"""

    @app.get("/api/ping")
    def ping():
        from utils.cache import redis_alive

        return ok(
            {
                "service": "jiaxing-rural-tourism-backend",
                "version": VERSION,
                "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "async_mode": socketio.async_mode,
                "database": app.config["MYSQL_DATABASE"],
                "redis": redis_alive(),
                "message_queue": (
                    "redis" if app.config["SOCKETIO_MESSAGE_QUEUE"] else "memory"
                ),
                "ws_namespace": WS_NAMESPACE,
                "ws_online": online_clients(),
            },
            message="pong",
        )


def _detect_message_queue(app):
    """Redis 可用则用 Pub/Sub 作 SocketIO 消息通道，否则退回进程内通道。"""
    try:
        import redis as redis_lib

        client = redis_lib.Redis(
            host=app.config["REDIS_HOST"],
            port=app.config["REDIS_PORT"],
            password=app.config["REDIS_PASSWORD"],
            socket_connect_timeout=1,
            socket_timeout=1,
            protocol=2,  # 兼容 Redis 5.x
        )
        client.ping()
        print("[INFO] SocketIO 消息通道：Redis Pub/Sub ({0})".format(
            app.config["REDIS_URL"]))
        return app.config["REDIS_URL"]
    except Exception as exc:  # pragma: no cover - 依赖外部服务
        print("[WARN] Redis 不可用（{0}），SocketIO 使用进程内消息通道".format(exc))
        return None


def create_app(config_name=None):
    """应用工厂。"""
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))
    app.json.ensure_ascii = False  # 中文不转义

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    jwt.init_app(app)

    message_queue = _detect_message_queue(app)
    app.config["SOCKETIO_MESSAGE_QUEUE"] = message_queue

    async_mode = ASYNC_MODE_FALLBACK or app.config["SOCKETIO_ASYNC_MODE"]
    socketio.init_app(
        app,
        cors_allowed_origins=app.config["SOCKETIO_CORS_ORIGINS"],
        async_mode=async_mode,
        message_queue=message_queue,
    )

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    register_error_handlers(app)
    register_jwt_handlers(app)
    register_blueprints(app)
    register_socket_events()
    register_routes(app)
    return app


app = create_app()


if __name__ == "__main__":
    print("=" * 60)
    print(" 农文旅平台后端启动  async_mode = {0}".format(socketio.async_mode))
    print(" 健康检查 : http://127.0.0.1:5000/api/ping")
    print(" 登录接口 : POST http://127.0.0.1:5000/api/auth/login")
    print(" 实时通道 : ws://127.0.0.1:5000/ws  (new_data)")
    print("=" * 60)
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
