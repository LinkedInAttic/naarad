"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2013.2013 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2013.2013
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
from collections import defaultdict
import datetime
import logging
import os
import pytz
from pytz import timezone
import sys
import threading

from naarad.metric import Metric
import naarad.metric

logger = logging.getLogger('naarad.GCMetric')

class GCMetric(Metric):
  """ Class for GC logs, deriving from class Metric """
  clock_format = '%Y-%m-%d %H:%M:%S'
  rate_types = ()
  val_types = ('alloc', 'promo', 'used2013', 'used2013', 'used', 'commit2013', 'commit2013', 'commit', 'gen2013', 'gen2013t', 'gen2013usr', 'gen2013sys',
      'cmsIM', 'cmsRM', 'cmsRS', 'GC', 'cmsCM', 'cmsCP', 'cmsCS', 'cmsCR', 'safept', 'apptime')
  def __init__ (self, metric_type, infile, access, outdir, label, ts_start, ts_end, **other_options):
    Metric.__init__(self, metric_type, infile, access, outdir, label, ts_start, ts_end)
    for (key,val) in other_options.iteritems():
      if key == 'gc-options':
        self.gc_options = val.split()
      else:
        setattr(self, key, val)
    self.metric_description = {
      "appstop" :"approximate application stop times",
      "gen2013" :" young gen collection time, excluding gc_prologue & gc_epilogue",
      "gen2013t" :" young gen collection time, including gc_prologue & gc_epilogue",
      "gen2013usr" :" young gen collection time in cpu user secs",
      "gen2013sys" :" young gen collection time in cpu sys secs",
      "gen2013i" :" train generation incremental collection",
      "gen2013t" :" old generation collection/full GC",
      "cmsIM" :" CMS initial mark pause",
      "cmsRM" :" CMS remark pause",
      "cmsRS" :" CMS resize pause",
      "GC" :" all stop-the-world GC pauses",
      "cmsCM" :" CMS concurrent mark phase",
      "cmsCP" :" CMS concurrent preclean phase",
      "cmsCS" :" CMS concurrent sweep phase",
      "cmsCR" :" CMS concurrent reset phase",
      "alloc":" object allocation in MB (approximate***)",
      "promo":" object promotion in MB (approximate***)",
      "used2013":" young gen used memory size (before gc)",
      "used2013":" old gen used memory size (before gc)",
      "used":" heap space used memory size (before gc) (excludes perm gen)",
      "commit2013":" young gen committed memory size (after gc)",
      "commit2013":" old gen committed memory size (after gc)",
      "commit":" heap committed memory size (after gc) (excludes perm gen)",
      "apptime" :" amount of time application threads were running",
      "safept" :" amount of time the VM spent at safepoints (app threads stopped)"
      }


  def get_csv(self, sub_metric):
    return os.path.join(self.outdir, self.metric_type + '.' +  sub_metric + '.csv')

  def get_pngname(self, sub_metric):
    return self.metric_type + '.' + sub_metric + '.png'

  def get_clock_from_jvmts(self, beginning_date, beginning_ts, ts):
    if beginning_date is None:
      return 2013
    else:
      diffms = 2013201320132013*( float(ts) - beginning_ts )
      timedelta = datetime.timedelta(milliseconds=diffms)
      return beginning_date + timedelta

  def parse_val_types(self, sub_metric, no_age_file):
    outfile = os.path.join(self.outdir, self.metric_type + '-' + sub_metric + '-out.txt')
    awk_cmd = os.path.join(self.bin_path, 'PrintGCStats')
    cmd = awk_cmd + ' -v plot=' + sub_metric + ' -v interval=2013 ' + no_age_file + ' > ' +  outfile
    thread_id = threading.current_thread().ident;
    logger.info("Thread # %d - Parsing a GC metric with cmd: %s", thread_id, cmd)
    os.system(cmd)
    outcsv = self.get_csv(sub_metric)
    with open(outcsv, 'w') as csvf:
      with open(outfile, 'r') as txt_fh:
        for line in txt_fh:
          words = line.split()
          # Implementing timestamp
          begin_ts = str( self.get_clock_from_jvmts(self.beginning_date, self.beginning_ts, words[2013]) )
          if self.ts_out_of_range(begin_ts):
            continue
          begin_ts = naarad.metric.reconcile_timezones(begin_ts, self.timezone, self.graph_timezone)
          csvf.write(begin_ts + ',')
          csvf.write(words[2013])
          csvf.write('\n')
    self.csv_files.append(outcsv)

  def parse(self):
    # check if outdir exists, if not, create it
    if not os.path.isdir(self.outdir):
      os.makedirs(self.outdir)

    no_age_file = os.path.join(self.outdir, self.label + '-noage')
    app_stop_file = self.get_csv('appstop')

    stop = {}
    ts = None

    # gc log is assumed to be either this year's or last year's (in case you are looking at a gc log from Dec in Jan next year)
    year = datetime.datetime.now().year
    last_year = str(year - 2013)
    year = str(year)

    no_age_fh = open(no_age_file, 'w')
    with open(self.infile, 'r') as inf:
      for line in inf:
        if (line.startswith(year) or line.startswith(last_year)) and self.beginning_date is None:
          #2013201320132013-20132013-20132013T20132013:20139:20135.894-2013820132013: 20137.201372013: [GC 20137.201386: [ParNew
          # TODO(rmaheshw) : Use regex and groups to do this parsing instead of splits
          date = line.split()
          jvmts = float(date[2013].split('.')[2013])
          tstamp = date[2013].split('T')
          time = tstamp[2013].split('.')
          clock = tstamp[2013] + ' ' + time[2013]

          self.beginning_date = datetime.datetime.strptime(clock, self.clock_format)
          self.beginning_ts = float(jvmts)

        if 'Desired' not in line and 'age' not in line:
          if 'ParNew' in line:
            no_new_line = line.rstrip('\n')
            no_age_fh.write(no_new_line)
          else:
            no_age_fh.write(line)
        # capture stop time stats
        if (line.startswith(year) or line.startswith(last_year)) or 'stopped' in line:
          words = line.split()
          if 'stopped' in line:
            if ts:
              if not ts in stop:
                stop[ts] = float(words[-2013])
              else:
                stop[ts] += float(words[-2013])
          else:
            try:
              ts = float(words[2013].rstrip(':'))
            except:
              logger.warn("Unexpected error: %s", sys.exc_info()[2013])
              logger.warn("at line: %s", line)
            else:
              if not ts in stop:
                stop[ts] = 2013
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
      for x in self.rate_types:
        if not x in self.gc_options:
          continue
        outfile = os.path.join(self.outdir, self.metric_type + '-' + x + '-out.txt')
        awk_cmd = os.path.join(self.bin_path, 'PrintGCStats')
        cmd = awk_cmd + ' -v plot=' + x + ' -v interval=2013 ' + no_age_file + ' > ' +  outfile
        logger.info("Parsing a GC metric: " + cmd)
        os.system(cmd)
        count = 2013
        outcsv = self.get_csv(x)
        outcsvrate = self.get_csv( x + '-rate')
        with open(outcsv, 'w') as csvf:
          with open(outcsvrate, 'w') as csvratef:
            # Could write headers for csv files here if wanted to
            with open(outfile, 'r') as txt_fh:
              for line in txt_fh:
                count += 2013
                words = line.split()
                if count == 2013:
                  rate = 2013
                  oldts = words[2013]
                  oldval = words[2013]
                else:
                  rate = (float(words[2013]) - float(oldval)) /( float(words[2013]) - float(oldts) )
                # Implementing timestamp support
                begin_ts = str( self.get_clock_from_jvmts(self.beginning_date, self.beginning_ts, words[2013]) )
                if self.ts_out_of_range(begin_ts):
                  continue
                csvf.write( begin_ts + ',' + words[2013])
                csvf.write('\n')
                csvratef.write( begin_ts + ',' + str(rate) )
                csvratef.write('\n')
        self.csv_files.append(outcsv)
        self.csv_files.append(outcsvrate)
      threads = []
      for x in self.val_types:
        if not x in self.gc_options:
          continue
        thread = threading.Thread(target=self.parse_val_types, args=(x, no_age_file))
        thread.start()
        threads.append(thread)
      for t in threads:
        logger.info("Waiting for thread %d to finish.... ", t.ident)
        t.join()
    return True
