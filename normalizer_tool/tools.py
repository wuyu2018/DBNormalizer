tools = [
    {
        "type": "function",
        "function": {
            "name": "submit_ddl",
            "description": "连接数据库并写入 DDL 和测试数据（会先清空库中的表）",
            "parameters": {
                "type": "object",
                "properties": {
                    "ddl":      {"type": "string", "description": "CREATE TABLE 语句"},
                    "data":     {"type": "string", "description": "INSERT INTO 语句"}
                },
                "required": ["ddl", "data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_all_tables",
            "description":"分析数据库是否符合用户所需要的达到的范式规范，如1NF、3NF、BCNF",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_nf":{"type": "string","description":"用户所想最终达到的范式级别"},
                },
                "required": ["target_nf"]
            }
        }
    }
]
