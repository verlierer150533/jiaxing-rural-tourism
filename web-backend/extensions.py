# -*- coding: utf-8 -*-
"""Flask 扩展单例。

单独成模块，避免 app.py 与 api/* 之间循环引用。
"""
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

jwt = JWTManager()
socketio = SocketIO()

# WebSocket 命名空间：Web 大屏与小程序的实时通道
WS_NAMESPACE = "/ws"
# 大屏订阅的事件名
WS_EVENT_NEW_DATA = "new_data"
