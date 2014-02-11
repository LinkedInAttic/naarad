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
    for (key, val) in other_options.iteritems():
      if key == 'gc-options':
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

  def parse_val_types(self, sub_metric, no_age_file):
    outfile = os.path.join(self.resource_directory, self.metric_type + '-' + sub_metric + '-out.txt')
    awk_cmd = os.path.join(self.bin_path, 'PrintGCStats')
    cmd = awk_cmd + ' -v plot=' + sub_metric + ' -v interval=1 ' + no_age_file + ' > ' +  outfile
    thread_id = threading.current_thread().ident
    logger.info("Thread # %d - Parsing a GC metric with cmd: %s", thread_id, cmd)
    os.system(cmd)
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

  def parse(self):
    # check if outdir exists, if not, create it
    if not os.path.isdir(self.outdir):
      os.makedirs(self.outdir)
    if not os.path.isdir(self.resource_directory):
      os.makedirs(self.resource_directory)

    no_age_file = os.path.join(self.resource_directory, self.label + '-noage')
    app_stop_file = self.get_csv('appstop')

    stop = {}
    ts = None

    gc_date_regex = re.compile(r'^[0-9]{4}-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9].[0-9]+[+-][0-9]{4}:')

    no_age_fh = open(no_age_file, 'w')
    with open(self.infile, 'r') as inf:
      for line in inf:
        if re.match(gc_date_regex, line) and self.beginning_date is None:
          #2012-02-23T21:29:35.894-0800: 17.070: [GC 17.086: [ParNew
          # TODO : Use regex and groups to do this parsing instead of splits
          words = line.split()
          jvmts = float(words[1].split('.')[0])
          tstamp = words[0].split('T')
          time = tstamp[1].split('.')
          clock = tstamp[0] + ' ' + time[0]

          self.beginning_date = datetime.datetime.strptime(clock, self.clock_format)
          self.beginning_ts = float(jvmts)
          logger.info('Setting beginning date and ts')

        if 'Desired' not in line and 'age' not in line:
          if 'ParNew' in line:
            no_new_line = line.rstrip('\n')
            no_age_fh.write(no_new_line)
          else:
            no_age_fh.write(line)
        # capture stop time stats
        if re.match(gc_date_regex, line) or 'stopped' in line:
          words = line.split()
          if 'stopped' in line:
            if ts:
              if not ts in stop:
                stop[ts] = float(words[-2])
              else:
                stop[ts] += float(words[-2])
          else:
            try:
              ts = float(words[1].rstrip(':'))
            except:
              logger.warn("Unexpected error: %s", sys.exc_info()[0])
              logger.warn("at line: %s", line)
            else:
              if not ts in stop:
                stop[ts] = 0
    no_age_fh.close()

    # Writing stop time stats
    with open(app_stop_file, 'w') as appstopf:
      for ts in sorted(stop.iterkeys()):
        # Implementing timestamp support
        begin_ts = str( self.get_clock_from_jvmts(self.beginning_date, self.beginning_ts, ts) )
        if self.ts_out_of_range(begin_ts):
          continue
        appstopf.write( begin_ts + ',' + str(stop[ts]) )
        appstopf.write( '\n' )

    self.csv_files.append(app_stop_file)

    with open(no_age_file, 'r') as no_age_fh:
      threads = []
      for x in self.val_types:
        if not x in self.sub_metrics:
          continue
        thread = threading.Thread(target=self.parse_val_types, args=(x, no_age_file))
        thread.start()
        threads.append(thread)
      for t in threads:
        logger.info("Waiting for thread %d to finish.... ", t.ident)
        t.join()
    return True

