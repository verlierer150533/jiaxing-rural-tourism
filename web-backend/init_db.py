# -*- coding: utf-8 -*-
"""数据库初始化 / 测试数据脚本（幂等，可重复执行）。

用法：
    python init_db.py                 只建库建表 + 基础种子（管理员 + 12 个点位）
    python init_db.py --demo          额外生成近 7 天测试日志（约 400 条），供大屏演示
    python init_db.py --demo --reset-logs   先清空 system_log 再生成，便于反复演示
"""
import argparse
import random
import sys
from datetime import datetime, timedelta

import pymysql
from sqlalchemy import func, text

from app import create_app
from config import get_config
from models import Admin, Attraction, Favorite, SystemLog, db

CFG = get_config()

SEED_ADMIN = {
    "username": "admin",
    "password": "admin123",
    "real_name": "系统管理员",
    "role": "super_admin",
}

# 经纬度先取公开地图初值，第 4 步在 Leaflet 地图上目视校验后再精修
SEED_ATTRACTIONS = [
    {
        "name": "盐官古镇",
        "category": "古镇",
        "town": "盐官镇",
        "address": "浙江省嘉兴市海宁市盐官镇观潮胜地公园",
        "longitude": 120.525300,
        "latitude": 30.393700,
        "summary": "钱塘江观潮胜地，海神庙、陈阁老宅与宰相府第风情街所在的历史古镇。",
        "description": (
            "盐官古镇位于海宁市盐官镇，是钱塘江大潮的最佳观潮地之一，"
            "农历八月十八前后可观“一线潮”“回头潮”。镇内保存海神庙、陈阁老宅、"
            "王国维故居等古迹，并与百里钱塘生态绿带相连，适合农文旅精品线路串联。"
        ),
        "external_url": None,
        # 轮播图占位：picsum 为 https 公共图床，归档前请替换为实拍图
        "images": [
            "https://picsum.photos/seed/yanguan-1/800/520",
            "https://picsum.photos/seed/yanguan-2/800/520",
            "https://picsum.photos/seed/yanguan-3/800/520",
        ],
        "sort": 10,
    },
    {
        "name": "大尖山果园",
        "category": "果园",
        "town": "黄湾镇",
        "address": "浙江省嘉兴市海宁市黄湾镇大尖山景区一带",
        "longitude": 120.846300,
        "latitude": 30.336200,
        "summary": "黄湾镇“水果之乡”核心采摘区，13000 余亩果园四季有果。",
        "description": (
            "黄湾镇是浙北闻名的“水果之乡”，拥有 13000 多亩果园，"
            "一年四季瓜果不断：1 月葡萄柚、2 月沃柑、3 月黄美人、4 月樱桃、"
            "5 月枇杷、6 月杨梅、7 月桃子、8 月火龙果、9 月葡萄、"
            "10—11 月橘子、12 月红美人与泰国青柚。大尖山景区一带集聚采摘园、"
            "滑翔伞基地与露营营地，是海宁百里钱塘国际旅游长廊的第一站。"
        ),
        "external_url": None,
        "images": [
            "https://picsum.photos/seed/orchard-1/800/520",
            "https://picsum.photos/seed/orchard-2/800/520",
            "https://picsum.photos/seed/orchard-3/800/520",
        ],
        "sort": 20,
    },
    {
        "name": "南关厢历史文化街区",
        "category": "村落",
        "town": "硖石街道",
        "address": "浙江省嘉兴市海宁市硖石街道南关厢",
        "longitude": 120.685600,
        "latitude": 30.509800,
        "summary": "海宁市区保存最完整的江南历史街区，非遗与市井生活交融。",
        "description": (
            "南关厢历史文化街区位于海宁硖石，沿市河而建，保留清末民初街巷格局，"
            "周边有徐志摩故居、衍芬草堂等人文点位，常年举办非遗市集与民俗活动，"
            "是“古镇 + 非遗 + 夜游”型农文旅线路的重要节点。"
        ),
        "external_url": None,
        "sort": 30,
    },
    {
        "name": "金庸故居",
        "category": "村落",
        "town": "袁花镇",
        "address": "浙江省嘉兴市海宁市袁花镇新伟村",
        "longitude": 120.744000,
        "latitude": 30.453000,
        "summary": "查良镛（金庸）先生故里，武侠文化主题人文点位。",
        "description": (
            "金庸故居位于海宁市袁花镇，是查良镛先生出生与少年生活之地，"
            "周边配套赫山房、武侠文化展陈，适合与袁花果园采摘串联成一日线路。"
        ),
        "external_url": None,
        "sort": 40,
    },
    {
        "name": "徐志摩故居",
        "category": "村落",
        "town": "硖石街道",
        "address": "浙江省嘉兴市海宁市硖石街道干河街",
        "longitude": 120.687000,
        "latitude": 30.512500,
        "summary": "诗人徐志摩出生地，中西合璧式民宅，与南关厢步行可达。",
        "description": (
            "徐志摩故居坐落于海宁硖石干河街，为中西合璧式砖木结构住宅，"
            "内设诗人生平陈列，与南关厢历史文化街区构成市区人文游核心。"
        ),
        "external_url": None,
        "sort": 50,
    },
    {
        "name": "海宁中国皮革城",
        "category": "景区",
        "town": "海洲街道",
        "address": "浙江省嘉兴市海宁市海州西路 201 号",
        "longitude": 120.674300,
        "latitude": 30.520600,
        "summary": "全国性皮革专业市场，购物型文旅节点，客流基数大。",
        "description": (
            "海宁中国皮革城是全国知名的皮革制品集散中心，配套会展、餐饮与酒店，"
            "是海宁“购物 + 旅游”线路的固定节点，也是本文客流统计的重点观察对象。"
        ),
        "external_url": None,
        "sort": 60,
    },
    {
        "name": "长安古镇",
        "category": "古镇",
        "town": "长安镇",
        "address": "浙江省嘉兴市海宁市长安镇",
        "longitude": 120.594700,
        "latitude": 30.458600,
        "summary": "运河古镇，长安闸遗址与老街市井并存。",
        "description": (
            "长安古镇因运河而兴，保存长安闸等运河遗产，老街仍有传统商铺与手作，"
            "适合与大运河文化线路结合，形成“古镇 + 运河”研学产品。"
        ),
        "external_url": None,
        "sort": 70,
    },
    {
        "name": "百里钱塘生态绿带",
        "category": "景区",
        "town": "盐官镇",
        "address": "浙江省嘉兴市海宁市盐官镇沿钱塘江北岸",
        "longitude": 120.560000,
        "latitude": 30.405000,
        "summary": "沿钱塘江展开的生态廊道，骑行与观潮露营热门地。",
        "description": (
            "百里钱塘生态绿带沿钱塘江北岸铺展，串联盐官古城、观潮点与露营营地，"
            "是海宁“潮文化 + 生态休闲”线路的主轴。"
        ),
        "external_url": None,
        "sort": 80,
    },
    {
        "name": "尖山滑翔伞基地",
        "category": "景区",
        "town": "黄湾镇",
        "address": "浙江省嘉兴市海宁市黄湾镇尖山新区",
        "longitude": 120.855000,
        "latitude": 30.345000,
        "summary": "省级运动休闲优秀项目，滑翔伞追潮与山地露营。",
        "description": (
            "尖山滑翔伞基地是浙江省运动休闲旅游优秀项目之一，"
            "可空中俯瞰钱塘江与万亩果园，与黄湾水果采摘季形成“采摘 + 户外”组合。"
        ),
        "external_url": None,
        "sort": 90,
    },
    {
        "name": "黄湾潮汐树拍摄点",
        "category": "景区",
        "town": "黄湾镇",
        "address": "浙江省嘉兴市海宁市黄湾镇杭州湾北翼滩涂",
        "longitude": 120.870000,
        "latitude": 30.360000,
        "summary": "钱塘江滩涂“潮汐树”奇观，四季出片的摄影打卡点。",
        "description": (
            "潮汐树是潮水冲刷滩涂形成的树枝状纹理，黄湾镇坐拥多处绝佳拍摄点位，"
            "已积累稳定的摄影客群，适合作为平台“内容引流 + 活动运营”的案例点位。"
        ),
        "external_url": None,
        "sort": 100,
    },
    {
        "name": "袁花果园",
        "category": "果园",
        "town": "袁花镇",
        "address": "浙江省嘉兴市海宁市袁花镇",
        "longitude": 120.739000,
        "latitude": 30.447000,
        "summary": "海宁东部采摘片区，柑橘与枇杷为主要品类。",
        "description": (
            "袁花镇果园集中分布在镇域南部，以柑橘、枇杷采摘为主，"
            "与金庸故居相邻，便于构建“人文 + 采摘”半日游线路。"
        ),
        "external_url": None,
        "sort": 110,
    },
    {
        "name": "斜桥农事体验点",
        "category": "果园",
        "town": "斜桥镇",
        "address": "浙江省嘉兴市海宁市斜桥镇",
        "longitude": 120.612000,
        "latitude": 30.470000,
        "summary": "农事体验与榨菜文化展示，面向亲子研学客群。",
        "description": (
            "斜桥镇以榨菜等传统农产品加工闻名，农事体验点提供种植、采收与"
            "加工参观，适合亲子研学与劳动教育，是“农业 + 研学”型点位。"
        ),
        "external_url": None,
        "sort": 120,
    },
]

