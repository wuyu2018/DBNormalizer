# -*- coding: utf-8 -*-
# XMLIO：XML 导入/导出工具。
# 把一个“表(关系)”的结构（表名、属性、函数依赖、schema 名）序列化成 XML 文件，
# 或从 XML 文件还原这些信息。GUI 中未集成，仅供命令行示例使用。
__author__ = 'Paris'

from xml.etree import ElementTree as XmlTree   # 使用 Python 内置 XML 库
#import FDependency
#import FDependencyList
#import Relation
#fileHandler=open(path+filename,'r')

class XmlParsing:
    # 记录文件路径与文件名
    def __init__(self,Path=None,fileName=None, ):
        self.fileName=fileName
        self.Path=Path
        pass

    # 把一个表的 schema 与 FD 写入 XML 文件（导出）。
    # tableName：表名；attributeList：属性列表；
    # fdList：[(左部属性列表, 右部属性列表), ...]；schemaName：所属 schema 名；
    # exPath：输出目录。
    def writeTableToXML(self,tableName,attributeList,fdList,schemaName,exPath='/'):
        '''
        fdList is list of tuples of list of left and right hand fd
        fdList=[(['a','b'],['c']),([].[])....]
        '''
        # 构造 XML 树：configuration -> schema -> tableInfo -> table -> attributes / fds
        XmlRoot=XmlTree.Element('configuration')   # 根节点
        Schema=XmlTree.SubElement(XmlRoot,'schema',{'name':schemaName})   # schema 节点
        TableInfo=XmlTree.SubElement(Schema,"tableInfo")
        Table=XmlTree.SubElement(TableInfo,"table",{'name':tableName})    # 表节点
        attributes=XmlTree.SubElement(Table,"attributes")   # 属性容器
        fds=XmlTree.SubElement(Table,"fds")                # FD 容器

        # 逐个属性写为 <attribute>text</attribute>
        for att in attributeList:
            at=XmlTree.SubElement(attributes,"attribute")
            at.text=att
        # 每条 FD 写为 <fd><LHS>...</LHS><RHS>...</RHS></fd>
        for fd in fdList:
            felem=XmlTree.SubElement(fds,"fd")
            lh=fd[0] #fd.lh
            rh=fd[1] #fd.rh
            lhs=XmlTree.SubElement(felem,"LHS")
            rhs=XmlTree.SubElement(felem,"RHS")
            # 左部属性
            for la in lh:
                lat=XmlTree.SubElement(lhs,"attribute")
                lat.text=la
            # 右部属性
            for ra in rh:
                rat=XmlTree.SubElement(rhs,"attribute")
                rat.text=ra
        # 把整棵树写到文件
        Xtree=XmlTree.ElementTree(XmlRoot)
        Xtree.write(exPath+tableName+".xml")
        return 0

    # 读取 XML 文件并还原成字典（导入）。
    # 返回：{'Schema_Name':..,'Table_Name':..,'Column':[属性],'Dependency':[(左,右),...]}
    def readXMLToTable(self,fileName,pathName="/"):
        TableInfo=dict()
        Tree=XmlTree.parse(open(pathName+fileName,'r'))   # 解析文件
        treeRoot=Tree.getroot()
        #print(treeRoot.tag)
        schemaName=treeRoot[0].attrib['name']   # 取 schema 名
        tables=treeRoot.findall(".//schema/tableInfo/table")  # 定位表节点
        #for table in tables:
        table=tables[0]                          # 取第一张表
        tableName=table.attrib['name']
        attributes=table.findall("./attributes/attribute")    # 读属性
        #attributes=table.findall("./attributes/attribute")
        attList=list()
        for elem in attributes:
            attList.append(elem.text)            # 收集属性名文本
        #print("The attributes are:=",attList)
        FDs=table.findall("./fds/fd")            # 定位 FD 节点
        #FdList=FDependencylist()
        FdList=list()
        #print(FDs)
        for fd in FDs:
            lhs=[l.text for l in fd.findall("./LHS/attribute")]   # 左部属性列表
            rhs=[r.text for r in fd.findall("./RHS/attribute")]   # 右部属性列表
            FdList.append((lhs,rhs))
        # 组装返回字典
        TableInfo['Schema_Name']=schemaName
        TableInfo['Table_Name']=tableName
        TableInfo['Column']=attList
        TableInfo['Dependency']=FdList
        return TableInfo
