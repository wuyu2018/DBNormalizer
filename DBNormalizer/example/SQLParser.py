# -*- coding: utf-8 -*-
# 示例（PostgreSQL 专用）：演示把数据库里的表转换为 SQLAlchemy 的 Table 对象，
# 并（可）生成 CREATE TABLE 语句/创建子关系。顶部连接串与库需要自行调整。
# 运行方式：python -m DBNormalizer.example.SQLParser
__author__ = 'Nantes'

from DBNormalizer.model.Relation import *
from sqlalchemy import *
from sqlalchemy.dialects.postgresql import *
from sqlalchemy.schema import CreateTable
from psycopg2 import *

# This function read the whole DB and returns a dictionary where the keys are the relation names
# 读取整库，返回 {表名: Relation}
def readDB_schema(db_inspector):
    db_schema = {}
    tables = db_inspector.get_table_names()

    for name in tables:
        att = db_inspector.get_columns(name)
        pk = db_inspector.get_pk_constraint(name)
        unique = db_inspector.get_unique_constraints(name)
        rel = Relation(name, schema_attributes=att, schema_keys=pk, schema_unique=unique)
        db_schema[name] = rel

    return db_schema


# Create connection to DB
# The db used in this example is the one Gabriela sent in skype
# 连接数据库（示例库 birdie）
db = create_engine('postgresql://humberto:@localhost/birdie')
meta = MetaData()
meta.reflect(bind=db)
# This thing read the whole schema this is the base to create the Relation objects
# 读取整个 schema，作为构造 Relation 对象的基础
insp = inspect(db)

# Call to the function defined above
# 调用上面定义的函数，得到 {表名: Relation}
relations = readDB_schema(insp)
# Creates a meta2 object to store the Table constructions
# 创建新的 MetaData 用于存放将要构造的 Table
meta2 = MetaData()
t1 = relations['buser'].SQL_statement(meta2)   # 把 buser 表转成 SQLAlchemy Table 对象
print(relations['buser'])
#t2 = relations['dependent'].SQL_statement(meta2)
#t3 = relations['employee_project'].SQL_statement(meta2)

# Print create table statements:
# 打印建表语句
# NOTE: for some reason it is not working with point datatype in posgreSQL
# 注意：在 PostgreSQL 中因 point 数据类型问题，下面语句可能无法工作
#print(CreateTable(t1))
#print(CreateTable(t2))
#print(CreateTable(t3))
# This will try to write in the database (now is not working as no engine is binded to meta2)
# 尝试真正在数据库中建表（因 meta2 未绑定 engine，暂不工作）
# meta2.create_all()

# A subrelation of a relation. The sub-relation is obtained from the attributes that are passed to this function:
# 创建子关系的示例：从原关系按给定属性抽出一个子关系
# Read the Relation function as more capabilities are needed.
#t3_sub = relations['employee_project'].sub_relation('employee_project_new', ['ssn', 'superssn', 'plocation'])
# Print relation object
#print(t3_sub)
# Print query of new relation object
#print(CreateTable(t3_sub.SQL_statement(meta2)))