# 演示用伪设备号（明确标记 demo，避免与真实数据混淆）
DEMO_SESSIONS = ["demo-sess-{0:03d}".format(i) for i in range(1, 61)]
DEMO_SEARCH_WORDS = ["杨梅", "枇杷", "古镇", "观潮", "采摘", "滑翔伞", "非遗", "亲子"]
DEMO_WORK_HOURS = [9, 10, 10, 11, 11, 12, 13, 14, 14, 15, 15, 16, 16, 17, 18, 19, 19, 20, 21]


def ensure_database():
    """连接 MySQL 服务器（不指定库），确保目标库存在。"""
    try:
        conn = pymysql.connect(
            host=CFG.MYSQL_HOST,
            port=CFG.MYSQL_PORT,
            user=CFG.MYSQL_USER,
            password=CFG.MYSQL_PASSWORD,
            charset="utf8mb4",
            autocommit=True,
            connect_timeout=10,
        )
    except Exception as exc:
        print("[ERROR] 无法连接 MySQL：{0}".format(exc))
        print("        请确认 MySQL80 服务已启动，账号 {0} / 空密码".format(CFG.MYSQL_USER))
        raise

    try:
        with conn.cursor() as cur:
            cur.execute(
                "CREATE DATABASE IF NOT EXISTS `{0}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci".format(
                    CFG.MYSQL_DATABASE
                )
            )
            cur.execute("SHOW DATABASES LIKE %s", (CFG.MYSQL_DATABASE,))
            print("[1/5] 数据库就绪: {0}".format(cur.fetchone()[0]))
    finally:
        conn.close()


