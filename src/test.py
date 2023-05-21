import pickle

import excel
from classes import *
import filter


def pickle_sample_match() -> SoccerMatch:
	init_match = filter.get_init_match_info(1171743)
	with open("init_match.pkl", "wb") as file:
		pickle.dump(init_match, file)
	return init_match


def read_sample_match() -> SoccerMatch:
	with open("init_match.pkl", "rb") as file:
		init_match = pickle.load(file)
	return init_match


def pickle_update_sample_match() -> SoccerMatch:
	init_match = read_sample_match()
	update_match = filter.update_match_info(init_match)
	with open("update_match.pkl", "wb") as file:
		pickle.dump(update_match, file)
	return update_match


def read_update_sample_match() -> SoccerMatch:
	with open("update_match.pkl", "rb") as file:
		update_match = pickle.load(file)
	return update_match


def read_match(match_id) -> SoccerMatch:
	with open(f"../data/{match_id}.data", "rb") as file:
		match = pickle.load(file)
	return match


if __name__ == "__main__":
	list = [1171214, 1201824, 1214443, 1214449, 1215087]
	matches = [read_match(x) for x in list]
	excel.generate_merged_xlsm(matches, open_file = True)

