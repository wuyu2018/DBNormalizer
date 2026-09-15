# -*- coding: utf-8 -*-
# ConnectionStore：持久化“以前连接过的数据库”信息。
# 把 host/port/username/password/database 存到用户目录下的 JSON 文件，
# 下次启动时读取，供连接面板的下拉框“选择即一键填写”。
#
# 注意：为支持一键填写，密码以明文保存在本机用户目录，请勿在共享机器上使用。
__author__ = 'Nantes'

import json
from pathlib import Path

# 存储位置：用户目录下，避免污染项目仓库
STORE_PATH = Path.home() / ".dbnormalizer" / "connections.json"


def load_connections():
    """读取全部历史连接，返回 list[dict]（文件不存在或损坏时返回空列表）。"""
    try:
        with open(STORE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def _key(conn):
    return (conn.get("host"), conn.get("port"),
            conn.get("username"), conn.get("database"))


def save_connection(conn):
    """保存一条连接：按 (host, port, username, database) 去重并置顶。"""
    conns = load_connections()
    key = _key(conn)
    conns = [c for c in conns if _key(c) != key]
    conns.insert(0, conn)

    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(conns, f, ensure_ascii=False, indent=2)
    return conns


def connection_label(conn):
    """生成下拉框显示用的标签。"""
    return "%s@%s:%s/%s" % (conn.get("username", ""), conn.get("host", ""),
                            conn.get("port", ""), conn.get("database", ""))
