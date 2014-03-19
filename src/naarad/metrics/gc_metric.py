# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import datetime
import logging
import os
import re
import sys
import threading

from naarad.metrics.metric import Metric
import naarad.utils
from naarad.naarad_imports import important_sub_metrics_import

logger = logging.getLogger('naarad.metrics.GCMetric')

class GCMetric(Metric):
  """ Class for GC logs, deriving from class Metric """
  clock_format = '%Y-%m-%d %H:%M:%S'
  rate_types = ()
  val_types = ('alloc', 'promo', 'used0', 'used1', 'used', 'commit0', 'commit1', 'commit', 'gen0', 'gen0t', 'gen0usr', 'gen0sys', 'gen0real',
      'cmsIM', 'cmsRM', 'cmsRS', 'GCPause', 'cmsCM', 'cmsCP', 'cmsCS', 'cmsCR', 'safept', 'apptime', 'used0AfterGC', 'used1AfterGC', 'usedAfterGC')
  def __init__ (self, metric_type, infile, hostname, outdir, resource_path, label, ts_start, ts_end, rule_strings,
                **other_options):
    Metric.__init__(self, metric_type, infile, hostname, outdir, resource_path, label, ts_start, ts_end, rule_strings)
    # TODO: Make this list configurable
    self.important_sub_metrics = important_sub_metrics_import['GC']
    self.sub_metrics = self.val_types
    self.beginning_ts = None
    self.beginning_date = None
    for (key, val) in other_options.iteritems():
      if key == 'gc-options' or key == 'sub_metrics':
        self.sub_metrics = val.split()
      else:
        setattr(self, key, val)
    self.sub_metric_description = {
      'appstop' : 'approximate application stop times',
      'gen0' : 'young gen collection time, excluding gc_prologue & gc_epilogue',
      'gen0t' : 'young gen collection time, including gc_prologue & gc_epilogue',
      'gen0usr' : 'young gen collection time in cpu user secs',
      'gen0sys' : 'young gen collection time in cpu sys secs',
      'gen0real' : 'young gen collection time in elapsed secs',
      'gen1i' : 'train generation incremental collection',
      'gen1t' : 'old generation collection/full GC',
      'cmsIM' : 'CMS initial mark pause',
      'cmsRM' : 'CMS remark pause',
      'cmsRS' : 'CMS resize pause',
      'GCPause' : 'all stop-the-world GC pauses',
      'cmsCM' : 'CMS concurrent mark phase',
      'cmsCP' : 'CMS concurrent preclean phase',
      'cmsCS' : 'CMS concurrent sweep phase',
      'cmsCR' : 'CMS concurrent reset phase',
      'alloc' : 'object allocation in MB (approximate***)',
      'promo' : 'object promotion in MB (approximate***)',
      'used0' : 'young gen used memory size (before gc)',
      'used1' : 'old gen used memory size (before gc)',
      'used' : 'heap space used memory size (before gc) (excludes perm gen)',
      'commit0' : 'young gen committed memory size (after gc)',
      'commit1' : 'old gen committed memory size (after gc)',
      'commit' : 'heap committed memory size (after gc) (excludes perm gen)',
      'apptime' : 'amount of time application threads were running',
      'safept' : 'amount of time the VM spent at safepoints (app threads stopped)',
      'used0AfterGC' : 'young gen used memory size (after gc)',
      'used1AfterGC' : 'old gen used memory size (after gc)',
      'usedAfterGC' : 'heap space used memory size (after gc)'
      }


  def get_pngname(self, sub_metric):
    return self.metric_type + '.' + sub_metric + '.png'

  def get_clock_from_jvmts(self, beginning_date, beginning_ts, ts):
    if beginning_date is None:
      logger.warning('Returning ts 0 since beginning date is not set')
      return 0
    else:
      diffms = 1000*( float(ts) - beginning_ts )
      timedelta = datetime.timedelta(milliseconds=diffms)
      return beginning_date + timedelta

  def parse_val_types(self, sub_metric):
    outfile = os.path.join(self.resource_directory, self.label + '-' + sub_metric + '-out.txt')
    if not naarad.utils.is_valid_file(outfile):
      return
    outcsv = self.get_csv(sub_metric)
    with open(outcsv, 'w') as csvf:
      with open(outfile, 'r') as txt_fh:
        for line in txt_fh:
          words = line.split()
          # Implementing timestamp
          begin_ts = str( self.get_clock_from_jvmts(self.beginning_date, self.beginning_ts, words[0]) )
          if self.ts_out_of_range(begin_ts):
            continue
          begin_ts = naarad.utils.reconcile_timezones(begin_ts, self.timezone, self.graph_timezone)
          csvf.write(begin_ts + ',')
          csvf.write(words[1])
          csvf.write('\n')
    self.csv_files.append(outcsv)
    # os.remove(outfile)

  def parse(self):
    prefix = os.path.join(self.resource_directory, self.label)
    awk_cmd = os.path.join(self.bin_path, 'PrintGCStats')
    gc_metrics = set(self.val_types) & set(self.sub_metrics)
    cmd = awk_cmd + ' -v plot=' + ','.join(gc_metrics) + ' -v splitfiles=1 -v splitfileprefix=' + prefix + ' ' + self.infile
    logger.info("Parsing GC metric with cmd: %s", cmd)
    os.system(cmd)
    gc_date_regex = re.compile(r'^[0-9]{4}-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9].[0-9]+[+-][0-9]{4}:')
    with open(self.infile, 'r') as inf:
      for line in inf:
        if re.match(gc_date_regex, line) and self.beginning_date is None:
          words = line.split()
          jvmts = float(words[1].split('.')[0])
          tstamp = words[0].split('T')
          time = tstamp[1].split('.')
          clock = tstamp[0] + ' ' + time[0]
          self.beginning_date = datetime.datetime.strptime(clock, self.clock_format)
          self.beginning_ts = float(jvmts)
          logger.info('Setting beginning date and ts')
          break
    threads = []
    for gc_sub_metric in gc_metrics:
      thread = threading.Thread(target=self.parse_val_types, args=(gc_sub_metric,))
      thread.start()
      threads.append(thread)
    for t in threads:
      logger.info("Waiting for thread %d to finish.... ", t.ident)
      t.join()
    return True

