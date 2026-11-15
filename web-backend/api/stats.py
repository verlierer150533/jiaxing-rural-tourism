# -*- coding: utf-8 -*-
"""数据统计接口：为 ECharts 大屏提供首屏数据。"""
from datetime import datetime, timedelta

from flask import Blueprint
from sqlalchemy import distinct, func

from models import Attraction, SystemLog, db
from utils.auth import role_required
from utils.response import ok

stats_bp = Blueprint("stats", __name__, url_prefix="/api/stats")


def _day_range(day=None):
    """返回某一天的 [00:00:00, 次日 00:00:00) 区间。"""
    day = day or datetime.now().date()
    start = datetime.combine(day, datetime.min.time())
    return start, start + timedelta(days=1)


def today_metrics():
    """今日 PV / UV / 外链点击 / 点击转化率。

    口径：
        PV = action='view' 的条数
        UV = action='view' 且 session_id 非空的去重设备数
        转化率 = click_external / PV
    """
    start, end = _day_range()

    pv = (
        SystemLog.query.filter(
            SystemLog.created_at >= start,
            SystemLog.created_at < end,
            SystemLog.action == "view",
        ).count()
    )
    click_external = (
        SystemLog.query.filter(
            SystemLog.created_at >= start,
            SystemLog.created_at < end,
            SystemLog.action == "click_external",
        ).count()
    )
    uv = (
        db.session.query(func.count(distinct(SystemLog.session_id)))
        .filter(
            SystemLog.created_at >= start,
            SystemLog.created_at < end,
            SystemLog.action == "view",
            SystemLog.session_id.isnot(None),
        )
        .scalar()
        or 0
    )

    return {
        "pv": pv,
        "uv": int(uv),
        "click_external": click_external,
        "conversion_rate": round(click_external / pv, 4) if pv else 0.0,
    }


@stats_bp.get("/overview")
@role_required()
def overview():
    """大屏首屏数据。"""
    start, end = _day_range()

    total_pv = SystemLog.query.filter(SystemLog.action == "view").count()
    total_uv = (
        db.session.query(func.count(distinct(SystemLog.session_id)))
        .filter(
            SystemLog.action == "view",
            SystemLog.session_id.isnot(None),
        )
        .scalar()
        or 0
    )

    category_rows = (
        db.session.query(Attraction.category, func.count(Attraction.id))
        .filter(Attraction.status == 1)
        .group_by(Attraction.category)
        .all()
    )
    town_rows = (
        db.session.query(Attraction.town, func.count(Attraction.id))
        .filter(Attraction.status == 1, Attraction.town.isnot(None))
        .group_by(Attraction.town)
        .all()
    )

    top_attractions = (
        Attraction.query.filter(Attraction.status == 1)
        .order_by(Attraction.view_count.desc(), Attraction.id.asc())
        .limit(8)
        .all()
    )

    hourly_rows = (
        db.session.query(
            func.hour(SystemLog.created_at), func.count(SystemLog.id)
        )
        .filter(
            SystemLog.created_at >= start,
            SystemLog.created_at < end,
            SystemLog.action == "view",
        )
        .group_by(func.hour(SystemLog.created_at))
        .all()
    )
    hour_map = {int(hour): int(count) for hour, count in hourly_rows if hour is not None}

    latest = (
        SystemLog.query.order_by(SystemLog.id.desc()).limit(10).all()
    )

    return ok(
        {
            "today": today_metrics(),
            "total": {
                "pv": total_pv,
                "uv": int(total_uv),
                "attraction_count": Attraction.query.filter(
                    Attraction.status == 1
                ).count(),
                "log_count": SystemLog.query.count(),
            },
            "category_dist": [
                {"name": name or "未分类", "value": int(count)}
                for name, count in category_rows
            ],
            "town_dist": [
                {"name": name, "value": int(count)} for name, count in town_rows
            ],
            "top_attractions": [
                {
                    "id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "view_count": item.view_count,
                }
                for item in top_attractions
            ],
            "hourly": [
                {"hour": "{0:02d}".format(hour), "pv": hour_map.get(hour, 0)}
                for hour in range(24)
            ],
            "latest": [item.to_dict() for item in latest],
        },
        message="ok",
    )
