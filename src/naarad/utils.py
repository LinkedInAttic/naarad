# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

# zen change

import calendar
from collections import defaultdict
import datetime
import logging
import os
import pytz
from pytz import timezone
import re
import sys
import threading
import time
import urllib

logger = logging.getLogger('naarad.utils')

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

