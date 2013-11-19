# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import logging
import os
import glob
import sys
from nose import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src')))

import naarad.graphing.matplotlib_naarad as mpl_n
from naarad.graphing.plot_data import PlotData as PlotData
logger = logging.getLogger('naarad')

def validate(filename):
  if os.path.exists(filename):
    if not os.path.getsize(filename):
      return False
    else:
      return True
  else:
    return False

def plot(list_of_plots, output_file, scenario_name, validation):
  mpl_n.graph_data(list_of_plots, '.', output_file)
  assert validate(output_file + '.png') == validation

def init_logging(log_level):
  log_file = 'test_matplotlib.log'
  # clear the log file
  with open(log_file, 'w'):
    pass
  numeric_level = getattr(logging, log_level.upper(), None) if log_level else logging.INFO
  if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % log_level)
  logger.setLevel(logging.DEBUG)
  fh = logging.FileHandler(log_file)
  fh.setLevel(logging.DEBUG)
  ch = logging.StreamHandler()
  ch.setLevel(numeric_level)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  fh.setFormatter(formatter)
  ch.setFormatter(formatter)
  logger.addHandler(fh)
  logger.addHandler(ch)

def setup_matplotlib_tests():
  init_logging('INFO')
  png_list = glob.glob('test*.png')
  for png in png_list:
    os.remove(png)
    logger.info('Deleting : %s', png)

#Test Cases
@with_setup(setup_matplotlib_tests())
def test_generator():
  #Test Data
  plot1 = PlotData('test1.csv', 1, 'GC Commit', 'MB', None, 600, 1200, 'line')
  plot2 = PlotData('test2.csv', 1, 'GC CMS Pause', 'seconds', None, 600, 1200, 'line')
  plot3 = PlotData('test3.csv', 1, 'GC Promo', 'bps', None, 600, 1200, 'line')
  plot4 = PlotData('test4.csv', 1, 'GC Promo', 'bps', None, 600, 1200, 'line')
  plot5 = PlotData('test5.csv', 1, 'GC Promo', 'bps', None, 600, 1200, 'line')
  yield plot, [plot1], 'test1', 'single plot with all valid csv', True
  yield plot, [plot1, plot2], 'test2', 'dual plot with all valid csv', True
  yield plot, [plot1, plot2, plot3], 'test3', 'multi plot with all valid csv', True
  yield plot, [plot4], 'test4', 'single plot with 1 empty csv', False
  yield plot, [plot4, plot1], 'test5', 'dual plot with 1 empty csv', True
  yield plot, [plot1, plot4, plot3], 'test6', 'multi plot with 1 empty csv', True
  yield plot, [plot5], 'test7', 'single plot with 1 non-existent csv', False
  yield plot, [plot5, plot1], 'test8', 'dual plot with 1 non-existent csv', True
  yield plot, [plot1, plot5, plot3], 'test9', 'multi plot with 1 non-existent csv', True