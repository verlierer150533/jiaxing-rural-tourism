# -*- coding: utf-8 -*-
"""农文旅资源接口：列表、详情、地图点位、筛选元数据、后台增删改。"""
from flask import Blueprint, request
from sqlalchemy import func, or_

from models import Attraction, SystemLog, db
from utils.auth import role_required
from utils.cache import (
    KEY_MAP,
    KEY_META,
    cache_get,
    cache_set,
    invalidate_attraction_cache,
)
from utils.response import fail, ok, paginate

attraction_bp = Blueprint("attraction", __name__, url_prefix="/api/attractions")

# 允许创建/更新时写入的字段
WRITABLE_FIELDS = (
    "name",
    "category",
    "town",
    "address",
    "longitude",
    "latitude",
    "cover_image",
    "summary",
    "description",
    "external_url",
    "sort",
    "status",
)
REQUIRED_CREATE_FIELDS = ("name", "category", "longitude", "latitude")
CATEGORIES = ("古镇", "果园", "村落", "景区")


def _client_ip():
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.remote_addr or "")[:64]


def _to_float(value, field):
    """转 float，失败抛 ValueError（由调用方转成 400）。"""
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError("{0} 必须是数字".format(field))


def _apply_payload(attraction, payload, is_create=False):
    """把请求体写入模型，返回错误信息或 None。"""
    if is_create:
        for field in REQUIRED_CREATE_FIELDS:
            if payload.get(field) in (None, ""):
                return "{0} 不能为空".format(field)

    for field in WRITABLE_FIELDS:
        if field not in payload:
            continue
        value = payload[field]
        if field in ("longitude", "latitude"):
            try:
                value = _to_float(value, field)
            except ValueError as exc:
                return str(exc)
        elif field in ("sort", "status"):
            try:
                value = int(value)
            except (TypeError, ValueError):
                return "{0} 必须是整数".format(field)
        elif field == "category":
            if value not in CATEGORIES:
                return "category 只能是 {0} 之一".format("/".join(CATEGORIES))
        setattr(attraction, field, value)

    if is_create and getattr(attraction, "status", None) is None:
        attraction.status = 1
    return None


@attraction_bp.get("")
def list_attractions():
    """资源列表（仅上架），支持关键词、类别、镇街与分页。"""
    query = Attraction.query.filter(Attraction.status == 1)

    keyword = (request.args.get("keyword") or "").strip()
    if keyword:
        like = "%{0}%".format(keyword)
        query = query.filter(
            or_(
                Attraction.name.like(like),
                Attraction.town.like(like),
                Attraction.address.like(like),
                Attraction.summary.like(like),
            )
        )

    category = (request.args.get("category") or "").strip()
    if category:
        query = query.filter(Attraction.category == category)

    town = (request.args.get("town") or "").strip()
    if town:
        query = query.filter(Attraction.town == town)

    sort = (request.args.get("sort") or "").strip()
    if sort == "-view_count":
        query = query.order_by(Attraction.view_count.desc(), Attraction.id.asc())
    elif sort == "-created_at":
        query = query.order_by(Attraction.created_at.desc(), Attraction.id.desc())
    else:
        query = query.order_by(Attraction.sort.asc(), Attraction.id.asc())

    data = paginate(
        query,
        page=request.args.get("page", 1),
        page_size=request.args.get("page_size", 10),
    )
    return ok(data)


@attraction_bp.get("/admin")
@role_required()
def admin_list():
    """后台资源列表：包含已下架资源（需登录）。"""
    query = Attraction.query

    keyword = (request.args.get("keyword") or "").strip()
    if keyword:
        like = "%{0}%".format(keyword)
        query = query.filter(
            or_(
                Attraction.name.like(like),
                Attraction.town.like(like),
                Attraction.address.like(like),
                Attraction.summary.like(like),
            )
        )

    category = (request.args.get("category") or "").strip()
    if category:
        query = query.filter(Attraction.category == category)

    town = (request.args.get("town") or "").strip()
    if town:
        query = query.filter(Attraction.town == town)

    status = (request.args.get("status") or "").strip()
    if status != "":
        try:
            query = query.filter(Attraction.status == int(status))
        except ValueError:
            return fail("status 必须是 0 或 1", 400, 400)

    query = query.order_by(Attraction.sort.asc(), Attraction.id.asc())
    data = paginate(
        query,
        page=request.args.get("page", 1),
        page_size=request.args.get("page_size", 10),
    )
    return ok(data)


@attraction_bp.get("/map")
def map_markers():
    """地图点位（两端 Leaflet / 微信地图直接消费）。

    读多写少，走 Redis 缓存 60 秒；后台增删改会立即失效。
    """
    cached = cache_get(KEY_MAP)
    if cached is not None:
        return ok(cached)

    items = (
        Attraction.query.filter(Attraction.status == 1)
        .order_by(Attraction.sort.asc(), Attraction.id.asc())
        .all()
    )
    payload = [item.to_map_dict() for item in items]
    cache_set(KEY_MAP, payload, ttl=60)
    return ok(payload)


