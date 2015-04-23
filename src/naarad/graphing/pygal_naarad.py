# coding=utf-8
"""
Copyright 2013 LinkedIn Corp. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import datetime
import pygal
import os
import logging

logger = logging.getLogger('naarad.graphing.pygal_naarad')


def convert_to_date(date_str):
  return datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')


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
  date_plot = pygal.DateY(x_label_rotation=20, height=500, width=1200, legend_at_bottom=True, style=pygal.style.BlueStyle)
  for plot in list_of_plots:
    plot_data = []
    with open(plot.input_csv, 'r') as csv_data:
      for line in csv_data:
        line_data = line.strip('\n').split(',')
        if '.' in line_data[0]:
          plot_data.append((datetime.datetime.strptime(line_data[0], '%Y-%m-%d %H:%M:%S.%f'), float(line_data[1])))
        else:
          plot_data.append((datetime.datetime.strptime(line_data[0], '%Y-%m-%d %H:%M:%S'), float(line_data[1])))
    date_plot.add(plot.graph_title, plot_data)
    date_plot.render_to_file(os.path.join(output_directory, output_filename + '.svg'))
    with open(os.path.join(output_directory, output_filename + '.div'), 'w') as div_file:
      div_file.write('<figure><embed type="image/svg+xml" src="' + resource_path + '/' + output_filename + '.svg' + '"/></figure>')
    return True, os.path.join(output_directory, output_filename + '.div')


def graph_data_on_the_same_graph(list_of_plots, output_directory, resource_path, output_filename):
  """
  graph_data_on_the_same_graph: put a list of plots on the same graph: currently it supports CDF
  """
  logger.warning('graph_data_on_the_same_graph is currently not supported in pygal')
  return False, None
