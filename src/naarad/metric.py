# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import calendar
from collections import defaultdict
import datetime
#from matplotlib import pyplot as plt, dates as mdates
#import numpy as np
import logging
import os
import pytz
from pytz import timezone
import re
import sys
import threading
import time
import urllib

logger = logging.getLogger('naarad.Metric')

##########################
# GLOBAL FUNCTIONS
#########################

def is_valid_url(url):
  """
  Check if a given string is in the correct URL format or not

  :param str url:
  :return: True or False
  """
  regex = re.compile(
      r'^(?:http|ftp)s?://' # http:// or https://
      r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
      r'localhost|' #localhost...
      r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
      r'(?::\d+)?' # optional port
      r'(?:/?|[/?]\S+)$', re.IGNORECASE)
  if regex.match(url):
    logger.info( "URL given as config")
    return True
  else:
    return False

def download_file(url):
  """
  Download a file pointed to by url to a temp file on local disk

  :param str url:
  :return: local_file
  """
  try:
    (local_file,headers) = urllib.urlretrieve(url)
  except:
    sys.exit("ERROR: Problem downloading config file. Please check the URL (" + url + "). Exiting...")
  return local_file

def reconcile_timezones(begin_ts, ts_timezone, graph_timezone):
  if not graph_timezone:
    return begin_ts
  # Converting timestamp strings to be in timezone: graph_timezone
  # We only support UTC and PDT
  if graph_timezone != ts_timezone:
    utc = pytz.utc
    pst = timezone('US/Pacific')
    if graph_timezone == "UTC":
      # Assume timezone is PDT
      try:
        dt = pst.localize(datetime.datetime.strptime(begin_ts,"%Y-%m-%d %H:%M:%S"))
      except ValueError:
        dt = pst.localize(datetime.datetime.strptime(begin_ts,"%Y-%m-%d %H:%M:%S.%f"))
      begin_ts = dt.astimezone(utc).strftime("%Y-%m-%d %H:%M:%S.%f")
    else:
      # Assume timezone is UTC since graph_timezone is PDT
      try:
        dt = utc.localize(datetime.datetime.strptime(begin_ts,"%Y-%m-%d %H:%M:%S"))
      except ValueError:
        dt = utc.localize(datetime.datetime.strptime(begin_ts,"%Y-%m-%d %H:%M:%S.%f"))
      begin_ts = dt.astimezone(pst).strftime("%Y-%m-%d %H:%M:%S.%f")
  return begin_ts

def convert_to_unixts(ts_string):
  try:
    dt_obj = datetime.datetime.strptime(ts_string, "%Y-%m-%d %H:%M:%S.%f")
  except ValueError:
    dt_obj = datetime.datetime.strptime(ts_string, "%Y-%m-%d %H:%M:%S")
  return float(calendar.timegm(dt_obj.utctimetuple())*1000.0 + dt_obj.microsecond/1000.0)

def is_number(string):
  try:
    float(string)
    return True
  except ValueError:
    return False

def get_all_sar_objects(metrics, indir, access, output_directory, label, ts_start, ts_end, options):
  metrics = []
  sar_types = ('device', 'cpuusage', 'cpuhz', 'memory', 'memutil', 'paging')
  for sar_metric_type in sar_types:
    #infile = indir + '/' + 'sar.' + sar_metric_type + '.out'
    infile = os.path.join(indir, 'sar.' + sar_metric_type + '.out')
    if os.path.exists(infile):
      obj_type = 'SAR-' + sar_metric_type
      metric = SARMetric(obj_type, infile, access, output_directory, label, ts_start, ts_end, options)
      metrics.append(metric)
  return metrics

def sanitize_string(string):
  string = string.replace('/', '-per-')
  if string.startswith('%'):
    string = string.replace('%', 'percent-')
  else:
    string = string.replace('%', '-percent-')
  return string

def get_default_csv(output_directory, val):
  val = sanitize_string(val)
  return os.path.join(output_directory, val + '.csv')

def convert_to_24hr_format(ts):
  words = ts.split()
  if len(words) == 1:
    return ts
  if words[1] == 'PM':
    tmp = words[0].split(':')
    hour = int(tmp[0]) + 12
    tmp[0] = str(hour)
    ts = ":".join(tmp)
  elif words[1] == 'AM':
    tmp = words[0].split(':')
    if tmp[0] == '12':
      tmp[0] = '00'
    ts = ":".join(tmp)
  return ts

def get_merged_csvname(output_directory, vals):
  return os.path.join(output_directory, '-'.join(vals) + '.csv')

def get_merged_charttitle(vals):
  return " vs ".join(vals)

def get_merged_plot_link_name(vals):
  return '-'.join(vals)

def get_merged_png_name(vals):
  return '-'.join(vals) + '.png'

