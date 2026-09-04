# -*- coding: utf-8 -*-
# SQLParser：数据库(SQLAlchemy)与关系模型之间的桥梁工具。
# 负责：
#   - 从 inspector 的 schema 字典里抽取属性名/主键/唯一约束
#   - 对某个表执行 SQL，得到每个属性“取值相同”的行分区（用于 FD 挖掘）
#   - 把 schema 信息反向转成 SQLAlchemy Table/Column，用于生成 CREATE TABLE 语句
#   - 在分解时按列过滤 schema（decompose_schema_*）
# 注：项目使用的方言为 MySQL（get_attribute_partition 内的 SQL 使用 GROUP_CONCAT）。
__author__ = 'Nantes-Paris'

from sqlalchemy import *


# 从"列 schema 列表"(SQLAlchemy 返回的字典列表)中抽出某一属性值。
# 例：att_property='name' 得到所有列名；不传 attr_name 则返回全部列的该属性。
def get_schema_attribute_property(attr_schema, att_property='type', attr_name=None):
    attributes = []
    if attr_name is None:
        for x in attr_schema:
            attributes.append(x[att_property])
    else:
        attributes = [x[att_property] for x in attributes if x['name'] == attr_name]  # 注：原代码逻辑有误(用空列表)
    return attributes


# 取出主键约束中包含的列
def get_schema_keys(key_schema, key_property='constrained_columns'):
    return key_schema[key_property]


# 取出所有唯一约束的列（column_names）
def get_schema_unique(unique_schema, un_property='column_names'):
    unique = []
    for x in unique_schema:
        unique.append(x[un_property])
    return unique


# 对一个表的每个属性计算其取值分区，返回 {属性名: 分区列表}
def get_table_partitions(table, attributes, db):
    partitions = {}
    attr = len(attributes)
    for i in range(attr):
        partitions[attributes[i]] = get_attribute_partition(table, attributes[i],db)
    return partitions


# 生成“检测某两列组合是否有重复”的 SQL（TODO 未实现）
def get_duplicate_colums(table, lhs, rhs, conn):
    #TODO Not IMPLEMENTED
    lhs_c = lhs[:]
    rhs_c = rhs[:]
    left_attr = lhs_c.pop(0)
    right_att = rhs_c.pop(0)
    for i in lhs_c:
        left_attr = over + "," + i       # 注：over 变量未定义，属占位代码
    for i in rhs_c:
        right_att = over + "," + i
    query =  "select" + left_attr + ", count(*) from (select distinct " + left_attr + "," + right_att + \
             "from" + table + "group by" + left_attr + "having count(*) > 1"
    return query


# 核心：计算单属性 attribute 的取值分区。
# 思路：给每行分配行号，再按该列取值 GROUP_CONCAT 行号 -> 取值相同的行号聚成一块。
# 返回形如 [[1,3,5],[2,4],...] 的分区。
def get_attribute_partition(table, attribute, db):
    # 把 array_agg 改成 GROUP_CONCAT
    # 把 index 加上反引号 `index`，因为它是 MySQL 的保留字
    query = "select `" + attribute + "`," + " GROUP_CONCAT(`index`) as e from (select `" + attribute + "`,"  \
            "row_number() over() as `index` from " + table + ") as fool  group by `" + attribute + "`"
    with db.connect() as conn:                      # 建立连接执行查询
        execute = conn.execute(text(query)).fetchall()
    x = []                                          # 结果分区
    for row in execute:
        # GROUP_CONCAT 返回的是 "1,3,7" 这样的字符串，先按行号切成整数列表再交给 findFDs 处理，
        # 不能直接把整个字符串当 set 用（会把行号拆成单个字符，多位数/重复逗号时导致越界）。
        ids = [int(y) for y in row._mapping['e'].split(',')]
        if row._mapping[attribute] is None:
            # SQL 中 NULL != NULL，不能把所有 NULL 行合并成一个等价类，否则它们会被当成“取值相同”
            # 而误判函数依赖，因此把每个 NULL 行单独作为一个块。
            for rid in ids:
                x.append([rid])
        else:
            x.append(ids)
    return x

