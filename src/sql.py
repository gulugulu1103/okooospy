from datetime import datetime

import sqlite_utils
from sqlite_utils import db


def clear_matches():
	db = sqlite_utils.Database("../data.db")
	db.execute("DELETE FROM matches")
	db.close()


def save_matches(match: list):
	db = sqlite_utils.Database("../data.db")
	db["matches"].insert_all(match, pk = "match_id", replace = True)
	db.close()


def read_matches() -> list:
	db = sqlite_utils.Database("../data.db")
	rows = db.execute("SELECT * FROM matches").fetchall()
	db.close()
	return rows


def save_initial_odds(data):
	db = sqlite_utils.Database("../data.db")
	# data : [{'providerId': 14, '1206393': ['2.05', '3.30', '3.20'], '1206406': ['2.45', '3.10', '2.70'], '1207296':
	# ['1.40', '3.90', '7.00'], '1206413': ['2.50', '3.30', '2.50']}]
	for item in data:
		provider_id = item['providerId']
		for match_id, odds in item.items():
			if match_id == 'providerId':
				continue
			win_odds, draw_odds, lose_odds = map(float, odds)
			db['initial_odds'].insert({
				'match_id'   : match_id,
				'provider_id': provider_id,
				'win_odds'   : win_odds,
				'draw_odds'  : draw_odds,
				'lose_odds'  : lose_odds
			}, pk = ('match_id', 'provider_id'))
	db.close()


def save_odds(data):
	db = sqlite_utils.Database("../data.db")
	# data : [{'providerId': 14, '1206393': ['2.05', '3.30', '3.20'], '1206406': ['2.45', '3.10', '2.70'], '1207296':
	# ['1.40', '3.90', '7.00'], '1206413': ['2.50', '3.30', '2.50']}]
	for item in data:
		provider_id = item['providerId']
		for match_id, odds in item.items():
			if match_id == 'providerId' or odds == []:
				continue
			win_odds, draw_odds, lose_odds = map(str, odds)
			db['odds'].insert({
				'match_id'       : match_id,
				'provider_id'    : provider_id,
				'time'           : datetime.now(),  # 添加当前时间作为时间戳
				'final_win_odds' : win_odds,
				'final_draw_odds': draw_odds,
				'final_lose_odds': lose_odds
			}, pk = ('match_id', 'provider_id'))
	db.close()


if __name__ == "__main__":
	# 查询数据
	rows = db["matches"].rows
	for row in rows:
		print(row)