def generate_html_report(output_directory, html_string):
  htmlfilename = os.path.join(output_directory, 'Report.html')
  with open(htmlfilename, 'w') as htmlf:
    header = '<html><head>'
    dygraphs_include = '''<script type='text/javascript'
      src='http://dygraphs.com/dygraph-combined.js'></script>
      </head>
      <body>'''
    htmlf.write(header)
    htmlf.write(dygraphs_include)
    htmlf.write(html_string)
    footer = '</body></html>'
    htmlf.write(footer)

def tscsv_nway_file_merge(outfile, filelist, filler):
  logger.info('called nway merge with %s', filelist)
  with open(outfile, 'w') as outf:
    filehandlers = [None] * len(filelist)
    currlines = [None] * len(filelist)
    for i in range(len(filelist)):
      try:
        filehandlers[i] = open(filelist[i], 'r')
      except IOError:
        logger.error('Cannot open: ' +  filelist[i])
        return
      currlines[i] = filehandlers[i].readline().strip()
    while True:
      # Assuming logs won't have far future dates - 1 yr max since sometimes people have logs in near future dates
      future_time = str( datetime.datetime.utcnow() + datetime.timedelta(days=365))
      min_ts = future_time
      for i in range(len(currlines)):
        if currlines[i] == "":
          continue
        ts = currlines[i].split(',')[0]
        if ts < min_ts:
          min_ts = ts
      if min_ts == future_time:
        break
      outwords = []
      outwords.append(min_ts)
      for i in range(len(currlines)):
        if currlines[i] == "":
          outwords.append(filler)
        else:
          ts = currlines[i].split(',')[0]
          val = currlines[i].split(',')[1]
          if ts == min_ts:
            outwords.append(val)
            currlines[i] = filehandlers[i].readline().strip()
          else:
            outwords.append(filler)
      outf.write( ','.join(outwords) + '\n' )

def nway_plotting(crossplots, metrics, output_directory, filler):
  listlen = len(crossplots)
  if listlen == 0:
    return ''
  html_string = []
  linkstring = []
  linkstring.append("<h1><a name=\"Correlated-Plots\"></a>Correlated Plots</h1>\n")
  linkstring.append("<div><ul>")
  i = 0
  #GC.appstop,all GC.alloc,GC.alloc-rate GC.promo,GC.gen0t,GC.gen0sys
  while i < listlen:
    plot = crossplots[i]
    vals = plot.split(',')
    i += 1
    if not 'all' in vals:
      csv_files = []
      for val in vals:
        csv_file = get_default_csv(output_directory, val)
        csv_files.append(csv_file)
      for j in range(len(vals)):
        vals[j] = sanitize_string(vals[j])
      merged_filename = get_merged_csvname(output_directory, vals)
      plot_title = get_merged_charttitle(vals)
      png_name = get_merged_plot_link_name(vals)
      merged_plotfile = get_merged_png_name(vals)

      tscsv_nway_file_merge(merged_filename, csv_files, filler)
      Metric.graphing_modules['matplotlib'].graph_csv_new(output_directory, csv_files, plot_title, png_name, vals)

      img_tag = "<h3><a name=\"{0}\"></a>{1}</h3><img src={2} />".format(png_name, plot_title, merged_plotfile)
      link_tag = "<li><a href=\"#{0}\">{1}</a></li>".format(png_name, plot_title)
      html_string.append(img_tag)
      linkstring.append(link_tag)
    else:
      vals.remove('all')
      for metric in metrics:
        for csv in metric.csv_files:
          csv_filename = csv.split('/')[-1]
          metric_name = '.'.join(csv_filename.split('.')[0:-1])
          if metric_name in vals:
            continue
          new_val = []
          new_val.extend(vals)
          new_val.append(metric_name)
          new_val_str = ','.join(new_val)
          crossplots.append(new_val_str)
          listlen += 1
  linkstring.append("</ul></div>")
  linkstring.extend(html_string)
  return '\n'.join(linkstring)

##########################
# CLASS DEFINITIONS
#########################

