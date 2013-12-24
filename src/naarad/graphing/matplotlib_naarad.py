# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import numpy
import os
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import logging

logger = logging.getLogger('naarad.graphing.matplotlib')


def convert_to_mdate(date_str):
  try:
    mdate = mdates.strpdate2num('%Y-%m-%d %H:%M:%S.%f')(date_str)
  except:
    mdate = mdates.strpdate2num('%Y-%m-%d %H:%M:%S')(date_str)
  return mdate

# MPL-WA-07
# matplotlib does not rotate colors correctly when using multiple y axes. This method fills in that gap.
def get_current_color(index):
  colors = ['black', 'orange', 'steelblue', 'm', 'red', 'cyan', 'g', 'gray']
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
    elif title != plot.graph_title:
      title = title + ',' + plot.graph_title
  return height/80, width/80, title


def curate_plot_list(plots):
  delete_nodes = []
  for plot in plots:
    if os.path.exists(plot.input_csv):
      if not os.path.getsize(plot.input_csv):
        logger.warning("%s file is empty. No plot corresponding to this file will be generated", plot.input_csv)
        delete_nodes.append(plot)
    else:
      logger.warning("%s file does not exist. No plot corresponding to this file will be generated", plot.input_csv)
      delete_nodes.append(plot)
  for node in delete_nodes:
    plots.remove(node)
  return plots


def graph_data(list_of_plots, output_directory, resource_path, output_filename):
  plots = curate_plot_list(list_of_plots)
  plot_count = len(plots)
  if plot_count == 0:
    return False, None
  graph_height, graph_width, graph_title = get_graph_metadata(list_of_plots)
  current_plot_count = 0
  fig, axis = plt.subplots()
  fig.set_size_inches(graph_width, graph_height)
  if plot_count < 2:
    fig.subplots_adjust(left=0.05, bottom=0.1, right=0.95)
  else:
    fig.subplots_adjust(left=0.05, bottom=0.1, right=0.95 - 0.04 * (plot_count - 2))
  current_axis = axis
  for plot in plots:
    current_plot_count += 1
    logger.info('Processing: ' + plot.input_csv + ' [ ' + output_filename + ' ]')
    timestamp, yval = numpy.loadtxt(plot.input_csv, unpack=True, delimiter=',', converters={0: convert_to_mdate})
    #maximum_yvalue = numpy.amax(yval) * (1.0 + 0.005 * current_plot_count)
    maximum_yvalue = numpy.amax(yval) * 1.005
    #minimum_yvalue = numpy.amin(yval) * (1.0 - 0.005 * current_plot_count)
    minimum_yvalue = 0
    if current_plot_count == 0:
      current_axis.yaxis.set_ticks_position('left')
    if current_plot_count > 1:
      current_axis = axis.twinx()
      current_axis.yaxis.grid(False)
      #Set right y-axis for additional plots
      current_axis.yaxis.set_ticks_position('right')
      #Offset the right y axis to avoid overlap
      current_axis.spines['right'].set_position(('axes', 1 + 0.06 * (current_plot_count-2)))
      current_axis.spines['right'].set_smart_bounds(True)
      current_axis.spines['right'].set_color(get_current_color(current_plot_count))
      current_axis.set_frame_on(True)
      current_axis.patch.set_visible(False)
    current_axis.set_ylabel(plot.y_label, color=get_current_color(current_plot_count), fontsize=10)
    current_axis.set_ylim([minimum_yvalue, maximum_yvalue])
    if plot.graph_type == 'line':
      current_axis.plot_date(x=timestamp, y=yval, linestyle='-', marker=None, color=get_current_color(current_plot_count))
    else:
      current_axis.plot_date(x=timestamp, y=yval, marker='.', color=get_current_color(current_plot_count))
    y_ticks = current_axis.get_yticklabels()
    for y_tick in y_ticks:
      y_tick.set_color(get_current_color(current_plot_count))
      y_tick.set_fontsize(8)
    for x_tick in current_axis.get_xticklabels():
      x_tick.set_fontsize(8)
  axis.yaxis.grid(True)
  axis.xaxis.grid(True)
  axis.set_title(graph_title)
  axis.set_xlabel('Time')
  x_date_format = mdates.DateFormatter('%H:%M:%S')
  axis.xaxis.set_major_formatter(x_date_format)
  plot_file_name = os.path.join(output_directory, output_filename + ".png")
  fig.savefig(plot_file_name)
  plt.close()
  #Create html fragment to be used for creation of the report
  with open(os.path.join(output_directory, output_filename + '.div'), 'w') as div_file:
    div_file.write('<img src="' + resource_path + '/' + os.path.basename(plot_file_name) + '" id="' + os.path.basename(plot_file_name) + '" width="100%" height="auto"/>')
  return True, os.path.join(output_directory, output_filename + '.div')
