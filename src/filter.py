from bs4 import BeautifulSoup
import re
import myhtml
from web import ChromeDriver
import logging

logging.basicConfig(level = logging.DEBUG, format = '%(asctime)s %(levelname)s %(message)s')
chrome: ChromeDriver = ChromeDriver()



def get_matches(soup):
	"""
    从指定URL和解析器对象中获取比赛信息
    :param url: 指定的URL
    :param soup: 解析器对象
    :return: 比赛信息列表
    """
	matches_url = "https://www.okooo.cn/danchang/"
	html = chrome.get_html(matches_url)
	soup = BeautifulSoup(html, 'html.parser')

	# 自定义过滤器，检查id属性是否以'table'开头
	def table_id_filter(tag):
		return tag.name == 'table' and tag.get('id', '').startswith('table')

	# 自定义过滤器，查找具有指定class属性的<tr>元素
	def alltr_filter(tag):
		return tag.name == 'tr' and 'class' in tag.attrs and 'alltrObj' in tag['class']

	# 首先查找指定的<div>
	div = soup.find('div', { 'class': 'jcmian', 'id': 'gametablesend' })

	# 在<div>内查找满足条件的<table>元素
	tables = div.find_all(table_id_filter)

	# 定义空列表，用于存储比赛信息
	matches = []

	# 遍历每个表格
	for table in tables:
		# 查找具有指定class属性的<tr>元素
		trs = table.tbody.find_all(alltr_filter)

		# 遍历每个<tr>元素
		for tr in trs:
			# 获取比赛信息
			league_name = tr.find('a', { 'class': 'ls' }).text
			match_time = tr.find('td', { 'class': 'switchtime' }).attrs['title']
			match_time_filtered = re.sub(r'比赛时间：', '', match_time)
			home_team = tr.find('span', { 'class': 'homenameobj' }).text
			away_team = tr.find('span', { 'class': 'awaynameobj' }).text
			match_id = tr.attrs['matchid']

			# 将比赛信息添加到列表中
			matches.append({
				'league_name': league_name,
				'match_time' : match_time_filtered,
				'home_team'  : home_team,
				'away_team'  : away_team,
				'match_id'   : match_id
			})

	return matches

def get_match_info(match_id: str):
	match_url = f"https://www.okooo.cn/soccer/match/{match_id}/history/"
	html = chrome.get_html(matches_url)
	soup = BeautifulSoup(html, 'html.parser')

	navibox = soup.find_all('div', { 'class': 'matchnavboxbg' })



if __name__ == "__main__":
	matches_url = "https://www.okooo.cn/danchang/"
	chrome: ChromeDriver = ChromeDriver()
	html = chrome.get_html(url)
	soup = BeautifulSoup(html, 'html.parser')
	matches = get_matches(soup)

	# 打印比赛信息
	for match in matches:
		logging.info(f"联赛名称：{match['league_name']}")
		logging.info(f"比赛时间：{match['match_time']}")
		logging.info(f"主队：{match['home_team']}")
		logging.info(f"客队：{match['away_team']}")
		logging.info(f"比赛 ID：{match['match_id']}")