class Metric(object):
  beginning_ts = None
  beginning_date = None
  ignore = False
  timezone = "PDT"
  options = None

  def __init__ (self, metric_type, infile, access, output_directory, label, ts_start, ts_end, **other_options):
    self.metric_type = metric_type
    self.infile = infile
    self.access = access
    self.outdir = output_directory
    self.label = label
    self.ts_start = ts_start
    self.ts_end = ts_end
    self.calc_metrics = None
    self.precision = None
    self.sep = ','
    self.titles_string = None
    self.ylabels_string = None
    self.csv_files = []
    self.metric_description = defaultdict(lambda: 'None')
    if other_options:
      for (key,val) in other_options.iteritems():
        setattr(self, key, val)
      if not self.titles_string:
        self.titles_string = self.columns
      if self.columns:
        self.columns = self.columns.split()
      self.titles = dict(zip(self.columns, self.titles_string.split(','))) if self.columns and self.titles_string else None
      self.ylabels = dict(zip(self.columns, self.ylabels_string.split(','))) if self.columns and self.ylabels_string else None

  def ts_out_of_range(self, timestamp):
    if self.ts_start and timestamp < self.ts_start:
      return True
    elif self.ts_end and timestamp > self.ts_end:
      return True
    return False

  def collect_local(self):
    return os.path.exists(self.infile)

  def collect(self):
    if self.access == 'local':
      return self.collect_local()
    else:
      logger.warn("WARNING: access is set to other than local for metric", self.label)
      return False

  def get_csv(self, column):
    col = sanitize_string(column)
    csv = os.path.join(self.outdir, self.metric_type + '.' + col + '.csv')
    return csv

  def parse(self):
    logger.info("Working on" + self.infile)
    with open(self.infile, 'r') as infile:
      data = {}
      for line in infile:
        if self.sep is None:
          words = line.strip().split()
        else:
          words = line.strip().split(self.sep)
        if len(words) == 0:
          continue
        if len(words) < len(self.columns):
          logger.error("ERROR: Number of columns given in config is more than number of columns present in file {0}\n".format(self.infile))
          return False
        ts = naarad.metric.reconcile_timezones(words[0], self.timezone, self.graph_timezone)
        for i in range(len(self.columns)):
          out_csv = self.get_csv(self.columns[i])
          if out_csv in data:
            data[out_csv].append( ts + ',' + words[i+1] )
          else:
            data[out_csv] = []
            data[out_csv].append( ts + ',' + words[i+1] )
    # Post processing, putting data in csv files
    for csv in data.keys():
      self.csv_files.append(csv)
      with open(csv, 'w') as fh:
        fh.write('\n'.join(data[csv]))
    return True

  def calc(self):
    if not self.calc_metrics:
      return
    calculation_array = self.calc_metrics.split()
    for calculation in calculation_array:
      words = calculation.split('=')
      newmetric = words[0]
      expr = words[1]
      p = re.compile('(\w+)\((.+)\)')
      calc_type = p.match(expr).group(1)
      old_metric = p.match(expr).group(2)
      logger.debug('In calc() : %s %s %s %s', newmetric, expr, old_metric, calc_type)
      if not calc_type in ('rate', 'diff'):
        logger.error("ERROR: Invalid calc_metric type {0} defined in config".format(calc_type))
        continue
      old_metric_csv = self.get_csv(old_metric)
      new_metric_csv = self.get_csv(newmetric)
      self.csv_files.append(new_metric_csv)
      old_val = None
      with open(old_metric_csv, 'r') as FH:
        with open(new_metric_csv, 'w') as NEW_FH:
          for line in FH:
            w = line.split(',')
            ts = w[0]
            val = w[1]
            if not old_val:
              old_ts = ts
              old_val = val
              continue
            if calc_type == 'rate':
              #Multiply rate by 1000 since timestamp is in ms
              new_metric_val = 1000 * (float(val) - float(old_val)) / (convert_to_unixts(ts) - convert_to_unixts(old_ts))
            elif calc_type == 'diff':
              new_metric_val = (float(val) - float(old_val))
            old_ts = ts
            old_val = val
            NEW_FH.write(ts)
            NEW_FH.write(',')
            NEW_FH.write(str(new_metric_val))
            NEW_FH.write('\n')

  def graph(self, graphing_library = 'matplotlib'):
    html_string = []
    html_string.append('<h1>Metric: {0}</h1>\n'.format(self.metric_type))
    graphed = False
    if self.metric_type.startswith('GC'):
      graphing_library = 'matplotlib'
    logger.info('Using graphing_library {lib} for metric {name}'.format(lib=graphing_library, name=self.label))
    for out_csv in self.csv_files:
      csv_filename = os.path.basename(out_csv)
      # The last element is .csv, don't need that in the name of the chart
      graph_title = '.'.join(csv_filename.split('.')[0:-1])
      column = '.'.join(graph_title.split('.')[1:])
      graphed, html_ret = Metric.graphing_modules[graphing_library].graph_csv(self.outdir, out_csv, graph_title, graph_title)
      if html_ret:
        html_string.append(html_ret)
      else:
        if graphed:
          img_tag = '<h3>{title}</h3><p><b>Description</b>: {description}</p><img src={image_name}.png />\n'.format(title=graph_title, description=self.metric_description[column], image_name=graph_title)
        else:
          img_tag = '<h3>{title}</h3><p><b>Description</b>: {description}</p>No data for this metric\n'.format(title=graph_title, description=self.metric_description[column])
        html_string.append(img_tag)
    return '\n'.join(html_string)
