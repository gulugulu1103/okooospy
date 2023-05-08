from bs4 import BeautifulSoup
import re
import sql
from web import ChromeDriver
import logging
from classes import SoccerMatch
# import testvar


# logging.basicConfig(level = logging.DEBUG, format = '%(asctime)s %(levelname)s %(message)s')


# chrome: ChromeDriver = ChromeDriver()

def get_init_match_info(match_id: str, chrome: ChromeDriver = ChromeDriver()) -> SoccerMatch:
	# def get_init_match_info(match_id: str) -> SoccerMatch:
	match_odd_url = f"https://www.okooo.com/soccer/match/{match_id}/odds/"
	match_odd_html = chrome.get_html(match_odd_url)
	soup = BeautifulSoup(match_odd_html, 'html.parser')
	# soup = BeautifulSoup(testvar.odd_html, 'html.parser')
	match: SoccerMatch = SoccerMatch()
	match.match_id = match_id
	# qbox 拥有主队 客队 联赛 时间
	qbox = soup.find('div', { 'class': 'qbox' })
	match.league = qbox.find('div', { 'class': 'qk_two' }).find('a').text
	match.match_time = qbox.find('span', { 'class': 'time' }).text.replace('\xa0', ' ')
	match.home_team, match.away_team = qbox.find('div', { 'class': 'qpai_zi jsTeamName' }).text, qbox.find('div', {
		'class': 'qpai_zi_1 jsTeamName' }).text

	# 找到包含tr标签的table,返回一个tbody，其中包含每场比赛的初始赔率、更新赔率、更新凯利指数
	table = soup.find('div', { "id": "data_main_content", "class": "container_wrapper" }) \
		.find('tbody')

	def filter_function(tag):
		return tag.name == 'span' and tag.get('style') != 'font-size:0;'

	odd_provider_ids = {
		24 : "99家平均", 14: "威廉·希尔", 27: "Bet365", 25: "SNAL", 18: "Oddset", 43: "Interwetten", 2: "竞彩官方",
		131: "香港马会", 84: "澳门彩票", 220: "沙巴", 322: "金宝博"
	}
	for id, company in odd_provider_ids.items():
		# 每个tr包含当前提供商的所有信息
		tr = table.find('tr', { 'id': f"tr{id}" })
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
		tr = table.find('tr', { 'id': f"tr{id}" })
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
	t = [x.text for x in table.find_all(filter_function)]
	match.add_profit_loss(company = "必发", initial_profit_loss = [int(t[3]), int(t[7]), int(t[12])])
	match.add_profit_loss(company = "竞彩", initial_profit_loss = [int(t[4]), int(t[8]), int(t[13])])

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


def test():
	matches_url = "https://www.okooo.cn/danchang/"
	chrome: ChromeDriver = ChromeDriver()
	html = chrome.get_html(matches_url)
	soup = BeautifulSoup(html, 'html.parser')
	matches = filter_matches(soup)

	sql.save_matches(matches)
	# 打印比赛信息
	for match in matches:
		logging.info(f"联赛名称：{match['league_name']}")
		logging.info(f"比赛时间：{match['match_date'] + ' ' + match['match_time']}")
		logging.info(f"主队：{match['home_team']}")
		logging.info(f"客队：{match['away_team']}")
		logging.info(f"比分：{match['home_score'] + '-' + match['away_score']}")
		logging.info(f"比赛 ID：{match['match_id']}")

	chrome.close()


if __name__ == "__main__":
	print(get_init_match_info(1171743).__dict__)
