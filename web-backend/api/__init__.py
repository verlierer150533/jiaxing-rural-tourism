# -*- coding: utf-8 -*-
"""API 蓝图注册。"""
from api.attraction import attraction_bp
from api.auth import auth_bp
from api.favorite import favorite_bp
from api.log import log_bp
from api.stats import stats_bp

ALL_BLUEPRINTS = (auth_bp, attraction_bp, log_bp, stats_bp, favorite_bp)


def register_blueprints(app):
    """注册全部业务蓝图。"""
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)
