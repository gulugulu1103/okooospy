import logging
import random
import re

from bs4 import BeautifulSoup
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver

from classes import *


def get_match_list_info(chrome: ChromeDriver) -> List[Tuple[str, str, str, str, str, str]]:
	logging.info("开始获取场次信息")
	match_list_url = "https://www.okooo.com/danchang/"
	match_list_html = chrome.get_html(match_list_url)
	soup = BeautifulSoup(match_list_html, 'html.parser')
	table_list = soup.find_all('table', { 'class': 'jcmaintable' })
	table_list = [x for x in table_list if x.find('tr', { 'style': "display:none;" }) is None]

	# 自定义过滤函数，用于筛选符合条件的tr标签
	def tr_filter(tag):
		if tag.get('id'):
			return tag.name == "tr" and re.fullmatch(f"tr[0-9]+", tag.get('id')) is not None
		return False

	# 自定义函数，用于处理字符串，将字符串分为两部分
	def f(s):
		r1 = s[:len(s)]
		for i in range(len(s)):
			if not s[i].isdigit():
				r1 = s[:i]
				break
		r2 = s[len(r1):]
		return r1, r2

	match_list: List[Tuple[str, str, str, str, str, str]] = []
	for table in table_list:
		trs = table.find_all(tr_filter)
		for tr in trs:
			id = tr.get('matchid')
			td1_tdsx = tr.find('td', { 'class': 'td1 tdsx' })
			show_id, league = f(td1_tdsx.text) if td1_tdsx else ('', '')
			match_time_element = tr.find('span', { 'class': 'BuyTime' })
			match_time = match_time_element.text if match_time_element else ''
			home_team_element = tr.find('span', { 'class': 'homenameobj homename' })
			away_team_element = tr.find('span', { 'class': 'awaynameobj awayname' })
			home_team = home_team_element.text if home_team_element else ''
			away_team = away_team_element.text if away_team_element else ''
			match: Tuple[str, str, str, str, str, str] = (show_id, league, match_time, home_team, away_team, id)
			logging.info(f"获取到的场次信息：{match}")
			match_list.append(match)

	return match_list


