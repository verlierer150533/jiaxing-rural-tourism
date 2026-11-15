# -*- coding: utf-8 -*-
"""统一响应体与分页工具。

所有接口返回 {code, message, data}：
    code = 0 成功；非 0 失败（与 HTTP 状态码保持一致）
"""
from flask import jsonify


def ok(data=None, message="success"):
    """成功响应。"""
    return jsonify({"code": 0, "message": message, "data": data})


def fail(message, code=1, http_status=200):
    """失败响应。"""
    return jsonify({"code": code, "message": message, "data": None}), http_status


def paginate(query, page=1, page_size=10, max_page_size=100, serializer=None):
    """对 SQLAlchemy Query 分页并序列化。

    :param query: BaseQuery（未取值的查询对象）
    :param page: 页码，从 1 开始
    :param page_size: 每页条数
    :param max_page_size: 每页上限
    :param serializer: 单条序列化函数，默认调用对象的 to_dict()
    :return: dict(list/total/page/page_size/pages)
    """
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(page_size)
    except (TypeError, ValueError):
        page_size = 10

    page = max(1, page)
    page_size = max(1, min(page_size, max_page_size))

    total = query.order_by(None).count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    if serializer is None:
        serializer = lambda obj: obj.to_dict()  # noqa: E731

    pages = (total + page_size - 1) // page_size if page_size else 0
    return {
        "list": [serializer(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }
