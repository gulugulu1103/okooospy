import json
import logging
import random
import re
from time import sleep

from fake_useragent import UserAgent
from requests import request, post
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


# logging.basicConfig(level = logging.DEBUG, format = '%(asctime)s %(levelname)s %(message)s')


def read_cookies() -> list | None:
	"""
    从文件中读取保存的 Cookie
    Returns:
        dict: 读取成功则返回 Cookie 字典，否则返回 None
    """
	try:
		with open('cookie.json', 'r') as f:
			cookie = json.load(f)
			return cookie
	except (FileNotFoundError, json.JSONDecodeError, KeyError):
		return None


class ChromeDriver:
	"""
	ChromeDriver 类用于与 Chrome 浏览器进行交互，以获取和更新网页的 HTML 源代码。
	"""
	driver = None
	url = "https://www.okooo.cn/danchang/"
	wait_complete_time = 6
	chrome_options = webdriver.ChromeOptions()

	def __init__(self, fake_ua=False):
		"""
		初始化 ChromeDriver 类，创建服务对象和浏览器对象。
		"""
		# 创建服务对象
		service = Service('../browser/chromedriver_win32/chromedriver.exe')
		service.start()

		# 创建浏览器对象
		self.chrome_options = webdriver.ChromeOptions()
		# options.add_argument('--headless')
		self.chrome_options.binary_location = "../browser/chrome-win/chrome.exe"

		# 无图模式
		prefs = { 'profile.managed_default_content_settings.images': 2 }
		self.chrome_options.add_experimental_option('prefs', prefs)

		if fake_ua:
			# 随机UA
			ua = UserAgent()
			self.chrome_options.add_argument(f'user-agent={ua.random}')
		self.driver = webdriver.Chrome(options = self.chrome_options)

	# if cookies is not None:
	# 	self.driver.add_cookie(cookies)

	def save_cookies(self):
		"""
		将当前浏览器的 Cookie 保存到文件中。
		"""
		# 检测是否处于无driver状态
		if self.driver is None:
			raise IOError("ChromeDriver.driver is None")

		cookie = self.driver.get_cookies()
		with open('cookie.json', 'w') as f:
			json.dump(cookie, f)

	def get_html(self, url: str = url, wait_factor: int = random.randint(0, 5)) -> str:
		"""
		访问给定的 URL，并返回其 HTML 源代码。
		Args:
		    url (str): 要访问的 URL。
		Returns:
		    str: 网页的 HTML 源代码。
		"""
		# 访问URL
		self.driver.get(url)
		logging.info("[ChromeDriver] : Visiting the URL: %s", url)
		sleep(wait_factor)
		logging.info("[ChromeDriver] : Waiting for the page to load...")
		wait_time = 1
		while self.driver.title == "405":
			# 当收到无效的405消息时，刷新页面
			logging.debug("[ChromeDriver] : Got the invalid message 405, refreshing...")
			sleep(wait_time)
			self.driver.refresh()
			wait_time *= 2  # 每次循环将等待时间增加一倍

		# sleep(self.wait_complete_time)  # 等待网页完全加载通常需要最多8秒
		self.save_cookies()
		for i in range(10):
			self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
			sleep(0.5)
		html = self.driver.page_source
		# logging.debug("[ChromeDriver] : Got the whole HTML: %s", html)
		return html

	def update_html(self) -> str:
		"""
		刷新当前页面或导航到默认 URL，并返回其 HTML 源代码。
		Returns:
		    str: 网页的 HTML 源代码。
		"""
		sleep(1)
		current_url = self.driver.current_url
		if current_url != self.url:
			self.driver.get(self.url)
		else:
			self.driver.refresh()

		self.save_cookies()
		# 获取网页的HTML源代码
		html = self.driver.page_source

		# logging.debug("[ChromeDriver] : Got the whole HTML: %s", html)
		return html

	def close(self) -> None:
		"""
		关闭浏览器实例。
		"""
		self.driver.quit()

	def __del__(self):
		"""
		当对象被销毁时关闭浏览器实例。
		"""
		self.close()


def re_get_match_odds(match_ids: list, provider_ids=None, end: bool = True) -> list | None:
	# 如果没有提供 provider_ids，则使用默认值
	if provider_ids is None:
		provider_ids = [24, 14, 27, 25, 18, 43, 2, 131, 84, 220, 322]

	# 根据 end 参数选择 URL
	url = "https://www.okooo.cn/ajax/?method=data.match.endodds" \
		if end else "https://www.okooo.cn/ajax/?method=data.match.odds"

	# 读取 cookies
	cookies = read_cookies()
	# 使用列表推导式生成 cookie_str
	cookie_str = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])

	# 准备请求参数
	payload = {
		'bettingTypeId'                   : 1,
		'providerId'                      : provider_ids,
		('matchId' if end else 'matchIds'): ",".join(map(str, match_ids))  # 以逗号分隔的 match_ids 字符串
	}
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
		              'Chrome/58.0.3029.110 Safari/537.36',
		'Cookie'    : cookie_str,
	}

	responses = []

	# 遍历所有 provider_ids
	for provider_id in provider_ids:
		payload['providerId'] = provider_id
		response = post(url, headers = headers, data = payload)

		# 如果返回状态码为 405，则等待后重试
		i = 1
		while response.status_code == 405:
			sleep(1 * i)
			response = post(url, headers = headers, data = payload)
			i += 1
			if i == 10:
				raise Exception('Unexpected response')

		# 如果请求成功
		if response.status_code == 200:
			json = { 'providerId': provider_id }
			# 根据 end 参数获取赔率数据
			odds_data = response.json()["match_endodds_response"] if end else response.json()
			json.update(odds_data)  # 更新 json 对象
			responses.append(json)
			sleep(0.2)
		else:
			logging.error(f"response status code: {response.status_code}\ntext: {response.text}")
			continue

	return responses


