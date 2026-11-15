# -*- coding: utf-8 -*-
"""模拟"小程序游客点击"并验证大屏实时推送。

用途：在不用微信开发者工具的情况下，预演一遍端到端链路：
    POST /api/log（浏览） → 后端落库 → WebSocket 广播 → 大屏收到 new_data

用法：
    python tests/simulate_visitor.py                       # 默认：看盐官古镇 + 点大尖山果园外链
    python tests/simulate_visitor.py --base http://127.0.0.1:5173
    python tests/simulate_visitor.py --session demo-abc
"""
import argparse
import json
import sys
import threading
import time
import urllib.request
import uuid

import socketio

received = []
lock = threading.Lock()


def post_log(base, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        base + "/api/log",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:5000")
    parser.add_argument("--session", default="sim-" + uuid.uuid4().hex[:8])
    parser.add_argument("--wait", type=float, default=6.0)
    args = parser.parse_args()

    namespace = "/ws"
    sio = socketio.Client(reconnection=False)

    @sio.on("new_data", namespace=namespace)
    def on_new_data(data):
        with lock:
            received.append(data)
        print("[大屏收到] event={0} 目标={1} PV={2} UV={3} 外链点击={4}".format(
            data.get("event"),
            (data.get("target") or {}).get("name"),
            data["metrics"]["pv"], data["metrics"]["uv"],
            data["metrics"]["click_external"]))

    sio.connect(args.base, namespaces=[namespace], transports=["polling"])
    print("[连接] {0}{1} 已连上".format(args.base, namespace))

    # 1) 浏览「盐官古镇」——小程序进入详情页会触发
    res1 = post_log(args.base, {
        "action": "view",
        "target_type": "attraction",
        "target_id": 1,
        "source": "miniprogram",
        "session_id": args.session,
        "detail": "详情页浏览 盐官古镇",
    })
    print("[HTTP] 浏览上报 -> code={0} log_id={1}".format(
        res1["code"], res1["data"]["log_id"]))

    time.sleep(1.0)

    # 2) 点击「大尖山果园」的第三方导流按钮
    res2 = post_log(args.base, {
        "action": "click_external",
        "target_type": "attraction",
        "target_id": 2,
        "source": "miniprogram",
        "session_id": args.session,
        "detail": "外链点击 大尖山果园",
    })
    print("[HTTP] 外链上报 -> code={0} log_id={1}".format(
        res2["code"], res2["data"]["log_id"]))

    time.sleep(args.wait)
    sio.disconnect()

    print("-" * 60)
    if len(received) >= 2:
        last = received[-1]["metrics"]
        print("[PASS] 大屏共收到 {0} 条实时事件".format(len(received)))
        print("       最新指标：PV={0} UV={1} 外链点击={2} 转化率={3}".format(
            last["pv"], last["uv"], last["click_external"], last["conversion_rate"]))
        return 0

    print("[FAIL] 只收到 {0} 条事件，请检查 WebSocket 是否正常".format(len(received)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