# 根据列/主键/唯一约束 schema 构建 SQLAlchemy Table 对象（用于 CREATE TABLE）
def parse_table(name, metadata, column_schema_list=None, pk_schema=None, unique_schema=None):
    table = Table(name, metadata)

    # Adds columns  添加列
    if column_schema_list:
        for k in column_schema_list:
            col = parse_column(k)
            table.append_column(col)

    # Adds primary key  添加主键约束
    if pk_schema:
        pk = PrimaryKeyConstraint(*pk_schema['constrained_columns'], name=pk_schema['name'])
        table.append_constraint(pk)

    # Adds unique constrain  添加唯一约束
    if unique_schema:
        for k in unique_schema:
            unique = UniqueConstraint(*k['column_names'], name=k['name'])
            table.append_constraint(unique)

    return table


# 把单个列 schema 字典转成 SQLAlchemy Column 对象
def parse_column(column_schema, primary_key=False, unique=False):
    name = column_schema['name']
    default = column_schema['default']
    c_type = column_schema['type']
    nullable = column_schema['nullable']
    autoincrement = column_schema['autoincrement']
    return Column(name, c_type, default=default, nullable=nullable, autoincrement=autoincrement,
                  primary_key=primary_key, unique=unique)


# 过滤出 over_attributes 中的列（用于子关系的 schema 构建）
def decompose_schema_attributes(schema, over_attributes):
    new_schema = [x for x in schema if x['name'] in over_attributes]
    return new_schema


# 只保留完全落在 over_attributes 之内的唯一约束（超出子关系范围的约束被丢弃）
def decompose_schema_unique(schema, over_attributes):
    new_schema = [x for x in schema if set(x['column_names']).issubset(set(over_attributes))]
    return new_schema


# 仅当主键列全部落在 over_attributes 内才保留主键，否则清空主键信息
def decompose_schema_pk(schema, over_attributes):
    if set(schema['constrained_columns']).issubset(set(over_attributes)):
        new_schema = schema
    else:
        new_schema = {}
    return new_schema


"""
Argument "table" should be an object of class table, argument
"db" should be an instance of create_engine().
autocommit parameter should be TRUE
"""
# 在数据库中真正创建该表
def Create_Table(table,db):
    table.metadata.create(db)

"""
Following methods replicates method Create_Table() but output is directed onto a .sql file
instead of database
"""
# 把建表语句写入 <表名>.sql 文件（而不是数据库）
def Create_Table_File(table):
    from sqlalchemy.schema import CreateTable
    filename = table.name + ".sql"
    f = open(filename,'w+')
    f.write(CreateTable(table.metadata))
    f.close()


"""
Arguments "main_table and subsume_of_main_tabletable" should be an object of class table,
argument "db" should be an instance of create_engine(), "over_attributes" are the list of attributes
that will be copied from main_table onto the subsume_of_main_tabletable.
autocommit parameter should be TRUE
"""
# 把主表中的若干列复制进子表（数据迁移）
def Copy_data(main_table,subsume_of_main_table,over_attributes,db):
    query = "SELECT " + over_attributes + " FROM " + main_table.name
    temp = db.execute(query)
    for row in temp:
        query = "INSERT INTO " + subsume_of_main_table.name + " VALUES(" + row +")"
        db.execute(query)

"""
Following methods replicates method Copy_data() but output is directed onto a .sql file
instead of database
"""
# 与 Copy_data 相同，但把 INSERT 语句写入文件
def Copy_data_file(main_table,subsume_of_main_table,over_attributes,db):
    query = "SELECT " + over_attributes + " FROM " + main_table.name
    temp = db.execute(query)
    filename = subsume_of_main_table.name + ".sql"
    f = open(filename,'a+')
    for row in temp:
        query = "INSERT INTO " + subsume_of_main_table.name + " VALUES(" + row +")"
        f.write("\n")
        f.write(query)
    f.close()

"""
Argument "table" should be an object of class table, argument
"db" should be an instance of create_engine().
autocommit parameter should be TRUE
"""
# 删除数据库中的表
def Drop_table(table,db):
    query = "DROP TABLE IF EXISTS " +table.name
    db.execute(query)


"""
Following methods replicates method Drop_table() but output is directed onto a .sql file
instead of database
"""
# 与 Drop_table 相同，但把 DROP 语句写入文件
def Drop_table_file(table):
    query = "DROP TABLE IF EXISTS " +table.name
    filename = table.name + ".sql"
    f = open(filename,'a+')
    f.write("\n")
    f.write(query)
    f.close()