def re_get_lottery_num() -> str:
	"""
	爬虫爬取最新的lottery_num
	Returns: 当期的lottery_num
	"""
	url = "https://www.okooo.com/I/?method=ok.news.info.getnotice&type=danchang"

	# 读取 cookies
	cookies = read_cookies()

	# 使用列表推导式生成 cookie_str
	cookie_str = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])

	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
		              'Chrome/58.0.3029.110 Safari/537.36',
		'Cookie'    : cookie_str,
	}

	response = request("GET", url)
	# 如果返回状态码为 405，则等待后重试
	i = 1
	while response.status_code != 200:
		sleep(1 * i)
		response = request("GET", url, headers = headers)
		i += 1
		if i == 10:
			raise Exception('Unexpected response')

	if response.status_code == 200:
		# Get the title from the response
		title = response.json()["info"][0]["title"]

		# Use a regular expression to extract the number
		match = re.search(r'第(\d+)期', title)

		if match:
			number = str(match.group(1))
			return number
		else:
			raise Exception('No number found in the title.')


def re_get_kelly_criterion(match_ids: list, LotteryNo: str, provider_indexes: list = None):
	"""
	拿到凯莉指数
	Returns:
	"""
	if provider_indexes is None:
		# 'get_kaili**' = 'id' + '0'
		provider_indexes = ['0', '2', '3', '4', '5', '6']  # 0:99家平均, 2:威廉希尔, 3:立博, 4:bet365, 5:澳门彩票, 6:bwin

	# index -> provider_ids
	provider_map = { '0': 24, '2': 14, '4': 27, '5': 84 }

	# 读取 cookies
	cookies = read_cookies()

	# 使用列表推导式生成 cookie_str
	cookie_str = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])

	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
		              'Chrome/58.0.3029.110 Safari/537.36',
		'Cookie'    : cookie_str,
	}

	responses = []
	for index in provider_indexes:
		url = f"https://www.okooo.com/ajax/?method=odds.sporttery.endodds&format=json&jsoncallback=get_kaili{index}0&LotteryNo={LotteryNo}&act=get_kaili&index={index}&LotteryType=WDL&v="

		response = request("GET", url, headers = headers)
		# 如果返回状态码为 405，则等待后重试
		i = 1
		while response.status_code == 405:
			sleep(1 * i)
			response = request("GET", url, headers = headers)
			i += 1
			if i == 10:
				raise Exception('Unexpected response')

		# 如果请求成功
		if response.status_code == 200:
			# json = { 'providerId': provider_id }
			json = { }
			# 根据 end 参数获取赔率数据
			kelly_criterion = response.json()['sporttery_endodds_response']
			json.update(kelly_criterion)  # 更新 json 对象
			responses.append(json)
			sleep(0.2)
		else:
			logging.error(f"response status code: {response.status_code}\ntext: {response.text}")

	print(responses)


def re_get_asian_handicaps(match_ids: list, provider_ids=None, end: bool = True) -> dict | None:
	"""
	使用 requests 查看亚盘赔率
	Args:
	    provider_ids (list, optional): 提供者 ID 列表。
	    match_ids (list, optional): 比赛 ID 列表。
	    end (bool): 是否为结束赔率。
	Returns:
	    dict: 包含比赛赔率信息的字典，如果获取失败则返回 None。
	"""

	if provider_ids is None:
		provider_ids = [34]

	# 准备访问
	url = "https://www.okooo.cn/ajax/?method=data.match.endodds" \
		if end else "https://www.okooo.cn/ajax/?method=data.match.odds"

	# TODO: 万一没有cookies该怎么办？
	cookies = read_cookies()
	cookie_str = ""
	for cookie in cookies:
		cookie_str += f"{cookie['name']}={cookie['value']}; "

	# 去掉最后一个分号和空格
	cookie_str = cookie_str[:-2]

	payload = {
		'bettingTypeId': 2,
		'providerId'   : provider_ids,
		'matchIds'     : str(match_ids).strip('[').strip(']')
	}
	headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
	                          'Chrome/58.0.3029.110 Safari/537.36',
	            'Cookie'    : cookie_str,
	            }

	responses = []

	for provider_id in provider_ids:
		json = { }
		payload['providerId'] = provider_id
		response = post(url, headers = headers, data = payload)
		i = 1
		while response.status_code == 405:
			sleep(i)
			response = post(url, headers = headers, data = payload)
			i += 1
			if i == 10:
				raise Exception('Unexpected response')
		if response.status_code == 200:
			json['providerId'] = provider_id
			json.update(response.json())
			responses.append(json)
			sleep(0.2)
		else:
			logging.error("response status code: %d\ntext:", response.status, response.text)
			continue

	return responses


if __name__ == "__main__":
	# chrome = ChromeDriver()
	# print(chrome.get_html())
	# print(chrome.get_match_odds())
	print(re_get_lottery_num())

	re_get_kelly_criterion([], re_get_lottery_num())