def get_init_match_info(match_id: str, chrome: ChromeDriver, wait_time = random.randint(1, 3)) -> SoccerMatch:
	logging.info(f"开始获取比赛 {match_id} 的初始信息")

	match_odd_url = f"https://www.okooo.com/soccer/match/{match_id}/odds/"
	match_odd_html = chrome.get_html(match_odd_url, wait_time = wait_time)
	soup = BeautifulSoup(match_odd_html, 'html.parser')

	match: SoccerMatch = SoccerMatch()
	match.match_id = match_id

	# qbox 拥有主队 客队 联赛 时间
	qbox = soup.find('div', { 'class': 'qbox' })
	if qbox:
		# 赛事联赛信息框
		_ = qbox.find('div', { 'class': 'qk_two' })
		if _:
			match.league = _.find('a').text
		else:
			_ = qbox.find('div', { 'id': 'lunci' })
			if _:
				match.league = _.find_all({ 'span' })[0].text
			else:
				logging.warning("没有找到联赛信息，将联赛信息设置为空字符串")
				match.league = ""

		match_time = qbox.find('span', { 'class': 'time' })
		if match_time:
			match.match_time = match_time.text.replace('\xa0', ' ')
		else:
			logging.warning("没有找到比赛时间信息，将比赛时间设置为空字符串")
			match.match_time = ""

		home_team = qbox.find('div', { 'class': 'qpai_zi jsTeamName' })
		if home_team:
			match.home_team = home_team.text
		else:
			logging.warning("没有找到主队信息，将主队信息设置为空字符串")
			match.home_team = ""

		away_team = qbox.find('div', { 'class': 'qpai_zi_1 jsTeamName' })
		if away_team:
			match.away_team = away_team.text
		else:
			logging.warning("没有找到客队信息，将客队信息设置为空字符串")
			match.away_team = ""
	else:
		logging.warning("没有找到qbox，将联赛、比赛时间、主队和客队信息设置为空字符串")
		match.league, match.match_time, match.home_team, match.away_team = "", "", "", ""

	# 找到包含tr标签的table,返回一个tbody，其中包含每场比赛的初始赔率、更新赔率、更新凯利指数
	table = soup.find('div', { "id": "data_main_content", "class": "container_wrapper" })
	if table:
		table = table.find('tbody')
	else:
		logging.warning("没有找到data_main_content，将不会添加赔率信息")
		return match

	def filter_function(tag):
		return tag.name == 'span' and tag.get('style') != 'font-size:0;'

	odd_provider_ids = {
		24 : "99家平均", 14: "威廉·希尔", 27: "Bet365", 25: "SNAL", 18: "Oddset", 43: "Interwetten", 2: "竞彩官方",
		131: "香港马会", 84: "澳门彩票", 220: "沙巴", 322: "金宝博"
	}
	for id, company in odd_provider_ids.items():
		logging.info(f"正在获取{company}的赔率信息")
		# 每个tr包含当前提供商的所有信息
		tr = table.find('tr', { 'id': f"tr{id}" })
		if tr is None:
			logging.warning(f"没有找到{company}的赔率信息")
			continue
		# initial_odds = [float(each.text) for each in tr.find_all('span', { 'class': 'nolink' })]
		t = [each.text for each in tr.find_all(filter_function)]
		initial_odds = [float(odd) for odd in t[2:5]]
		current_odds = [float(odd) for odd in t[5:8]]
		current_kelly = [float(odd) for odd in t[11:14]]
		match.add_odds(
				company = company,
				initial_odds = initial_odds,
				current_odds = current_odds,
				current_kelly = current_kelly
		)

	# 添加亚盘信息阶段
	asian_handicap_url = f"https://www.okooo.com/soccer/match/{match_id}/ah/"
	asian_handicap_html = chrome.get_html(asian_handicap_url)
	soup = BeautifulSoup(asian_handicap_html, 'html.parser')
	# soup = BeautifulSoup(testvar.ah_html, 'html.parser')

	table = soup.find('div', { 'id': "data_main_content", 'class': "container_wrapper" }) \
		.find('tbody')
	asian_handicap_providers = { 84: "澳门彩票", 43: "Interwetten", 322: "金宝博" }
	for id, company in asian_handicap_providers.items():
		logging.info(f"正在获取{company}的亚盘信息")
		tr = table.find('tr', { 'id': f"tr{id}" })
		if tr is None:
			logging.warning(f"没有找到{company}的亚盘信息")
			continue
		t = [each.text for each in tr.find_all(filter_function)]
		initial_handicap = (float(t[2]), t[3], float(t[4]))
		current_handicap = (float(t[5]), t[6], float(t[7]))
		match.add_asian_handicap(
				company = company,
				initial_handicap = initial_handicap,
				current_handicap = current_handicap
		)

	# 添加让球信息
	handicap_odds_url = f"https://www.okooo.com/soccer/match/{match_id}/hodds/"
	handicap_odd_html = chrome.get_html(handicap_odds_url)
	soup = BeautifulSoup(handicap_odd_html, 'html.parser')
	# soup = BeautifulSoup(testvar.ho_html, 'html.parser')
	table = soup.find('div', { 'id': "data_main_content", 'class': "container_wrapper" }) \
		.find('tbody')
	handicap_odds_providers = { 2: "竞彩官方", 43: "Interwetten", 322: "金宝博" }

	for id, company in handicap_odds_providers.items():
		logging.info(f"正在获取{company}的让球信息")

		# 要比较多个tr的id : "tr2_0"
		def tr_filter(tag):
			if tag.name == "tr" and re.fullmatch(f"tr{id}_[0-9]+", tag.get('id')) is not None:
				return True

		trs = table.find_all(tr_filter)
		for tr in trs:
			t = ([each.text for each in tr.find_all(filter_function)])
			# 以竞彩官方的handicap值为准，赋值让球值
			if id == 2:
				match.handicap = int(t[2])
			# 过滤出让球值与竞彩官方相同的条目
			elif match.handicap is None:
				match.handicap = int(t[2])
				logging.warning(f"没有找到官方的让球值，使用{company}的让球值")

			if int(t[2]) == int(match.handicap):
				initial_odds = [float(odd) for odd in t[3:6]]
				current_odds = [float(odd) for odd in t[6:9]]
				match.add_handicap_odds(
						company = company,
						initial_odds = initial_odds,
						current_odds = current_odds
				)
	# match.add_handicap_odds("")

	# 添加盈亏信息
	profit_loss_url = f"https://www.okooo.com/soccer/match/{match_id}/exchanges/"
	profit_loss_html = chrome.get_html(profit_loss_url)
	soup = BeautifulSoup(profit_loss_html, 'html.parser')
	# soup = BeautifulSoup(testvar.pl_html, 'html.parser')

	table = soup.find_all('table', { 'class': "noBberBottom" })[1] \
		.find('tbody')

	# 添加必发指数
	trs = table.find_all('tr')[2:]
	t = [tr.text.split('\n') for tr in trs]
	if t[0][11] and t[1][11] and t[2][11]:
		match.add_profit_loss(company = "必发", initial_profit_loss = [int(t[0][11]), int(t[1][11]), int(t[2][11])])
	else:
		logging.info("无法解析必发公司的盈亏信息。")
	# 添加竞彩指数
	if t[0][12] and t[1][12] and t[2][12]:
		match.add_profit_loss(company = "竞彩", initial_profit_loss = [int(t[0][12]), int(t[1][12]), int(t[2][12])])
	else:
		logging.info("无法解析竞彩公司的盈亏信息。")

	# 添加比赛历史信息
	history_url = f"https://www.okooo.com/soccer/match/{match_id}/history/"
	history_html = chrome.get_html(history_url)
	soup = BeautifulSoup(history_html, 'html.parser')
	last_vs_tr = None
	table_dir = { 'homecomp': "主队历史", 'awaycomp': "客队历史", 'vscomp': "交战历史" }
	for trclass, history_type in table_dir.items():
		table = soup.find('table', { 'class': trclass })
		table = table.find('tbody')
		trs = table.find_all('tr')
		trs = trs[3:min(13, len(trs))]
		last_vs_tr = trs[0]
		his_str = ''
		for tr in trs:
			if tr.find('span', { 'class': "bold redtxt" }):
				# home_his_str += '赢'
				his_str += '3'
			elif tr.find('span', { 'class': "bold bluetxt" }):
				# home_his_str += '输'
				his_str += '0'
			elif tr.find('span', { 'class': "bold" }):
				# home_his_str += '平'
				his_str += '1'
			else:
				his_str += '-'
		match.add_match_history(history_type = history_type,
		                        history = his_str)
	# 添加最后交战信息
	t = last_vs_tr.text.split()[3:]
	last_vs_str = ''.join(t[:3]) + '\n' + ''.join(t[-4:-1])
	match.add_match_history(history_type = "最后交战历史",
	                        history = last_vs_str)

	return match


