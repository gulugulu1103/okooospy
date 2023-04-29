import sqlite_utils
from sqlite_utils import db


def insert_matches(match: list):
	db = sqlite_utils.Database("../data.db")
	db["matches"].insert_all(match, pk="match_id", replace = True)


if __name__ == "__main__":
	# 查询数据
	rows = db["matches"].rows
	for row in rows:
		print(row)
