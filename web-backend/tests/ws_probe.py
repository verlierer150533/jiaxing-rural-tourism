# -*- coding: utf-8 -*-
"""WebSocket 联调探针（独立进程，不依赖 eventlet）。

流程：
    1. 连接服务端 /ws 命名空间
    2. 另起线程调用 POST /api/log 制造一条浏览足迹
    3. 断言 8 秒内收到 new_data，并校验关键字段

运行前提：`python app.py` 已在 127.0.0.1:5000 启动。
"""
import json
import os
import sys
import threading
import time
import urllib.request
import uuid

import socketio

# 默认直连后端；设置 PROBE_BASE 可改为经 Vite 代理验证（如 http://127.0.0.1:5173）
BASE = os.getenv("PROBE_BASE", "http://127.0.0.1:5000")
NAMESPACE = "/ws"

received = []
done = threading.Event()

sio = socketio.Client(reconnection=False)


@sio.on("new_data", namespace=NAMESPACE)
def on_new_data(data):
    received.append(data)
    print("\n[WS] 收到 new_data：")
    print(json.dumps(data, ensure_ascii=False, indent=2)[:900])
    done.set()


def post_log():
    """线程内触发一次浏览行为。"""
    time.sleep(1.0)
    body = json.dumps(
        {
            "action": "view",
            "target_type": "attraction",
            "target_id": 2,
            "source": "miniprogram",
            "session_id": "probe-{0}".format(uuid.uuid4().hex[:8]),
            "detail": "ws_probe 自动测试",
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        BASE + "/api/log",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = response.read().decode("utf-8")
    print("[HTTP] POST /api/log ->", payload[:400])


def main():
    try:
        sio.connect(BASE, namespaces=[NAMESPACE], transports=["polling"])
    except Exception as exc:
        print("[FAIL] 无法连接 WebSocket：{0}".format(exc))
        return 2

    print("[WS] 已连接 {0}{1}".format(BASE, NAMESPACE))

    worker = threading.Thread(target=post_log)
    worker.start()

    got = done.wait(8)
    worker.join()
    sio.disconnect()

    if not got or not received:
        print("[FAIL] 8 秒内未收到 new_data")
        return 1

    data = received[0]
    missing = [key for key in ("event", "log", "target", "metrics", "timestamp")
               if key not in data]
    if missing:
        print("[FAIL] new_data 缺少字段：{0}".format(missing))
        return 1

    print("[PASS] new_data 字段完整")
    print("       event   = {0}".format(data["event"]))
    print("       target  = {0}".format(
        (data.get("target") or {}).get("name")))
    print("       metrics = {0}".format(data["metrics"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
