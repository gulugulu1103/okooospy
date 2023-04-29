import sqlite_utils

# 连接到SQLite数据库
db = sqlite_utils.Database("../example.db")

# 创建一个表
db["stocks"].create({"date": str, "trans": str, "symbol": str, "qty": float, "price": float})

# 插入一些数据
db["stocks"].insert_all([{"date": "2023-04-29", "trans": "BUY", "symbol": "AAPL", "qty": 100, "price": 200}])

# 查询数据
rows = db["stocks"].rows
for row in rows:
    print(row)
