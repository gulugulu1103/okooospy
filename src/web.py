import json
import logging
from time import sleep, time
from requests import request, post
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logging.basicConfig(level = logging.DEBUG, format = '%(asctime)s %(levelname)s %(message)s')


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


cookies = read_cookies()


class ChromeDriver:
	"""
	ChromeDriver 类用于与 Chrome 浏览器进行交互，以获取和更新网页的 HTML 源代码。
	"""
	driver = None
	url = "https://www.okooo.cn/danchang/"
	wait_complete_time = 6

	def __init__(self):
		"""
		初始化 ChromeDriver 类，创建服务对象和浏览器对象。
		"""
		# 创建服务对象
		service = Service('../browser/chromedriver_win32/chromedriver.exe')
		service.start()

		# 创建浏览器对象
		options = webdriver.ChromeOptions()
		# options.add_argument('--headless')
		options.binary_location = "../browser/chrome-win/chrome.exe"
		self.driver = webdriver.Chrome(service = service, options = options)

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

	def get_html(self, url: str = url) -> str:
		"""
		访问给定的 URL，并返回其 HTML 源代码。
		Args:
		    url (str): 要访问的 URL。
		Returns:
		    str: 网页的 HTML 源代码。
		"""

		sleep(1)
		# 访问URL
		self.driver.get(url)

		wait_time = 1
		while self.driver.title == "405":
			# 当收到无效的405消息时，刷新页面
			logging.debug("[ChromeDriver] : Got the invalid message 405, refreshing...")
			self.driver.refresh()
			sleep(wait_time)
			wait_time *= 2  # 每次循环将等待时间增加一倍

		# sleep(self.wait_complete_time)  # 等待网页完全加载通常需要最多8秒
		self.save_cookies()
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

	def get_match_odds(self, provider_ids: list = [27],
	                   match_ids: list = [1206413, 1206406, 1207296, 1206393, 1206387, 1207286, 1206380, 1207280,
	                                      1206369, 1206354, 1207267], end: bool = True) -> json:
		"""
		获取比赛赔率信息。
		Args:
		    provider_ids (list): 提供者 ID 列表。
		    match_ids (list): 比赛 ID 列表。
		    end (bool): 是否为结束赔率。
		Returns:
		    json: 包含比赛赔率信息的 JSON 对象。
		"""
		url = "https://www.okooo.cn/ajax/?method=data.match.endodds" \
			if end else "https://www.okooo.cn/ajax/?method=data.match.odds"
		url += f"&bettingTypeId=1"  # 1 赔率 | 2 亚盘
		url += "&matchIds="
		for id in match_ids:
			url += f"{id},"
		url.rstrip(',')
		for id in provider_ids:
			temp_url = url + f"&providerId={id}"
			print(temp_url)
			print(self.get_html(temp_url))

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


def re_get_match_odds(provider_ids=None, match_ids: list = None, end: bool = True) -> dict | None:
	"""
	使用 requests 调整胜率。
	Args:
	    provider_ids (list, optional): 提供者 ID 列表。
	    match_ids (list, optional): 比赛 ID 列表。
	    end (bool): 是否为结束赔率。
	Returns:
	    dict: 包含比赛赔率信息的字典，如果获取失败则返回 None。
	"""

	if provider_ids is None:
		provider_ids = [14, 27, 24]

	# 添加默认值以供测试
	if match_ids is None:
		match_ids = [1206413, 1206406, 1207296, 1206393]

	# 准备访问
	url = "https://www.okooo.cn/ajax/?method=data.match.endodds" \
		if end else "https://www.okooo.cn/ajax/?method=data.match.odds"

	cookies = read_cookies()
	cookie_str = ""
	for cookie in cookies:
		cookie_str += f"{cookie['name']}={cookie['value']}; "

	# 去掉最后一个分号和空格
	cookie_str = cookie_str[:-2]

	payload = {
		'bettingTypeId': 1,
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
		while response.status_code == 405:
			sleep(1)
			response = post(url, headers = headers, data = payload)
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
	# print(chrome.get_match_odds())

	print(re_get_match_odds(end = False))