def update_match_info(match: SoccerMatch, chrome: ChromeDriver) -> SoccerMatch:
	logging.info(f"开始更新比赛 {match.match_id} 的信息")
	match_id = match.match_id
	match_odd_url = f"https://www.okooo.com/soccer/match/{match_id}/odds/"
	match_odd_html = chrome.get_html(match_odd_url)
	soup = BeautifulSoup(match_odd_html, 'html.parser')

	# 找到包含tr标签的table,返回一个tbody，其中包含每场比赛的初始赔率、更新赔率、更新凯利指数
	main_content = soup.find('div', { "id": "data_main_content", "class": "container_wrapper" })

	if main_content:
		table = main_content.find('tbody')
	else:
		table = None
		logging.info(f"未找到data_main_content元素，可能页面结构已经发生变化。")

	def filter_function(tag):
		return tag.name == 'span' and tag.get('style') != 'font-size:0;'

	odd_provider_ids = {
		24 : "99家平均", 14: "威廉·希尔", 27: "Bet365", 25: "SNAL", 18: "Oddset", 43: "Interwetten", 2: "竞彩官方",
		131: "香港马会", 84: "澳门彩票", 220: "沙巴", 322: "金宝博"
	}

	if table:
		for id, company in odd_provider_ids.items():
			# 每个tr包含当前提供商的所有信息
			tr = table.find('tr', { 'id': f"tr{id}" })
			if tr:
				t = [each.text for each in tr.find_all(filter_function)]
				current_odds = [float(odd) for odd in t[5:8]]
				current_kelly = [float(odd) for odd in t[11:14]]
				match.update_odds(
						company = company,
						updated_odds = current_odds,
						updated_kelly = current_kelly
				)
			else:
				logging.info(f"在表格中未找到id为 {id} 的元素。")
	else:
		logging.info(f"未找到tbody元素，可能页面结构已经发生变化。")

	# 添加亚盘信息阶段
	asian_handicap_url = f"https://www.okooo.com/soccer/match/{match_id}/ah/"
	asian_handicap_html = chrome.get_html(asian_handicap_url)
	soup = BeautifulSoup(asian_handicap_html, 'html.parser')

	main_content = soup.find('div', { 'id': "data_main_content", 'class': "container_wrapper" })

	if main_content:
		table = main_content.find('tbody')
	else:
		table = None
		logging.info(f"未找到data_main_content元素，可能页面结构已经发生变化。")

	asian_handicap_providers = { 84: "澳门彩票", 43: "Interwetten", 322: "金宝博" }

	if table:
		for id, company in asian_handicap_providers.items():
			tr = table.find('tr', { 'id': f"tr{id}" })
			if tr:
				t = [each.text for each in tr.find_all(filter_function)]
				current_handicap = (float(t[5]), t[6], float(t[7]))
				match.update_asian_handicap(
						company = company,
						updated_handicap = current_handicap
				)
			else:
				logging.info(f"在表格中未找到id为 {id} 的元素。")
		else:
			logging.info(f"未找到tbody元素，可能页面结构已经发生变化。")

	# 添加让球信息
	handicap_odds_url = f"https://www.okooo.com/soccer/match/{match_id}/hodds/"
	handicap_odd_html = chrome.get_html(handicap_odds_url)
	soup = BeautifulSoup(handicap_odd_html, 'html.parser')

	main_content = soup.find('div', { 'id': "data_main_content", 'class': "container_wrapper" })

	if main_content:
		table = main_content.find('tbody')
	else:
		table = None
		logging.info(f"未找到data_main_content元素，可能页面结构已经发生变化。")

	handicap_odds_providers = { 2: "竞彩官方", 43: "Interwetten", 322: "金宝博" }

	if table:
		for id, company in handicap_odds_providers.items():
			# 要比较多个tr的id : "tr2_0"
			def tr_filter(tag):
				if tag.name == "tr" and re.fullmatch(f"tr{id}_[0-9]+", tag.get('id')) is not None:
					return True

			trs = table.find_all(tr_filter)
			for tr in trs:
				t = ([each.text for each in tr.find_all(filter_function)])
				# 以竞彩官方的handicap值为准，赋值让球值
				if id == 2:
					match.handicap = int(t[2])
				# 过滤出让球值与竞彩官方相同的条目
				if int(t[2]) == int(match.handicap):
					current_odds = [float(odd) for odd in t[6:9]]
					match.update_handicap_odds(
							company = company,
							updated_odds = current_odds
					)
	else:
		logging.info(f"未找到tbody元素，可能页面结构已经发生变化。")

	# 添加盈亏信息
	profit_loss_url = f"https://www.okooo.com/soccer/match/{match_id}/exchanges/"
	profit_loss_html = chrome.get_html(profit_loss_url)
	soup = BeautifulSoup(profit_loss_html, 'html.parser')

	table = soup.find_all('table', { 'class': "noBberBottom" })

	if table and len(table) > 1:
		table = table[1].find('tbody')
	else:
		table = None
		logging.info(f"未找到noBberBottom元素，可能页面结构已经发生变化。")

	if table:
		# 添加必发指数
		t = [x.text for x in table.find_all(filter_function)]
		match.update_profit_loss(company = "必发", updated_profit_loss = [int(t[3]), int(t[7]), int(t[12])])
		match.update_profit_loss(company = "竞彩", updated_profit_loss = [int(t[4]), int(t[8]), int(t[13])])
	else:
		logging.info(f"未找到tbody元素，可能页面结构已经发生变化。")

	# 添加比赛历史信息
	match.match_history = { }
	history_url = f"https://www.okooo.com/soccer/match/{match_id}/history/"
	history_html = chrome.get_html(history_url)
	soup = BeautifulSoup(history_html, 'html.parser')
	last_vs_tr = None
	table_dir = { 'homecomp': "主队历史", 'awaycomp': "客队历史", 'vscomp': "交战历史" }
	for trclass, history_type in table_dir.items():
		table = soup.find('table', { 'class': trclass })

		if table:
			table = table.find('tbody')
		else:
			table = None
			logging.info(f"未找到{trclass}元素，可能页面结构已经发生变化。")

		if table:
			trs = table.find_all('tr')
			trs = trs[3:min(13, len(trs))]
			last_vs_tr = trs[0]
			his_str = ''
			for tr in trs:
				if tr.find('span', { 'class': "bold redtxt" }):
					# home_his_str += '赢'
					his_str += '3'
				elif tr.find('span', { 'class': "bold bluetxt" }):
					# home_his_str += '输'
					his_str += '0'
				elif tr.find('span', { 'class': "bold" }):
					# home_his_str += '平'
					his_str += '1'
				else:
					his_str += '-'
			match.add_match_history(history_type = history_type,
			                        history = his_str)
		else:
			logging.info(f"未找到tbody元素，可能页面结构已经发生变化。")

	# 添加最后交战信息
	if last_vs_tr:
		t = last_vs_tr.text.split()[3:]
		last_vs_str = ''.join(t[:3]) + '\n' + ''.join(t[-4:-1])
		match.add_match_history(history_type = "最后交战历史",
		                        history = last_vs_str)
	else:
		logging.info(f"未找到最后交战信息。")

	return match


if __name__ == "__main__":
	match = get_init_match_info(1171208, chrome = ChromeDriver())
	print(match.__dict__)
