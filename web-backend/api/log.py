# -*- coding: utf-8 -*-
"""浏览足迹接口。

核心链路：
    小程序 POST /api/log
        → 写入 system_log（并可自增 attraction.view_count）
        → 统计今日 PV/UV/外链点击
        → WebSocket 向 /ws 广播 new_data
        → Web 大屏 ECharts 实时跳动
"""
from datetime import datetime

from flask import Blueprint, request
from sqlalchemy import update

from extensions import WS_NAMESPACE, WS_EVENT_NEW_DATA
from models import Attraction, SystemLog, db
from utils.auth import role_required
from utils.response import fail, ok, paginate

log_bp = Blueprint("log", __name__, url_prefix="/api")

ALLOWED_ACTIONS = ("view", "click_external", "search")
ALLOWED_TARGET_TYPES = ("attraction", "product", "article", "system")
ALLOWED_SOURCES = ("miniprogram", "web")


def _client_ip():
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.remote_addr or "")[:64]


@log_bp.post("/log")
def create_log():
    """记录一条浏览足迹并实时广播（游客端匿名调用）。"""
    payload = request.get_json(silent=True)
    if payload is None:
        return fail("请求体必须是 JSON", 400, 400)

    action = (payload.get("action") or "").strip()
    if action not in ALLOWED_ACTIONS:
        return fail("action 只能是 {0} 之一".format("/".join(ALLOWED_ACTIONS)), 400, 400)

    target_type = (payload.get("target_type") or "attraction").strip()
    if target_type not in ALLOWED_TARGET_TYPES:
        target_type = "attraction"

    target_id = payload.get("target_id")
    if target_id is not None:
        try:
            target_id = int(target_id)
        except (TypeError, ValueError):
            return fail("target_id 必须是整数", 400, 400)

    source = (payload.get("source") or "miniprogram").strip()
    if source not in ALLOWED_SOURCES:
        source = "miniprogram"

    session_id = (payload.get("session_id") or "").strip()[:64] or None

    detail = payload.get("detail")
    if detail:
        detail = str(detail)[:480]

    # ---- 查目标资源（不存在也照常记日志，便于排查前端误传） ----
    target = None
    if target_type == "attraction" and target_id is not None:
        target = db.session.get(Attraction, target_id)
        if target is None:
            detail = ((detail + " ") if detail else "") + "[target_missing]"

    log = SystemLog.record(
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        admin_id=None,
        source=source,
        ip=_client_ip(),
        user_agent=(request.headers.get("User-Agent") or "")[:255],
        session_id=session_id,
    )

    # ---- 浏览量原子自增，避免并发读改写 ----
    if target is not None and action == "view":
        db.session.execute(
            update(Attraction)
            .where(Attraction.id == target.id)
            .values(view_count=Attraction.view_count + 1)
        )
        db.session.commit()
        db.session.refresh(target)

    metrics = _today_metrics()

    event_payload = {
        "event": action,
        "log": log.to_dict(),
        "target": (
            {
                "id": target.id,
                "name": target.name,
                "category": target.category,
                "town": target.town,
            }
            if target is not None
            else None
        ),
        "metrics": metrics,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    _broadcast(event_payload)

    return ok({"log_id": log.id, "metrics": metrics}, message="记录成功")


@log_bp.get("/logs")
@role_required()
def list_logs():
    """浏览足迹列表（后台，需登录）。"""
    query = SystemLog.query

    action = (request.args.get("action") or "").strip()
    if action:
        query = query.filter(SystemLog.action == action)

    source = (request.args.get("source") or "").strip()
    if source:
        query = query.filter(SystemLog.source == source)

    target_type = (request.args.get("target_type") or "").strip()
    if target_type:
        query = query.filter(SystemLog.target_type == target_type)

    date_from = (request.args.get("date_from") or "").strip()
    if date_from:
        try:
            query = query.filter(
                SystemLog.created_at >= datetime.strptime(date_from, "%Y-%m-%d")
            )
        except ValueError:
            return fail("date_from 格式应为 YYYY-MM-DD", 400, 400)

    date_to = (request.args.get("date_to") or "").strip()
    if date_to:
        try:
            end = datetime.strptime(date_to, "%Y-%m-%d")
            query = query.filter(SystemLog.created_at < end.replace(hour=23, minute=59, second=59))
        except ValueError:
            return fail("date_to 格式应为 YYYY-MM-DD", 400, 400)

    query = query.order_by(SystemLog.id.desc())
    data = paginate(
        query,
        page=request.args.get("page", 1),
        page_size=request.args.get("page_size", 10),
    )
    return ok(data)


def _today_metrics():
    """今日实时指标（与 /api/stats/overview 的 today 同口径）。"""
    from api.stats import today_metrics

    return today_metrics()


def _broadcast(payload):
    """广播到 /ws；失败不影响 HTTP 结果。"""
    from ws.events import broadcast_new_data

    return broadcast_new_data(payload)
