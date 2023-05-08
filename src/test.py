import pickle
import classes
import filter


def pickle_sample_match() -> classes.SoccerMatch:
	init_match = filter.get_init_match_info(1171743)
	with open("init_match.pkl", "wb") as file:
		pickle.dump(init_match, file)
	return init_match

def read_sample_match() -> classes.SoccerMatch:
	# Using pickle.load()
	with open("init_match.pkl", "rb") as file:
		init_match = pickle.load(file)
	return init_match


if __name__ == "__main__":
	print(pickle_sample_match().__dict__)