def create_tables(app):
    """建表（已存在则跳过）。"""
    with app.app_context():
        db.create_all()
        rows = db.session.execute(
            text(
                "SELECT TABLE_NAME, TABLE_COLLATION FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA = :schema ORDER BY TABLE_NAME"
            ),
            {"schema": CFG.MYSQL_DATABASE},
        ).fetchall()
        for name, collation in rows:
            print("[2/5] 表: {0:<12} {1}".format(name, collation))
        return [row[0] for row in rows]


def ensure_schema(app):
    """补齐 create_all 无法处理的增量字段（session_id）。"""
    with app.app_context():
        columns = db.session.execute(
            text(
                "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = 'system_log'"
            ),
            {"schema": CFG.MYSQL_DATABASE},
        ).fetchall()
        names = {row[0] for row in columns}
        if "session_id" not in names:
            db.session.execute(
                text(
                    "ALTER TABLE system_log ADD COLUMN session_id VARCHAR(64) NULL "
                    "COMMENT '设备级会话标识，用于 UV 去重'"
                )
            )
            db.session.execute(
                text("ALTER TABLE system_log ADD INDEX idx_log_session (session_id)")
            )
            db.session.commit()
            print("[3/5] 已补充字段 system_log.session_id")
        else:
            print("[3/5] 字段 system_log.session_id 已存在")

        # ---- attraction.images（详情页轮播图，JSON 数组）----
        attraction_columns = db.session.execute(
            text(
                "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = 'attraction'"
            ),
            {"schema": CFG.MYSQL_DATABASE},
        ).fetchall()
        attraction_names = {row[0] for row in attraction_columns}
        if "images" not in attraction_names:
            db.session.execute(
                text(
                    "ALTER TABLE attraction ADD COLUMN images JSON NULL "
                    "COMMENT '轮播图JSON数组，最多5张'"
                )
            )
            db.session.commit()
            print("[3/5] 已补充字段 attraction.images")
        else:
            print("[3/5] 字段 attraction.images 已存在")


