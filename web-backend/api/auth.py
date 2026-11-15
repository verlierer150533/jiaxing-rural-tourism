# -*- coding: utf-8 -*-
"""认证相关接口：登录、当前用户信息、修改密码。"""
from datetime import datetime

from flask import Blueprint, current_app, request
from flask_jwt_extended import create_access_token

from models import Admin, SystemLog, db
from utils.auth import role_required
from utils.response import fail, ok

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _client_ip():
    """取真实客户端 IP（兼容反向代理）。"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.remote_addr or "")[:64]


def _user_agent():
    return (request.headers.get("User-Agent") or "")[:255]


@auth_bp.post("/login")
def login():
    """管理员登录，返回 JWT。"""
    payload = request.get_json(silent=True)
    if payload is None:
        return fail("请求体必须是 JSON", 400, 400)

    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    if not username or not password:
        return fail("用户名或密码不能为空", 400, 400)

    admin = Admin.query.filter_by(username=username).first()
    if admin is None or not admin.check_password(password):
        SystemLog.record(
            action="login_failed",
            target_type="admin",
            target_id=admin.id if admin else None,
            detail="账号或密码错误",
            admin_id=admin.id if admin else None,
            source="web",
            ip=_client_ip(),
            user_agent=_user_agent(),
        )
        # 不区分“账号不存在”与“密码错误”，防账号枚举
        return fail("账号或密码错误", 401, 401)

    if admin.status != 1:
        return fail("账号已被禁用", 403, 403)

    admin.last_login_at = datetime.now()
    db.session.commit()

    expires = current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    token = create_access_token(
        identity=str(admin.id),
        additional_claims={"username": admin.username, "role": admin.role},
        expires_delta=expires,
    )

    SystemLog.record(
        action="login",
        target_type="admin",
        target_id=admin.id,
        detail="登录成功",
        admin_id=admin.id,
        source="web",
        ip=_client_ip(),
        user_agent=_user_agent(),
    )

    return ok(
        {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": int(expires.total_seconds()),
            "admin": admin.to_dict(),
        },
        message="登录成功",
    )


@auth_bp.get("/profile")
@role_required()
def profile():
    """当前登录管理员信息。"""
    from flask import g

    return ok(g.current_admin.to_dict())


@auth_bp.put("/password")
@role_required()
def change_password():
    """修改本次登录账号的密码。"""
    from flask import g

    payload = request.get_json(silent=True)
    if payload is None:
        return fail("请求体必须是 JSON", 400, 400)

    old_password = payload.get("old_password") or ""
    new_password = payload.get("new_password") or ""
    if not old_password or not new_password:
        return fail("原密码与新密码不能为空", 400, 400)
    if len(new_password) < 6:
        return fail("新密码长度不能少于 6 位", 400, 400)

    admin = g.current_admin
    if not admin.check_password(old_password):
        return fail("原密码不正确", 400, 400)

    admin.set_password(new_password)
    db.session.commit()
    SystemLog.record(
        action="update",
        target_type="admin",
        target_id=admin.id,
        detail="修改密码",
        admin_id=admin.id,
        source="web",
        ip=_client_ip(),
        user_agent=_user_agent(),
    )
    return ok(None, message="密码修改成功")
