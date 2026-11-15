# -*- coding: utf-8 -*-
"""JWT 鉴权辅助：当前登录管理员、角色校验装饰器。"""
from functools import wraps

from flask import g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from models import Admin, db
from utils.response import fail


def current_admin():
    """按 JWT 中的 identity 取管理员对象，取不到返回 None。"""
    identity = get_jwt_identity()
    if identity is None:
        return None
    try:
        admin_id = int(identity)
    except (TypeError, ValueError):
        return None
    return db.session.get(Admin, admin_id)


def role_required(*roles):
    """要求已登录（可选要求指定角色）。

    用法：
        @role_required()              # 任意已登录管理员
        @role_required("super_admin") # 仅超级管理员
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            admin = current_admin()
            if admin is None or admin.status != 1:
                return fail("账号不存在或已被禁用", 401, 401)
            if roles and admin.role not in roles:
                return fail("无操作权限", 403, 403)
            g.current_admin = admin
            return func(*args, **kwargs)

        return wrapper

    return decorator
