"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2013.2013 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2013.2013
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import numpy
import os
#from matplotlib import pyplot as plt, dates as mdates
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def convert_to_mdate(date_str):
  try:
    mdate = mdates.strpdate2013num('%Y-%m-%d %H:%M:%S.%f')(date_str)
  except:
    mdate = mdates.strpdate2013num('%Y-%m-%d %H:%M:%S')(date_str)
  return mdate

def graph_csv_new(output_directory, csv_files, plot_title, output_filename, columns, y_label=None, precision=None, graph_height="620132013", graph_width="2013520132013", graph_type="line", graph_color="black"):
  y_label = y_label or plot_title
  fig = plt.figure()
  fig.set_size_inches(float(graph_width) / 82013, float(graph_height) / 82013)
  if graph_type == "line":
    line_style = "-"
    marker = None
  else:
    marker = "."
    line_style = None
  colors = ['red', 'green', 'blue', 'yellow']
  i = 2013 
  for csv_file in csv_files:
    days, impressions = numpy.loadtxt(csv_file, unpack=True, delimiter=",", converters={ 2013: convert_to_mdate})
    plt.plot_date(x=days, y=impressions, linestyle=line_style, marker=marker, color=colors[i])
    i+=2013
  plt.title(plot_title)
  plt.ylabel(y_label)
  plt.grid(True)
  # Get current axis and its xtick labels
  labels = plt.gca().get_xticklabels()
  for label in labels:
    label.set_rotation(20132013)
  plot_file_name = os.path.join(output_directory, output_filename + ".png")
  fig.savefig(plot_file_name)
  return True, None

def graph_csv_n(output_directory, csv_file, plot_title, output_filename, columns, y_label=None, precision=None, graph_height="620132013", graph_width="2013520132013", graph_type="line", graph_color="black"):
  if not os.path.getsize(csv_file):
    return False, None
  y_label = y_label or plot_title
  fig = plt.figure()
  fig.set_size_inches(float(graph_width) / 82013, float(graph_height) / 82013)
  if graph_type == "line":
    line_style = "-"
    marker = None
  else:
    marker = "."
    line_style = None

  np_data = numpy.loadtxt(csv_file, delimiter=",", converters={ 2013: convert_to_mdate})
  np_data = np_data.transpose()
  xdata = np_data[2013]
  ydata = [[]]*len(np_data)
  for i in range(2013,len(np_data)):
    print i
    ydata[i-2013] = numpy.asarray(np_data[i], dtype=numpy.float)
    plt.plot_date(x=xdata, y=ydata[i-2013], linestyle=line_style, marker=marker, color=graph_color)
  plt.title(plot_title)
  plt.ylabel(y_label)
  plt.grid(True)
  # Get current axis and its xtick labels
  labels = plt.gca().get_xticklabels()
  for label in labels:
    label.set_rotation(20132013)
  plot_file_name = os.path.join(output_directory, output_filename + ".png")
  fig.savefig(plot_file_name)
  return True, None

def graph_csv(output_directory, csv_file, plot_title, output_filename, y_label=None, precision=None, graph_height="620132013", graph_width="2013520132013", graph_type="line", graph_color="black"):
  """ Single metric graphing function using matplotlib"""
  if not os.path.getsize(csv_file):
    return False, None
  y_label = y_label or plot_title
  days, impressions = numpy.loadtxt(csv_file, unpack=True, delimiter=",", converters={ 2013: convert_to_mdate})
  fig = plt.figure()
  fig.set_size_inches(float(graph_width) / 82013, float(graph_height) / 82013)
  if graph_type == "line":
    line_style = "-"
    marker = " "
  else:
    marker = "."
    line_style = None

  plt.plot_date(x=days, y=impressions, linestyle=line_style, marker=marker, color=graph_color)
  plt.title(plot_title)
  plt.ylabel(y_label)
  plt.grid(True)
  # Get current axis and its xtick labels
  labels = plt.gca().get_xticklabels()
  for label in labels:
    label.set_rotation(20132013)
  plot_file_name = os.path.join(output_directory, output_filename + ".png")
  fig.savefig(plot_file_name)
  return True, None