def seed_base(app):
    """基础种子：管理员 + 12 个资源点位。"""
    with app.app_context():
        admin = Admin.query.filter_by(username=SEED_ADMIN["username"]).first()
        if admin is None:
            admin = Admin(
                username=SEED_ADMIN["username"],
                real_name=SEED_ADMIN["real_name"],
                role=SEED_ADMIN["role"],
            )
            admin.set_password(SEED_ADMIN["password"])
            db.session.add(admin)
            print("[4/5] 新增管理员: {0} / {1}".format(
                SEED_ADMIN["username"], SEED_ADMIN["password"]))
        else:
            print("[4/5] 管理员已存在: {0}".format(admin.username))

        created, skipped = 0, 0
        for item in SEED_ATTRACTIONS:
            if Attraction.query.filter_by(name=item["name"]).first():
                skipped += 1
                continue
            db.session.add(Attraction(**item))
            created += 1

        db.session.commit()
        print("[4/5] 资源点位: 新增 {0} 条，跳过 {1} 条".format(created, skipped))

        # ---- 已有库的轮播图回填（幂等：只补空值，不覆盖已配好的图）----
        backfilled = 0
        for item in SEED_ATTRACTIONS:
            images = item.get("images")
            if not images:
                continue
            record = Attraction.query.filter_by(name=item["name"]).first()
            if record is not None and not record.images:
                record.images = list(images)
                backfilled += 1
        if backfilled:
            db.session.commit()
            print("[4/5] 轮播图回填: {0} 条".format(backfilled))

        # ---- 清理早期的"商城首页"占位外链（改由 purchase_url 生成淘宝搜索链接）----
        cleared = (
            Attraction.query.filter(
                Attraction.external_url.in_(
                    [
                        "https://www.taobao.com",
                        "https://taobao.com",
                        "https://www.tmall.com",
                        "https://www.jd.com",
                        "https://jd.com",
                    ]
                )
            ).update({Attraction.external_url: None}, synchronize_session=False)
        )
        if cleared:
            db.session.commit()
            print("[4/5] 清理首页占位外链: {0} 条".format(cleared))


def seed_demo_logs(app, reset=False):
    """生成近 7 天测试日志，并把 view_count 与日志对齐。"""
    with app.app_context():
        if reset:
            deleted = SystemLog.query.delete()
            db.session.commit()
            print("[demo] 已清空 system_log：{0} 条".format(deleted))

        if SystemLog.query.count() > 0:
            print("[demo] system_log 已有数据，跳过生成（如需重灌请加 --reset-logs）")
            _sync_view_count()
            return

        attractions = Attraction.query.filter(Attraction.status == 1).all()
        if not attractions:
            print("[demo] 没有可用点位，跳过")
            return

        random.seed(20271104)  # 固定种子，保证每次生成结果可复现
        now = datetime.now()
        logs = []

        # ---- 后台登录日志 ----
        for _ in range(12):
            day = now - timedelta(days=random.randint(0, 6))
            logs.append(
                SystemLog(
                    action="login",
                    target_type="admin",
                    target_id=1,
                    detail="演示登录记录",
                    admin_id=1,
                    source="web",
                    ip="127.0.0.1",
                    user_agent="demo-agent",
                    created_at=day.replace(
                        hour=random.choice([8, 9, 13, 14, 17]),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59),
                    ),
                )
            )

        # ---- 小程序游客足迹 ----
        for offset in range(7):
            day = (now - timedelta(days=6 - offset)).date()
            daily_count = random.randint(45, 75)
            for _ in range(daily_count):
                roll = random.random()
                if roll < 0.70:
                    action = "view"
                elif roll < 0.90:
                    action = "click_external"
                else:
                    action = "search"

                target = random.choice(attractions)
                created = datetime(
                    day.year,
                    day.month,
                    day.day,
                    random.choice(DEMO_WORK_HOURS),
                    random.randint(0, 59),
                    random.randint(0, 59),
                )
                if action == "search":
                    logs.append(
                        SystemLog(
                            action="search",
                            target_type="system",
                            target_id=None,
                            detail="关键词搜索：{0}".format(random.choice(DEMO_SEARCH_WORDS)),
                            source="miniprogram",
                            ip="116.23.{0}.{1}".format(
                                random.randint(1, 254), random.randint(1, 254)),
                            user_agent="MicroMessenger demo",
                            session_id=random.choice(DEMO_SESSIONS),
                            created_at=created,
                        )
                    )
                else:
                    logs.append(
                        SystemLog(
                            action=action,
                            target_type="attraction",
                            target_id=target.id,
                            detail="{0} {1}".format(
                                "查看详情" if action == "view" else "跳转外链",
                                target.name,
                            ),
                            source="miniprogram",
                            ip="116.23.{0}.{1}".format(
                                random.randint(1, 254), random.randint(1, 254)),
                            user_agent="MicroMessenger demo",
                            session_id=random.choice(DEMO_SESSIONS),
                            created_at=created,
                        )
                    )

        db.session.add_all(logs)
        db.session.commit()
        print("[demo] 生成测试日志 {0} 条（近 7 天）".format(len(logs)))
        _sync_view_count()


