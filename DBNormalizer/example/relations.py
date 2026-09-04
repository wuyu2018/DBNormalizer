# -*- coding: utf-8 -*-
# 工具模块（供 example 目录内其他脚本复用）：
# 提供一个从 SQLAlchemy inspector 读取整个数据库模式、并把每张表构造成 Relation 的函数。
__author__ = 'Nantes'
from DBNormalizer.model.Relation import *
from sqlalchemy import *


#db = create_engine('postgresql://humberto:@localhost/birdie')
#insp = inspect(db)
# birdie.echo = True
#meta = MetaData()
#meta.reflect(bind=db)
#

# 读取数据库模式：输入 inspector，返回 {表名: Relation 对象}
def readDB_schema(db_inspector):
    db_schema = {}
    tables = db_inspector.get_table_names()   # 得到全部表名

    for name in tables:
        att = db_inspector.get_columns(name)            # 列信息
        pk = db_inspector.get_pk_constraint(name)       # 主键信息
        unique = db_inspector.get_unique_constraints(name)  # 唯一约束
        # 用表名 + 各 schema 信息构造 Relation 对象
        rel = Relation(name, schema_attributes=att, schema_keys=pk, schema_unique=unique)
        db_schema[name] = rel

    return db_schema

#relations = readDB_schema(insp)
#print(relations['buser'])
