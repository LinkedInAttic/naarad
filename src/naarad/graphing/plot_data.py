# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""


class PlotData:
  """Class to hold details of the metrics to be plotted"""
  def __init__(self, input_csv, csv_column, series_name, y_label, precision, graph_height, graph_width, graph_type, x_label=None, plot_label=None, highlight_regions=None):
    self.input_csv = input_csv
    self.csv_column = csv_column
    self.graph_title = series_name
    self.y_label = y_label
    self.precision = precision
    if graph_height is None:
      self.graph_height = 600
    else:
      self.graph_height = graph_height
    if graph_width is None:
      self.graph_width = 1200
    else:
      self.graph_width = graph_width
    self.graph_type = graph_type
    self.plot_label = plot_label
    self.x_label = x_label
    self.highlight_regions = highlight_regions
    return None
