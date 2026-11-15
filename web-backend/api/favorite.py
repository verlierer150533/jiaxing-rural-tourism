# -*- coding: utf-8 -*-
"""收藏接口：匿名设备收藏 / 取消收藏 / 收藏列表。

设计取舍：
    1. 平台没有账号体系，收藏绑定小程序生成的匿名 session_id；
    2. POST 采用 toggle 语义（再点一次即取消），前端爱心按钮只调一个接口；
    3. 收藏不写 system_log，也不计入 PV/UV 与大屏统计，避免污染现有指标口径；
    4. 同一设备对同一点位有唯一约束，并发双击由数据库兜底。
"""
from flask import Blueprint, request
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from models import Attraction, Favorite, db
from utils.response import fail, ok

favorite_bp = Blueprint("favorite", __name__, url_prefix="/api/favorite")

TARGET_TYPE = "attraction"


def _clean_session_id():
    return (request.args.get("session_id") or "").strip()[:64]


def _favorite_count(target_id):
    return (
        db.session.query(func.count(Favorite.id))
        .filter(
            Favorite.target_type == TARGET_TYPE,
            Favorite.target_id == target_id,
        )
        .scalar()
        or 0
    )


@favorite_bp.post("")
def toggle_favorite():
    """收藏 / 取消收藏（同一接口切换）。"""
    payload = request.get_json(silent=True)
    if payload is None:
        return fail("请求体必须是 JSON", 400, 400)

    session_id = (payload.get("session_id") or "").strip()[:64]
    if not session_id:
        return fail("session_id 不能为空", 400, 400)

    try:
        target_id = int(payload.get("target_id"))
    except (TypeError, ValueError):
        return fail("target_id 必须是整数", 400, 400)

    attraction = db.session.get(Attraction, target_id)
    if attraction is None or attraction.status != 1:
        return fail("资源不存在或已下架", 404, 404)

    existing = Favorite.query.filter_by(
        session_id=session_id,
        target_type=TARGET_TYPE,
        target_id=target_id,
    ).first()

    if existing is not None:
        db.session.delete(existing)
        db.session.commit()
        return ok(
            {"favorited": False, "favorite_count": _favorite_count(target_id)},
            message="已取消收藏",
        )

    favorite = Favorite(
        session_id=session_id, target_type=TARGET_TYPE, target_id=target_id
    )
    db.session.add(favorite)
    try:
        db.session.commit()
    except IntegrityError:
        # 并发双击：另一请求已插入，视为已收藏
        db.session.rollback()
        return ok(
            {"favorited": True, "favorite_count": _favorite_count(target_id)},
            message="已收藏",
        )

    return ok(
        {"favorited": True, "favorite_count": _favorite_count(target_id)},
        message="已收藏",
    )


@favorite_bp.get("")
def list_favorites():
    """当前会话收藏的资源列表（只返回仍上架的点位）。"""
    session_id = _clean_session_id()
    if not session_id:
        return fail("session_id 不能为空", 400, 400)

    rows = (
        db.session.query(Favorite, Attraction)
        .join(Attraction, Attraction.id == Favorite.target_id)
        .filter(
            Favorite.session_id == session_id,
            Favorite.target_type == TARGET_TYPE,
            Attraction.status == 1,
        )
        .order_by(Favorite.created_at.desc(), Favorite.id.desc())
        .all()
    )

    items = []
    for favorite, attraction in rows:
        item = attraction.to_dict()
        item["favorited_at"] = favorite.created_at.strftime("%Y-%m-%d %H:%M:%S")
        items.append(item)

    return ok({"list": items, "total": len(items)})


@favorite_bp.get("/check")
def check_favorite():
    """查询当前会话是否收藏了某个点位（用于爱心按钮初始状态）。"""
    session_id = _clean_session_id()
    if not session_id:
        return fail("session_id 不能为空", 400, 400)

    try:
        target_id = int(request.args.get("target_id"))
    except (TypeError, ValueError):
        return fail("target_id 必须是整数", 400, 400)

    exists = (
        Favorite.query.filter_by(
            session_id=session_id,
            target_type=TARGET_TYPE,
            target_id=target_id,
        ).first()
        is not None
    )
    return ok({"favorited": exists, "favorite_count": _favorite_count(target_id)})
