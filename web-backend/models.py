# -*- coding: utf-8 -*-
"""SQLAlchemy 数据模型。

当前包含四张表：
    admin        后台管理员
    attraction   农文旅资源点位（古镇 / 果园 / 村落 / 景区），携带经纬度供 GIS 使用
    system_log   系统日志（后台操作日志 + 小程序游客行为日志，靠 source 区分）
    favorite     游客收藏（匿名设备会话 + 资源点位）
"""
from datetime import datetime
from urllib.parse import quote

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

# 所有表统一 InnoDB + utf8mb4，避免中文与 emoji 乱码
MYSQL_TABLE_ARGS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

# 淘宝搜索站点（移动端可直接唤起 App）
TAOBAO_SEARCH = "https://s.taobao.com/search?q="
# 视为"没有自定义链接"的占位值：早期种子数据里填的是商城首页
PLACEHOLDER_URLS = {
    "",
    "https://www.taobao.com",
    "https://taobao.com",
    "https://www.tmall.com",
    "https://www.jd.com",
    "https://jd.com",
}


def _fmt(dt):
    """datetime -> 'YYYY-MM-DD HH:MM:SS'。"""
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None


class Admin(db.Model):
    """后台管理员。"""

    __tablename__ = "admin"
    __table_args__ = MYSQL_TABLE_ARGS

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(
        db.String(50), unique=True, nullable=False, index=True, comment="登录账号"
    )
    password_hash = db.Column(db.String(255), nullable=False, comment="密码哈希")
    real_name = db.Column(db.String(50), nullable=True, comment="姓名")
    role = db.Column(
        db.String(30), nullable=False, default="super_admin", comment="角色标识"
    )
    status = db.Column(
        db.SmallInteger, nullable=False, default=1, comment="1启用 0禁用"
    )
    last_login_at = db.Column(db.DateTime, nullable=True, comment="最后登录时间")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # ---- 密码 ----
    def set_password(self, raw_password):
        """加盐哈希存储，禁止明文。"""
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """校验密码。"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, raw_password)

    def to_dict(self):
        """对外序列化：绝不返回 password_hash。"""
        return {
            "id": self.id,
            "username": self.username,
            "real_name": self.real_name,
            "role": self.role,
            "status": self.status,
            "last_login_at": _fmt(self.last_login_at),
            "created_at": _fmt(self.created_at),
        }

    def __repr__(self):
        return "<Admin {0}>".format(self.username)


class Attraction(db.Model):
    """农文旅资源点位：古镇、果园、村落、景区。"""

    __tablename__ = "attraction"
    __table_args__ = MYSQL_TABLE_ARGS

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(
        db.String(100), unique=True, nullable=False, index=True, comment="资源名称"
    )
    category = db.Column(
        db.String(20), nullable=False, index=True, comment="类别：古镇/果园/村落/景区"
    )
    town = db.Column(
        db.String(50), nullable=True, index=True, comment="所属镇街（海宁市）"
    )
    address = db.Column(db.String(255), nullable=True, comment="详细地址")

    # GIS 坐标：Numeric(10,6) 精度约 0.1 米，足够村级点位
    longitude = db.Column(
        db.Numeric(10, 6), nullable=False, comment="经度 WGS84/GCJ02 待统一"
    )
    latitude = db.Column(
        db.Numeric(10, 6), nullable=False, comment="纬度 WGS84/GCJ02 待统一"
    )

    cover_image = db.Column(db.String(255), nullable=True, comment="封面图")
    images = db.Column(
        db.JSON,
        nullable=True,
        comment="轮播图，JSON 数组（最多 5 张），为空时回退 cover_image",
    )
    summary = db.Column(db.String(255), nullable=True, comment="一句话简介")
    description = db.Column(db.Text, nullable=True, comment="详情富文本")
    external_url = db.Column(
        db.String(255), nullable=True, comment="导流外链（淘宝/京东等，不做支付）"
    )

    status = db.Column(
        db.SmallInteger, nullable=False, default=1, comment="1上架 0下架"
    )
    view_count = db.Column(
        db.Integer, nullable=False, default=0, comment="累计浏览量"
    )
    sort = db.Column(db.Integer, nullable=False, default=0, comment="排序权重")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    @property
    def image_list(self):
        """轮播图数组：优先 images，其次 cover_image，最后空数组。"""
        raw = self.images
        items = raw if isinstance(raw, list) else []
        items = [u for u in items if isinstance(u, str) and u.strip()]
        if not items and self.cover_image:
            items = [self.cover_image]
        return items[:5]

    @property
    def purchase_url(self):
        """导流链接：只有「果园」类才生成淘宝购买入口。

        规则：
            1. 运营自定义的 external_url 优先（任何类别都可覆盖）；
            2. 否则仅 category == '果园' 时按名称生成淘宝搜索直达链接；
            3. 古镇 / 村落 / 景区没有实体商品，返回 None，前端不渲染购买区块。
        """
        custom = (self.external_url or "").strip()
        if custom and custom not in PLACEHOLDER_URLS:
            return custom
        if self.category != "果园":
            return None
        keyword = "海宁 {0}".format(self.name or "")
        return TAOBAO_SEARCH + quote(keyword, safe="")

    def to_dict(self):
        """经纬度转 float，前端 Leaflet 需要数值而非字符串。"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "town": self.town,
            "address": self.address,
            "longitude": float(self.longitude) if self.longitude is not None else None,
            "latitude": float(self.latitude) if self.latitude is not None else None,
            "cover_image": self.cover_image,
            "images": self.image_list,
            "summary": self.summary,
            "description": self.description,
            "external_url": self.external_url,
            "purchase_url": self.purchase_url,
            "status": self.status,
            "view_count": self.view_count,
            "sort": self.sort,
            "created_at": _fmt(self.created_at),
            "updated_at": _fmt(self.updated_at),
        }

    def to_map_dict(self):
        """地图打点用的轻量结构（不带富文本，减小传输体积）。"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "town": self.town,
            "longitude": float(self.longitude) if self.longitude is not None else None,
            "latitude": float(self.latitude) if self.latitude is not None else None,
            "summary": self.summary,
            "cover_image": self.cover_image,
            "images": self.image_list[:1],
            "view_count": self.view_count,
        }

    def __repr__(self):
        return "<Attraction {0}>".format(self.name)


class SystemLog(db.Model):
    """系统日志。

    source='web'        后台管理操作（登录、增删改）
    source='miniprogram' 小程序游客行为（浏览、点击外链）
    游客行为日志不绑定 admin_id，后台操作会带 admin_id。
    """

    __tablename__ = "system_log"
    __table_args__ = MYSQL_TABLE_ARGS

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    admin_id = db.Column(
        db.Integer, db.ForeignKey("admin.id", ondelete="SET NULL"), nullable=True
    )
    action = db.Column(
        db.String(50), nullable=False, index=True,
        comment="动作：login/view/click_external/create/update/delete",
    )
    target_type = db.Column(
        db.String(30), nullable=True, comment="目标类型：attraction/admin/system"
    )
    target_id = db.Column(db.Integer, nullable=True, comment="目标主键")
    detail = db.Column(db.String(500), nullable=True, comment="补充描述")
    ip = db.Column(db.String(64), nullable=True, comment="来源 IP")
    source = db.Column(
        db.String(20), nullable=False, default="web",
        comment="来源端：web / miniprogram",
    )
    user_agent = db.Column(db.String(255), nullable=True)
    session_id = db.Column(
        db.String(64),
        nullable=True,
        index=True,
        comment="设备级会话标识（小程序 UUID），用于 UV 去重",
    )
    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.now, index=True
    )

    admin = db.relationship("Admin", backref="logs", lazy="joined")

    @classmethod
    def record(cls, action, target_type=None, target_id=None, detail=None,
               admin_id=None, source="web", ip=None, user_agent=None,
               session_id=None, commit=True):
        """写入一条日志并返回实例（统一入口，便于后续加埋点）。"""
        log = cls(
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            admin_id=admin_id,
            source=source,
            ip=ip,
            user_agent=user_agent,
            session_id=session_id,
        )
        db.session.add(log)
        if commit:
            db.session.commit()
        return log

    def to_dict(self):
        return {
            "id": self.id,
            "admin_id": self.admin_id,
            "admin_name": self.admin.username if self.admin else None,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "detail": self.detail,
            "ip": self.ip,
            "source": self.source,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "created_at": _fmt(self.created_at),
        }

    def __repr__(self):
        return "<SystemLog {0}:{1}>".format(self.action, self.target_id)


class Favorite(db.Model):
    """游客收藏。

    平台没有账号体系，收藏绑定匿名设备会话号（session_id），
    同一设备对同一点位只能有一条记录（数据库唯一约束保证）。
    """

    __tablename__ = "favorite"
    __table_args__ = (
        db.UniqueConstraint(
            "session_id", "target_type", "target_id", name="uk_favorite"
        ),
        MYSQL_TABLE_ARGS,
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(
        db.String(64), nullable=False, index=True, comment="设备会话号"
    )
    target_type = db.Column(
        db.String(30), nullable=False, default="attraction", comment="目标类型"
    )
    target_id = db.Column(
        db.Integer, nullable=False, index=True, comment="目标主键"
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "created_at": _fmt(self.created_at),
        }

    def __repr__(self):
        return "<Favorite {0}->{1}>".format(self.session_id, self.target_id)