@attraction_bp.get("/meta")
def meta():
    """筛选元数据：类别与镇街的资源数量（缓存 120 秒）。"""
    cached = cache_get(KEY_META)
    if cached is not None:
        return ok(cached)

    categories = (
        db.session.query(Attraction.category, func.count(Attraction.id))
        .filter(Attraction.status == 1)
        .group_by(Attraction.category)
        .all()
    )
    towns = (
        db.session.query(Attraction.town, func.count(Attraction.id))
        .filter(Attraction.status == 1, Attraction.town.isnot(None))
        .group_by(Attraction.town)
        .all()
    )
    payload = {
        "categories": [
            {"name": name, "count": count} for name, count in categories
        ],
        "towns": [{"name": name, "count": count} for name, count in towns],
    }
    cache_set(KEY_META, payload, ttl=120)
    return ok(payload)


@attraction_bp.get("/<int:attraction_id>")
def get_attraction(attraction_id):
    """资源详情（无副作用，浏览计数由 /api/log 负责）。"""
    attraction = db.session.get(Attraction, attraction_id)
    if attraction is None or attraction.status != 1:
        return fail("资源不存在或已下架", 404, 404)
    return ok(attraction.to_dict())


@attraction_bp.post("")
@role_required()
def create_attraction():
    """新建资源（需登录）。"""
    from flask import g

    payload = request.get_json(silent=True)
    if payload is None:
        return fail("请求体必须是 JSON", 400, 400)

    if Attraction.query.filter_by(name=payload.get("name")).first():
        return fail("同名资源已存在", 409, 409)

    attraction = Attraction()
    error = _apply_payload(attraction, payload, is_create=True)
    if error:
        return fail(error, 400, 400)

    db.session.add(attraction)
    db.session.commit()
    invalidate_attraction_cache()
    SystemLog.record(
        action="create",
        target_type="attraction",
        target_id=attraction.id,
        detail="新建资源：{0}".format(attraction.name),
        admin_id=g.current_admin.id,
        source="web",
        ip=_client_ip(),
    )
    return ok(attraction.to_dict(), message="创建成功")


@attraction_bp.put("/<int:attraction_id>")
@role_required()
def update_attraction(attraction_id):
    """更新资源（局部更新，需登录）。"""
    from flask import g

    attraction = db.session.get(Attraction, attraction_id)
    if attraction is None:
        return fail("资源不存在", 404, 404)

    payload = request.get_json(silent=True)
    if payload is None:
        return fail("请求体必须是 JSON", 400, 400)

    new_name = payload.get("name")
    if new_name and new_name != attraction.name:
        if Attraction.query.filter_by(name=new_name).first():
            return fail("同名资源已存在", 409, 409)

    error = _apply_payload(attraction, payload, is_create=False)
    if error:
        return fail(error, 400, 400)

    db.session.commit()
    invalidate_attraction_cache()
    SystemLog.record(
        action="update",
        target_type="attraction",
        target_id=attraction.id,
        detail="更新资源：{0}".format(attraction.name),
        admin_id=g.current_admin.id,
        source="web",
        ip=_client_ip(),
    )
    return ok(attraction.to_dict(), message="更新成功")


@attraction_bp.delete("/<int:attraction_id>")
@role_required()
def delete_attraction(attraction_id):
    """删除资源（需登录）。"""
    from flask import g

    attraction = db.session.get(Attraction, attraction_id)
    if attraction is None:
        return fail("资源不存在", 404, 404)

    name = attraction.name
    db.session.delete(attraction)
    db.session.commit()
    invalidate_attraction_cache()
    SystemLog.record(
        action="delete",
        target_type="attraction",
        target_id=attraction_id,
        detail="删除资源：{0}".format(name),
        admin_id=g.current_admin.id,
        source="web",
        ip=_client_ip(),
    )
    return ok({"id": attraction_id}, message="删除成功")


@attraction_bp.patch("/<int:attraction_id>/status")
@role_required()
def toggle_status(attraction_id):
    """上架 / 下架。"""
    from flask import g

    attraction = db.session.get(Attraction, attraction_id)
    if attraction is None:
        return fail("资源不存在", 404, 404)

    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    try:
        status = int(status)
    except (TypeError, ValueError):
        return fail("status 必须是 0 或 1", 400, 400)
    if status not in (0, 1):
        return fail("status 必须是 0 或 1", 400, 400)

    attraction.status = status
    db.session.commit()
    invalidate_attraction_cache()
    SystemLog.record(
        action="update",
        target_type="attraction",
        target_id=attraction.id,
        detail="{0}：{1}".format("上架" if status else "下架", attraction.name),
        admin_id=g.current_admin.id,
        source="web",
        ip=_client_ip(),
    )
    return ok({"id": attraction.id, "status": status}, message="操作成功")
