import csv
import sys

from datetime import datetime

def read_data(csv_name):
	'''
	read data from csv in to a list
	'''
	data = []
	with open(csv_name, 'rb') as csv_data:
		reader = csv.reader(csv_data, delimiter=',', quotechar='|')
		for row in reader:
			try:
				row[1] = float(row[1])
				data.append(row)
			#ignore if value is NaN
			except ValueError:
				pass
	return data

def write_data(csv_name, data):
	'''
	write data to a csv file from a list
	'''
	with open(csv_name, 'wb+') as csv_file:
		writer = csv.writer(csv_file)
		for row in data:
			writer.writerow(row)

def auto_increment(lst, key):
	'''
	auto-increment a count dictionary
	'''
	lst[key] = lst[key]+1 if key in lst else 1
	return lst

def computer_ema(smoothing_factor, points):
	'''
	compute exponential moving average of a list of points
	'''
	ema  = list()
	#the initial point has a ema equal to itself
	if(len(points) > 0):
		ema.append(points[0])
	for i in xrange(1, len(points)):
		ema.append(smoothing_factor*points[i]+(1-smoothing_factor)*ema[i-1])
	return ema

def parse_timestamp_str(t_str):
	'''
	covert a timestamp string to total seconds
	'''
	try:
		t = datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S.%f")
	except:
		t = datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S")
	return t