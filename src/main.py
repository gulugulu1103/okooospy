import logging
import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk

import data
import excel
import filter
import web
from classes import *

logging.basicConfig(level = logging.INFO,
                    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class App:
	def __init__(self, root):
		# 统一的chrome引擎
		self.chrome = web.ChromeDriver(fake_ua = True)

		# 场次信息
		self.show_matches: List[Tuple[str, str, str, str, str, str]] = []
		# 首先先从硬盘读取场次信息
		self.show_matches = data.read_show_matches()
		if not self.show_matches:
			logging.info('self.show_matches 是空的，从网页获取场次信息')
			self.show_matches = filter.get_match_list_info(self.chrome)
			data.save_show_matches(self.show_matches)

		# 选取的场次ID列表
		self.selected: List[str] = []
		# 从硬盘读取选取的场次ID列表
		self.selected = data.read_selected_list()

		# 比赛信息列表
		self.match_list: List[SoccerMatch] = []
		# 缓存的比赛信息列表
		self.cached_match_list: List[str] = []
		for file in os.listdir("../data/"):
			if os.path.isfile(os.path.join("../data/", file)):
				file_name = os.path.splitext(file)[0]  # 去掉后缀名
				self.cached_match_list.append(file_name)

		self.root = root
		self.root.title('场次列表')
		self.tree = ttk.Treeview(self.root, columns = ('showid', 'league', 'time', 'home', 'away', 'id'),
		                         show = 'headings', selectmode = 'none')
		self.tree.heading('showid', text = '场次', command = lambda: self.sort_column('showid', False))
		self.tree.heading('league', text = '赛事', command = lambda: self.sort_column('name', False))
		self.tree.heading('time', text = '时间', command = lambda: self.sort_column('time', False))
		self.tree.heading('home', text = '主', command = lambda: self.sort_column('home', False))
		self.tree.heading('away', text = '客', command = lambda: self.sort_column('away', False))
		self.tree.heading('id', text = 'ID', command = lambda: self.sort_column('id', False))
		self.tree.column('showid', width = 40, anchor = 'center')
		self.tree.column('league', width = 80, anchor = 'center')
		self.tree.column('time', width = 200, anchor = 'center')
		self.tree.column('home', width = 100, anchor = 'center')
		self.tree.column('away', width = 100, anchor = 'center')
		self.tree.column('id', width = 100, anchor = 'center')
		self.tree.grid(row = 0, column = 0, columnspan = 3, sticky = 'nsew')

		for match in self.show_matches:
			self.tree.insert('', 'end', values = match, tags = ('unselected',))
			if match[5] in self.selected:
				self.tree.item(self.tree.get_children('')[-1], tags = ('selected',))

		self.tree.tag_configure('unselected', background = 'white')
		self.tree.tag_configure('selected', background = 'yellow')
		self.tree.bind('<Double-1>', self.toggle_selection)

		# buttons
		self.refresh_button = tk.Button(self.root, text = '刷新列表', command = self.refresh_show_matches)
		self.refresh_button.grid(row = 1, column = 0, sticky = 'ew')
		self.submit_button = tk.Button(self.root, text = '生成', command = self.generate_excel)
		self.submit_button.grid(row = 1, column = 1, sticky = 'ew')
		self.update_button = tk.Button(self.root, text = '更新', command = self.update_excel)
		self.update_button.grid(row = 1, column = 2, sticky = 'ew')

		# # Adding a label and entry (input box) for setting wait time
		# self.wait_time_label = tk.Label(self.root, text = '等待时间: ')
		# self.wait_time_label.grid(row = 2, column = 0, sticky = 'ew')
		# self.wait_time_entry = tk.Entry(self.root)
		# self.wait_time_entry.grid(row = 2, column = 1, columnspan = 2, sticky = 'ew')

	def sort_column(self, col, reverse):
		match_data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
		match_data.sort(reverse = reverse)

		for index, (_, child) in enumerate(match_data):
			self.tree.move(child, '', index)

		self.tree.heading(col, command = lambda: self.sort_column(col, not reverse))

	def toggle_selection(self, event):
		item = self.tree.identify_row(event.y)
		if item:
			tags = self.tree.item(item, 'tags')
			if 'unselected' in tags:
				self.tree.item(item, tags = ('selected',))
				self.selected.append(self.tree.set(item, 'id'))
			else:
				self.tree.item(item, tags = ('unselected',))
				self.selected.remove(self.tree.set(item, 'id'))
			data.save_selected_list(self.selected)

	def refresh_show_matches(self):
		"""
		刷新场次列表
		"""
		self.show_matches = filter.get_match_list_info(self.chrome)
		data.save_show_matches(self.show_matches)
		self.tree.delete(*self.tree.get_children(''))
		for match in self.show_matches:
			self.tree.insert('', 'end', values = match, tags = ('unselected',))
			if match[5] in self.selected:
				self.tree.item(self.tree.get_children('')[-1], tags = ('selected',))

		# 检测是否self.selected中含有未在self.show_matches中的场次
		for match_id in self.selected:
			# 如果包含，则删除
			if match_id not in [match[5] for match in self.show_matches]:
				self.selected.remove(match_id)
		data.save_selected_list(self.selected)

	def get_info_from_seleted(self) -> None:
		"""
		从self.selected_matches中获取场次列表，通过爬虫爬取比赛信息，保存到self.match_list中
		"""
		for match_id, index in zip(self.selected, range(0, len(self.selected))):
			# 如果已经缓存了该场次的信息，则直接从硬盘读取
			if match_id in self.cached_match_list:
				match = data.read_match(match_id)
			else:
				# 否则，通过爬虫爬取比赛信息
				match = filter.get_init_match_info(match_id, self.chrome)
			# 保存到硬盘
			data.save_match(match)
			# 保存到self.match_list
			self.match_list.append(match)

	def new_fake_chrome(self) -> web.ChromeDriver:
		if self.chrome:
			self.chrome.close()
			del self.chrome
		self.chrome = web.ChromeDriver(fake_ua = True)
		return self.chrome

	def generate_excel(self):
		if not self.match_list:  # 如果没有执行过get_info_from_selected()，则执行
			self.get_info_from_seleted()
		# 生成excel
		now = datetime.now()
		time_str = now.strftime("%Y_%m_%d_%H_%M_%S")
		excel.generate_merged_xlsm(self.match_list, output_filename = f"../output/{time_str}.xlsm", open_file = True)

	def update_info_from_selected(self):
		if not self.selected:
			logging.error("没有选中任何场次！")
			return

		for match_id in self.selected:
			# 如果已经缓存了该场次的信息，则直接从硬盘读取，然后更新
			if os.path.exists('../data/' + match_id + '.data'):
				logging.info("发现缓存，正在读取场次：" + match_id)
				match = data.read_match(match_id)
				# 更新
				logging.info("正在更新场次：" + match_id)
				filter.update_match_info(match, self.chrome)
				# 保存更新后的文件
				logging.info("正在保存更新后的场次：" + match_id)
				data.save_match(match)
				# 如果self.match_list中已经有该场次的信息，则替换
				for index, match_ in enumerate(self.match_list):
					logging.info("正在替换场次：" + match_id)
					if match_['id'] == match['id']:
						self.match_list[index] = match
						break
				# 否则，添加
				if match not in self.match_list:
					logging.info("正在添加场次：" + match_id)
					self.match_list.append(match)


			# 否则，通过爬虫爬取比赛信息
			else:
				logging.info("未发现缓存，正在爬取场次：" + match_id)
				match = filter.get_init_match_info(match_id, self.chrome)
				data.save_match(match)
				self.match_list.append(match)

	def update_excel(self):
		self.update_info_from_selected()
		self.generate_excel()

	def __del__(self):
		# 关闭chrome引擎
		self.chrome.close()


if __name__ == '__main__':
	root = tk.Tk()
	app = App(root)
	root.mainloop()
