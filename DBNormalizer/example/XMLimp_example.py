# -*- coding: utf-8 -*-
# 示例：XML 导入 —— 从 XML 文件读回某张表的属性与 FD 信息。
# 演示 readXMLToTable 的用法：返回字典含表名、属性列表、FD 元组列表。
# 需要自行调整 imPath 目录。
# 运行方式：python -m DBNormalizer.example.XMLimp_example
__author__ = 'Paris'

from DBNormalizer.example.relations import readDB_schema
from DBNormalizer.model.SQLParser import *
from DBNormalizer.model.Decomp import *
from DBNormalizer.model.XMLIO import *

'''
The correct path to folder should be specified for imPath
'''
imPath="/Users/mariaslanova/PycharmProjects/DBNormalizer/DBNormalizer/DBNormalizer/XML/XML_import/"  # XML 输入目录
N=Normalization()
D=Decomposition()
Xml=XmlParsing()
db = create_engine('postgresql://mariaslanova:@localhost/Test1')  # 连接数据库(此示例其实未使用库数据)
insp = inspect(db)
meta = MetaData()
meta.reflect(bind=db)

# 从 XML 文件读取表信息
tableinfo=Xml.readXMLToTable("table0.xml",imPath)
print(tableinfo['Table_Name'])     # 表名

reltn=set(tableinfo['Column'])     # 属性集合
print(reltn)
g=tableinfo['Dependency']          # FD 元组列表 [(lhs,rhs),...]
FDs=FDependencyList()
for t in g:
    FDs.append(FDependency(t[0],t[1]))   # 转换成 FDependency 对象
print(FDs)
