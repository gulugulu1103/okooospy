import os
import pickle
from classes import *


def save_match(match: SoccerMatch) -> None:
	with open(f"../data/{match.match_id}.data", "wb") as file:
		pickle.dump(match, file)


def read_match(match_id) -> SoccerMatch | None:
	if os.path.exists(f"../data/{match_id}.data"):
		with open(f"../data/{match_id}.data", "rb") as file:
			match = pickle.load(file)
		return match
	return None


def read_matches(match_ids: list) -> List[SoccerMatch]:
	matches = []
	for match_id in match_ids:
		# detect whether the file exists
		if not os.path.exists(f"../data/{match_id}.data"):
			continue
		with open(f"{match_id}.data", "rb") as file:
			matches.append(pickle.load(file))
	return matches


def save_selected_list(selected: List[str]) -> None:
	"""
	保存选中的比赛 ID 列表，用于GUI
	Returns: None
	"""
	with open('selected_matches.txt', 'w') as f:
		f.write('\n'.join(selected))


def read_selected_list() -> List[str]:
	"""
	读入选中的比赛 ID 列表，用于GUI
	Returns:比赛ID列表
	"""
	selected = []
	if os.path.exists('selected_matches.txt'):
		with open('selected_matches.txt', 'r') as f:
			selected = f.read().split('\n')
	return selected


def save_show_matches(show_matches: List[Tuple[str, str, str, str, str, str]]) -> None:
	"""
	保存显示比赛列表，用于GUI
	Returns: None
	"""
	with open('show_matches.txt', 'w') as f:
		for match in show_matches:
			f.write(','.join(match))
			f.write('\n')


def read_show_matches() -> List[Tuple[str, str, str, str, str, str]]:
	"""
	读入显示比赛列表，用于GUI
	Returns:显示比赛列表
	"""
	show_matches = []
	if os.path.exists('show_matches.txt'):
		with open('show_matches.txt', 'r') as f:
			for line in f.readlines():
				show_matches.append(tuple(line.strip().split(',')))
	return show_matches


if __name__ == '__main__':
	print(read_selected_list())
	print(read_show_matches())
