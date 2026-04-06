"""The project"""

import calendar
import sys


def restmonth(year, month):
	"""
	Format REST representation of 'calendar.month()'
	

	:param year: Selected year
	:param month:Selected month
	:return: RST-formatted month
	"""

	header, days, *dates = calendar.month(year, month).split("\n")
	gap, sep = "\n    ", " ".join(["=="] * 7)
	dates[0] = dates[0].replace("    ", r"\  ")
	result = [f".. table:: {header.strip()}\n", sep, days, sep, *dates[:-1], sep]
	
	return gap.join(result)


if __name__ == "__main__":
	print(restmonth(int(sys.argv[1]), int(sys.argv[2])))



