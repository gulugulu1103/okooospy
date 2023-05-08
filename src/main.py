import web, filter, sql
from bs4 import BeautifulSoup

def fetch_matches():
	# 生成matches列表
	matches_url = "https://www.okooo.cn/danchang/"
	chrome = web.ChromeDriver()
	html = chrome.get_html(matches_url)
	soup = BeautifulSoup(html, 'html.parser')
	matches = filter.filter_matches(soup)

	#
	sql.clear_matches()
	sql.save_matches(matches)
