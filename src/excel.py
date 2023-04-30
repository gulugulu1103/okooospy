import os
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side


def set_header_style(cell):
	cell.font = Font(bold = True, size = 14)
	cell.alignment = Alignment(horizontal = 'center', vertical = 'center')
	cell.fill = PatternFill(start_color = 'D9D9D9', end_color = 'D9D9D9', fill_type = 'solid')
	cell.border = Border(left = Side(style = 'thin'), right = Side(style = 'thin'), top = Side(style = 'thin'),
	                     bottom = Side(style = 'double'))


def write_match_list(data: list):
	if os.path.exists('output.xlsx'):
		workbook = load_workbook(filename = 'output.xlsx', data_only = False)
	else:
		workbook = Workbook()

	# 获取工作簿中的所有工作表
	worksheets = workbook.worksheets

	# 检查第一个工作表是否命名为“场次列表”
	if worksheets[0].title == '场次列表':
		match_list_worksheet = worksheets[0]
	else:
		# 创建一个场次列表
		match_list_worksheet = workbook.create_sheet('场次列表', 0)

	# 写入表头
	headers = ['场次', '赛事', '比赛时间', '主', '比分', '客', 'ID', '选中']
	for col_num, header in enumerate(headers, 1):
		match_list_worksheet.cell(row = 1, column = col_num).value = header
		set_header_style(match_list_worksheet.cell(row = 1, column = col_num))

	# 设置列宽
	column_widths = [5, 10, 20, 20, 10, 20, 10]
	for col_num, width in enumerate(column_widths, 1):
		match_list_worksheet.column_dimensions[
			match_list_worksheet.cell(row = 1, column = col_num).column_letter].width = width

	# 将查询结果写入工作表
	for row_num, row in enumerate(data, 2):
		match_list_worksheet.cell(row = row_num, column = 1).value = row_num - 1  # 场次
		match_list_worksheet.cell(row = row_num, column = 2).value = row[0]  # 赛事
		match_list_worksheet.cell(row = row_num, column = 3).value = f"{row[1]} {row[2]}"  # 比赛时间
		match_list_worksheet.cell(row = row_num, column = 4).value = row[3]  # 主队
		if row[6] and row[7]:
			match_list_worksheet.cell(row = row_num, column = 5).value = f"{row[6]} - {row[7]}"  # 比分
		match_list_worksheet.cell(row = row_num, column = 6).value = row[4]  # 客队
		match_list_worksheet.cell(row = row_num, column = 7).value = row[5]  # ID

	workbook.save('output.xlsx')
	workbook.close()


def get_selected_ids(workbook_path = "output.xlsx", sheet_name="场次列表"):
	# 加载工作簿和工作表
	wb = load_workbook(workbook_path, data_only = True)
	match_list_worksheet = wb[sheet_name]

	selected_ids = []

	# 遍历“选中”列
	for row_num in range(2, match_list_worksheet.max_row + 1):
		selected = match_list_worksheet.cell(row = row_num, column = 8).value
		if selected == 1:
			# 获取相应的 ID 并添加到列表中
			match_id = match_list_worksheet.cell(row = row_num, column = 7).value
			selected_ids.append(match_id)

	return selected_ids
