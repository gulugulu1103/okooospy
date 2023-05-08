from typing import Dict, List, Tuple


class SoccerMatch:
	def __init__(self):
		self.match_id = None # 比赛ID
		self.league = None  # 联赛名称
		self.match_time = None  # 比赛时间
		self.home_team = None  # 主队名称
		self.away_team = None  # 客队名称
		self.handicap = None  # 让球值

		self.odds: Dict[str, Dict[str, List[float]]] = { }  # 存储赔率信息
		self.asian_handicaps: Dict[str, Dict[str, Tuple[float, str, float]]] = { }  # 存储亚盘信息
		self.profit_loss: Dict[str, Dict[str, List[int]]] = { }  # 存储盈亏指数
		self.match_history: Dict[str, str] = { }  # 存储比赛历史
		self.handicap_odds: Dict[str, List[float]] = { }  # 存储让球指数

	# 添加赔率信息
	def add_odds(self, company: str, initial_odds: List[float], current_odds: List[float], current_kelly: List[float]):
		self.odds[company] = {
			"initial"      : initial_odds,
			"current"      : current_odds,
			"current_kelly": current_kelly
		}

	# 更新赔率信息
	def update_odds(self, company: str, updated_odds: List[float], updated_kelly: List[float]):
		if company in self.odds:
			self.odds[company]["updated"] = updated_odds
			self.odds[company]["updated_kelly"] = updated_kelly

	# 添加亚盘信息
	def add_asian_handicap(self, company: str, initial_handicap: Tuple[float, str, float],
	                       current_handicap: Tuple[float, str, float]):
		self.asian_handicaps[company] = {
			"initial": initial_handicap,
			"current": current_handicap
		}

	# 更新亚盘信息
	def update_asian_handicap(self, company: str, updated_handicap: Tuple[float, str, float]):
		if company in self.asian_handicaps:
			self.asian_handicaps[company]["updated"] = updated_handicap

	# 添加让球信息
	def add_handicap_odds(self, company: str, initial_odds: List[float],
	                      current_odds: List[float]):
		self.handicap_odds[company] = {
			"initial": initial_odds,
			"current": current_odds
		}

	# 更新让球信息
	def update_handicap_odds(self, company: str, updated_odds: List[float]):
		if company in self.handicap_odds:
			self.handicap_odds[company]["updated"] = updated_odds

	# 添加盈亏指数
	def add_profit_loss(self, company: str, initial_profit_loss: List[int]):
		self.profit_loss[company] = {
			"initial": initial_profit_loss
		}

	def update_profit_loss(self, company: str, updated_profit_loss: List[int]):
		if company in self.profit_loss:
			self.profit_loss[company]["updated"] = updated_profit_loss

	# 添加比赛历史
	def add_match_history(self, history_type: str, history: str):
		self.match_history[history_type] = history


def test_soccer_match():
	match = SoccerMatch(league = "Super League",
	                    match_time = "2023-05-10 19:30",
	                    home_team = "Team A",
	                    away_team = "Team B",
	                    handicap = 1)

	# 添加赔率信息
	match.add_odds(company = "99家平均",
	               initial_odds = [2.0, 3.5, 4.0],
	               current_odds = [1.9, 3.6, 4.1],
	               current_kelly = [0.93, 0.87, 0.34])
	match.add_odds(company = "威廉希尔",
	               initial_odds = [2.0, 3.5, 4.0],
	               current_odds = [1.9, 3.6, 4.1],
	               current_kelly = [0.93, 0.87, 0.34])

	# 添加亚盘信息
	match.add_asian_handicap(company = "澳门",
	                         initial_handicap = (0.9, "受让一球", 1.1),
	                         current_handicap = (0.95, "受让一球", 1.05))
	match.add_asian_handicap(company = "Interwetten",
	                         initial_handicap = (0.9, "受让一球", 1.1),
	                         current_handicap = (0.95, "受让一球", 1.05))
	match.add_asian_handicap(company = "金宝博",
	                         initial_handicap = (0.9, "受让一球", 1.1),
	                         current_handicap = (0.95, "受让一球", 1.05))

	# 添加盈亏指数
	match.add_profit_loss(company = "必发",
	                      initial_profit_loss = [100, 200, 300])
	match.add_profit_loss(company = "竞彩",
	                      initial_profit_loss = [100, 200, 300])

	# 添加比赛历史
	match.add_match_history(history_type = "交战历史",
	                        history = "3011001330")
	match.add_match_history(history_type = "主队历史",
	                        history = "1300001000")
	match.add_match_history(history_type = "客队历史",
	                        history = "0100113100")

	# 更新赔率信息
	match.update_odds(company = "99家平均",
	                  updated_odds = [1.8, 3.7, 4.2],
	                  updated_kelly = 0.95)
	match.update_odds(company = "bet365",
	                  updated_odds = [1.8, 3.7, 4.2],
	                  updated_kelly = 0.95)

	# 更新亚盘信息
	match.update_asian_handicap(company = "澳门",
	                            updated_handicap = (0.98, "受让一球", 1.02))
	match.update_asian_handicap(company = "澳门",
	                            updated_handicap = (0.98, "受让一球", 1.02))

	# 输出比赛信息
	print(f"联赛：{match.league}")
	print(f"比赛时间：{match.match_time}")
	print(f"主队：{match.home_team}")
	print(f"客队：{match.away_team}")
	print(f"让球值：{match.handicap}")

	print("\n赔率信息：")
	for company, odds in match.odds.items():
		print(
				f"{company} - 初始赔率：{odds['initial']}，即时赔率：{odds['current']}，即时凯利指数：{odds['current_kelly']}，更新赔率：{odds.get('updated')}，更新凯莉指数：{odds.get('updated_kelly')}")

	print("\n亚盘信息：")
	for company, handicaps in match.asian_handicaps.items():
		print(
				f"{company} - 初始亚盘：{handicaps['initial']}，即时亚盘：{handicaps['current']}，更新亚盘：{handicaps.get('updated')}")

	print("\n盈亏指数：")
	for company, profit_loss in match.profit_loss.items():
		print(f"{company} - 初始盈亏指数：{profit_loss['initial']}，即时盈亏指数：{profit_loss['current']}")

	print("\n比赛历史：")
	for history_type, history in match.match_history.items():
		print(f"{history_type}：{history}")


if __name__ == "__main__":
	test_soccer_match()
