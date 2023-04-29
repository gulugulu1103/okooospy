import logging
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')


class ChromeDriver:
    driver = None
    url = "https://www.okooo.cn/danchang/"
    wait_complete_time = 6

    def __init__(self):
        # 创建服务对象
        service = Service('../browser/chromedriver_win32/chromedriver.exe')
        service.start()

        # 创建浏览器对象
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.binary_location = "browser/chrome-win/chrome.exe"
        self.driver = webdriver.Chrome(service=service, options=options)

    def get_html(self, url: str = url) -> str:
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
        html = self.driver.page_source
        logging.debug("[ChromeDriver] : Got the whole HTML: %s", html)
        return html

    def update_html(self) -> str:
        sleep(1)
        """
        Checks if the current tab is the same as the URL provided during initialization.
        If it is, the page is refreshed. Otherwise, the URL is opened in a new tab.
        Finally, return the HTML source of the tab.
        :return: The HTML source of the tab.
        """
        current_url = self.driver.current_url
        if current_url != self.url:
            self.driver.get(self.url)
        else:
            self.driver.refresh()

        # 获取网页的HTML源代码
        html = self.driver.page_source

        logging.debug("[ChromeDriver] : Got the whole HTML: %s", html)
        return html

    def close(self) -> None:
        self.driver.quit()


if __name__ == "__main__":
    chrome: ChromeDriver = ChromeDriver()
    sleep(1)
    chrome.get_html()
    sleep(100)