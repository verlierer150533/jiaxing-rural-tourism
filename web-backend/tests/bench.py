# -*- coding: utf-8 -*-
"""接口性能压测脚本（无第三方依赖，仅标准库）。

用法（后端已启动）：
    python tests/bench.py            # 默认每个场景 200 次请求、10 并发
    python tests/bench.py 300 20     # 自定义 次数 并发数

场景：
    A. GET  /api/attractions        走 MySQL 查询 + 分页
    B. GET  /api/attractions/map    走 Redis 缓存（命中后直接返回）
    C. POST /api/log                写库 + 统计 + WebSocket 广播
"""
import json
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor

BASE = "http://127.0.0.1:5000"
DEFAULT_TOTAL = 200
DEFAULT_WORKERS = 10


def _time_request(url, data=None, method="GET"):
    body = None
    headers = {}
    if data is not None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            response.read()
            ok = 200 <= response.status < 300
    except urllib.error.HTTPError as exc:
        ok = False
        exc.read()
    except Exception:
        ok = False
    return (time.perf_counter() - start) * 1000.0, ok


def run_scenario(name, total, workers, make_request):
    latencies = []
    errors = [0]
    lock = threading.Lock()

    def worker():
        local = []
        local_errors = 0
        for _ in range(total // workers):
            elapsed, ok = make_request()
            local.append(elapsed)
            if not ok:
                local_errors += 1
        with lock:
            latencies.extend(local)
            errors[0] += local_errors

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for _ in range(workers):
            pool.submit(worker)
    wall = time.perf_counter() - started

    latencies.sort()
    count = len(latencies)

    def pick(percent):
        if not count:
            return 0.0
        index = min(count - 1, int(count * percent))
        return latencies[index]

    result = {
        "scene": name,
        "requests": count,
        "errors": errors[0],
        "wall_s": round(wall, 2),
        "rps": round(count / wall, 1) if wall else 0,
        "avg_ms": round(statistics.mean(latencies), 1) if count else 0,
        "p50_ms": round(pick(0.50), 1),
        "p95_ms": round(pick(0.95), 1),
        "p99_ms": round(pick(0.99), 1),
        "max_ms": round(max(latencies), 1) if count else 0,
    }
    return result


def main():
    total = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TOTAL
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_WORKERS

    print("=" * 78)
    print(" 压测目标 {0}　每场景 {1} 次请求 / {2} 并发".format(BASE, total, workers))
    print("=" * 78)

    results = []

    results.append(
        run_scenario(
            "A. GET /api/attractions",
            total,
            workers,
            lambda: _time_request(
                BASE + "/api/attractions?page=1&page_size=10&category=%E6%9E%9C%E5%9B%AD"
            ),
        )
    )

    # 缓存场景：先预热一次
    _time_request(BASE + "/api/attractions/map")
    results.append(
        run_scenario(
            "B. GET /api/attractions/map (Redis)",
            total,
            workers,
            lambda: _time_request(BASE + "/api/attractions/map"),
        )
    )

    counter = {"n": 0}

    def log_request():
        counter["n"] += 1
        payload = {
            "action": "view",
            "target_type": "attraction",
            "target_id": (counter["n"] % 12) + 1,
            "source": "miniprogram",
            "session_id": "bench-{0}".format(uuid.uuid4().hex[:8]),
            "detail": "bench",
        }
        return _time_request(BASE + "/api/log", payload, method="POST")

    results.append(run_scenario("C. POST /api/log (写库+广播)", total, workers, log_request))

    print("{0:<34}{1:>7}{2:>7}{3:>9}{4:>9}{5:>9}{6:>9}{7:>9}".format(
        "场景", "请求数", "错误", "RPS", "平均ms", "P50", "P95", "P99"))
    print("-" * 78)
    for item in results:
        print("{0:<34}{1:>7}{2:>7}{3:>9}{4:>9}{5:>9}{6:>9}{7:>9}".format(
            item["scene"], item["requests"], item["errors"], item["rps"],
            item["avg_ms"], item["p50_ms"], item["p95_ms"], item["p99_ms"]))
    print("-" * 78)

    with open("tests/bench_result.json", "w", encoding="utf-8") as fh:
        json.dump(
            {
                "target": BASE,
                "total": total,
                "workers": workers,
                "at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "results": results,
            },
            fh,
            ensure_ascii=False,
            indent=2,
        )
    print("结果已写入 tests/bench_result.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
