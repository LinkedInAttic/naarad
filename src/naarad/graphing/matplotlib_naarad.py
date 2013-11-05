# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import numpy
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import logging
from plot_data import *


logger = logging.getLogger('naarad.graphing.matplotlib')

def convert_to_mdate(date_str):
  try:
    mdate = mdates.strpdate2num('%Y-%m-%d %H:%M:%S.%f')(date_str)
  except:
    mdate = mdates.strpdate2num('%Y-%m-%d %H:%M:%S')(date_str)
  return mdate

def get_current_color(index):
  colors = ['g', 'b', 'y', 'r', 'c', 'm', 'k']
  return colors[index % len(colors)]

def get_graph_metadata(plots):
  height = 0
  width = 0
  title = ''
  for plot in plots:
    if plot.graph_height > height:
      height = plot.graph_height
    if plot.graph_width > width:
      width = plot.graph_width
    if title == '':
      title = plot.graph_title
    else:
      title = title + ',' + plot.graph_title
  return height/80, width/80, title

def graph_csv_new(output_directory, csv_files, plot_title, output_filename, columns, y_label=None, precision=None, graph_height="600", graph_width="1500", graph_type="line", graph_color="black"):
  y_label = y_label or plot_title
  fig = plt.figure()
  fig.set_size_inches(float(graph_width) / 80, float(graph_height) / 80)
  if graph_type == "line":
    line_style = "-"
    marker = None
  else:
    marker = "."
    line_style = None
  colors = ['red', 'green', 'blue', 'yellow']
  i = 0 
  for csv_file in csv_files:
    days, impressions = numpy.loadtxt(csv_file, unpack=True, delimiter=",", converters={ 0: convert_to_mdate})
    plt.plot_date(x=days, y=impressions, linestyle=line_style, marker=marker, color=colors[i])
    i+=1
  plt.title(plot_title)
  plt.ylabel(y_label)
  plt.grid(True)
  # Get current axis and its xtick labels
  labels = plt.gca().get_xticklabels()
  for label in labels:
    label.set_rotation(30)
  plot_file_name = os.path.join(output_directory, output_filename + ".png")
  fig.savefig(plot_file_name)
  plt.close()
  return True, None

def graph_csv_n(output_directory, csv_file, plot_title, output_filename, columns, y_label=None, precision=None, graph_height="600", graph_width="1500", graph_type="line", graph_color="black"):
  if not os.path.getsize(csv_file):
    return False, None
  y_label = y_label or plot_title
  fig = plt.figure()
  fig.set_size_inches(float(graph_width) / 80, float(graph_height) / 80)
  if graph_type == "line":
    line_style = "-"
    marker = None
  else:
    marker = "."
    line_style = None

  np_data = numpy.loadtxt(csv_file, delimiter=",", converters={ 0: convert_to_mdate})
  np_data = np_data.transpose()
  xdata = np_data[0]
  ydata = [[]]*len(np_data)
  for i in range(1,len(np_data)):
    print i
    ydata[i-1] = numpy.asarray(np_data[i], dtype=numpy.float)
    plt.plot_date(x=xdata, y=ydata[i-1], linestyle=line_style, marker=marker, color=graph_color)
  plt.title(plot_title)
  plt.ylabel(y_label)
  plt.grid(True)
  # Get current axis and its xtick labels
  labels = plt.gca().get_xticklabels()
  for label in labels:
    label.set_rotation(20)
  plot_file_name = os.path.join(output_directory, output_filename + ".png")
  fig.savefig(plot_file_name)
  plt.close()
  return True, None

def graph_csv(output_directory, csv_file, plot_title, output_filename, y_label=None, precision=None, graph_height="600", graph_width="1500", graph_type="line", graph_color="black"):
  """ Single metric graphing function using matplotlib"""
  if not os.path.getsize(csv_file):
    return False, None
  y_label = y_label or plot_title
  days, impressions = numpy.loadtxt(csv_file, unpack=True, delimiter=",", converters={ 0: convert_to_mdate})
  fig = plt.figure()
  fig.set_size_inches(float(graph_width) / 80, float(graph_height) / 80)
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
    label.set_rotation(30)
  plot_file_name = os.path.join(output_directory, output_filename + ".png")
  fig.savefig(plot_file_name)
  plt.close()
  return True, None

def graph_data(list_of_plots, output_directory, output_filename):
  plot_count = len(list_of_plots)

  if plot_count == 0:
    return True, None

  graph_height, graph_width, graph_title = get_graph_metadata(list_of_plots)

  current_plot_count=0
  if plot_count <= 2:
    fig, axis = plt.subplots()
    fig.set_size_inches(graph_width, graph_height)
    fig.subplots_adjust(bottom=0.2)
    for plot in list_of_plots:
      current_plot_count += 1
      current_axis = axis
      logger.info('Processing: ' + plot.input_csv)
      if not os.path.getsize(plot.input_csv):
        logger.warning('%s is empty.', plot.input_csv)
        return False, None
      timestamp, yval = numpy.loadtxt(plot.input_csv, unpack=True, delimiter=',', converters={0: convert_to_mdate})
      if current_plot_count > 1:
        current_axis = axis.twinx()
      current_axis.set_ylabel(plot.graph_title + '(' + plot.y_label + ')', color=get_current_color(current_plot_count))
      if plot.graph_type == 'line':
        current_axis.plot_date(x=timestamp, y=yval, linestyle='-', marker=None, color=get_current_color(current_plot_count))
      else:
        current_axis.plot_date(x=timestamp, y=yval, linestyle=None, marker='.', color=get_current_color(current_plot_count))
      y_ticks = current_axis.get_yticklabels()
      for y_tick in y_ticks:
        y_tick.set_color(get_current_color(current_plot_count))
  else:
    fig = plt.figure()
    host = host_subplot(111, axes_class=AA.Axes)
    axis_offset = 0.75
    fig.subplots_adjust(right=1-0.05*plot_count, bottom=0.2)
    fig.set_size_inches(graph_width, graph_height)
    for plot in list_of_plots:
      current_plot_count += 1
      logger.info('Processing: ' + plot.input_csv)
      if not os.path.getsize(plot.input_csv):
        logger.warning('%s is empty.', plot.input_csv)
        return False, None
      timestamp, yval = numpy.loadtxt(plot.input_csv, unpack=True, delimiter=',', converters={0:convert_to_mdate})
      if current_plot_count == 1:
        current_axis = host
      else:
        current_axis = host.twinx()
        new_y_axis = current_axis.get_grid_helper().new_fixed_axis
        current_axis.axis['right'] = new_y_axis(loc='right', axes=current_axis, offset=((current_plot_count-2) * axis_offset, 0))
        current_axis.axis['right'].toggle(all=True)
      current_axis.set_ylabel(plot.graph_title + '(' + plot.y_label + ')', color=get_current_color(current_plot_count))
      if plot.graph_type == 'line':
        current_axis.plot_date(x=timestamp, y=yval, linestyle='-', marker=None, color=get_current_color(current_plot_count))
      else:
        current_axis.plot_date(x=timestamp, y=yval, linestyle=None, marker='.', color=get_current_color(current_plot_count))
  plt.title(graph_title)
  plt.xlabel('Time')
  plt.grid(True)
  plt.setp(current_axis.xaxis.get_majorticklabels(), rotation=20)
  plot_file_name = os.path.join(output_directory, output_filename + ".png")
  fig.savefig(plot_file_name)
  plt.close()
  return True,None