def _sync_view_count():
    """让 attraction.view_count 与 view 日志条数一致，保证大屏口径统一。"""
    rows = (
        db.session.query(SystemLog.target_id, func.count(SystemLog.id))
        .filter(
            SystemLog.action == "view",
            SystemLog.target_type == "attraction",
            SystemLog.target_id.isnot(None),
        )
        .group_by(SystemLog.target_id)
        .all()
    )
    counts = {int(target_id): int(count) for target_id, count in rows}
    for attraction in Attraction.query.all():
        attraction.view_count = counts.get(attraction.id, 0)
    db.session.commit()


def report(app):
    """打印结果，作为验证依据。"""
    from api.stats import today_metrics

    with app.app_context():
        print("-" * 76)
        print("表数据量：admin={0}  attraction={1}  system_log={2}  favorite={3}".format(
            Admin.query.count(), Attraction.query.count(),
            SystemLog.query.count(), Favorite.query.count()))
        print("今日指标：{0}".format(today_metrics()))
        print("-" * 76)
        print("{0:<4}{1:<24}{2:<7}{3:<9}{4:>12}{5:>12}{6:>8}".format(
            "ID", "名称", "类别", "镇街", "经度", "纬度", "浏览量"))
        for a in Attraction.query.order_by(Attraction.sort, Attraction.id).all():
            print("{0:<4}{1:<24}{2:<7}{3:<9}{4:>12}{5:>12}{6:>8}".format(
                a.id, a.name, a.category, a.town or "-",
                float(a.longitude), float(a.latitude), a.view_count))
        print("-" * 76)
        top = (
            Attraction.query.order_by(Attraction.view_count.desc())
            .limit(5)
            .all()
        )
        print("热度 Top5：" + "，".join(
            "{0}({1})".format(a.name, a.view_count) for a in top))
        print("-" * 76)


def main():
    parser = argparse.ArgumentParser(description="初始化农文旅平台数据库")
    parser.add_argument("--demo", action="store_true", help="生成近 7 天测试日志")
    parser.add_argument("--reset-logs", action="store_true", help="先清空 system_log 再生成")
    args = parser.parse_args()

    print("=" * 76)
    print(" 初始化数据库：{0}@{1}:{2}/{3}".format(
        CFG.MYSQL_USER, CFG.MYSQL_HOST, CFG.MYSQL_PORT, CFG.MYSQL_DATABASE))
    print(" 参数：demo={0} reset_logs={1}".format(args.demo, args.reset_logs))
    print("=" * 76)

    ensure_database()
    app = create_app("development")
    create_tables(app)
    ensure_schema(app)
    seed_base(app)

    if args.demo or args.reset_logs:
        seed_demo_logs(app, reset=args.reset_logs)
    else:
        print("[5/5] 未指定 --demo，跳过测试日志")

    report(app)
    print("完成。登录账号：{0} / {1}".format(
        SEED_ADMIN["username"], SEED_ADMIN["password"]))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("[FAILED] 初始化失败: {0}: {1}".format(type(exc).__name__, exc))
        sys.exit(1)
