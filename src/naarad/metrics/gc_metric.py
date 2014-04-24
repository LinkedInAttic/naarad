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
from naarad.naarad_constants import important_sub_metrics_import

logger = logging.getLogger('naarad.metrics.GCMetric')


class GCMetric(Metric):
  """ Class for GC logs, deriving from class Metric """
  clock_format = '%Y-%m-%d %H:%M:%S'
  rate_types = ()
  val_types = ('alloc', 'promo', 'used0', 'used1', 'used', 'commit0', 'commit1', 'commit', 'gen0', 'gen0t', 'gen0usr', 'gen0sys', 'gen0real',
      'cmsIM', 'cmsRM', 'cmsRS', 'GCPause', 'cmsCM', 'cmsCP', 'cmsCS', 'cmsCR', 'safept', 'apptime', 'used0AfterGC', 'used1AfterGC', 'usedAfterGC', 
      'gen1t', 'g1-pause-young', 'g1-pause-mixed', 'g1-pause-remark', 'g1-pause-cleanup', 'g1-pause-remark.ref-proc', 'g1-pause-young.parallel',
      'g1-pause-young.parallel.gcworkers', 'g1-pause-young.parallel.ext-root-scanning.avg', 'g1-pause-young.parallel.ext-root-scanning.max', 
      'g1-pause-young.parallel.update-rs.avg', 'g1-pause-young.parallel.update-rs.max', 'g1-pause-young.parallel.update-rs.processed-buffers.avg', 
      'g1-pause-young.parallel.update-rs.processed-buffers.max', 'g1-pause-young.parallel.scan-rs.avg', 'g1-pause-young.parallel.scan-rs.max', 
      'g1-pause-young.parallel.object-copy-rs.avg', 'g1-pause-young.parallel.object-copy-rs.max', 'g1-pause-young.parallel.termination.avg', 
      'g1-pause-young.parallel.termination.max', 'g1-pause-young.parallel.gc-worker-other.avg', 'g1-pause-young.parallel.gc-worker-other.max', 
      'g1-pause-young.parallel.gc-worker-total.avg', 'g1-pause-young.parallel.gc-worker-total.max', 'g1-pause-young.parallel.gc-worker-end.avg', 
      'g1-pause-young.parallel.gc-worker-end.max', 'g1-pause-young.code-root-fixup', 'g1-pause-young.clear-ct', 'g1-pause-young.other', 
      'g1-pause-young.other.choose-cset', 'g1-pause-young.other.ref-proc', 'g1-pause-young.other.reg-enq', 'g1-pause-young.other.free-cset', 
      'g1-pause-mixed.parallel', 'g1-pause-mixed.parallel.gcworkers', 'g1-pause-mixed.parallel.ext-root-scanning.avg', 
      'g1-pause-mixed.parallel.ext-root-scanning.max', 'g1-pause-mixed.parallel.update-rs.avg', 'g1-pause-mixed.parallel.update-rs.max', 
      'g1-pause-mixed.parallel.update-rs.processed-buffers.avg', 'g1-pause-mixed.parallel.update-rs.processed-buffers.max', 
      'g1-pause-mixed.parallel.scan-rs.avg', 'g1-pause-mixed.parallel.scan-rs.max', 'g1-pause-mixed.parallel.object-copy-rs.avg', 
      'g1-pause-mixed.parallel.object-copy-rs.max', 'g1-pause-mixed.parallel.termination.avg', 'g1-pause-mixed.parallel.termination.max', 
      'g1-pause-mixed.parallel.gc-worker-other.avg', 'g1-pause-mixed.parallel.gc-worker-other.max', 'g1-pause-mixed.parallel.gc-worker-total.avg', 
      'g1-pause-mixed.parallel.gc-worker-total.max', 'g1-pause-mixed.parallel.gc-worker-end.avg', 'g1-pause-mixed.parallel.gc-worker-end.max', 
      'g1-pause-mixed.code-root-fixup', 'g1-pause-mixed.clear-ct', 'g1-pause-mixed.other', 'g1-pause-mixed.other.choose-cset', 
      'g1-pause-mixed.other.ref-proc', 'g1-pause-mixed.other.reg-enq', 'g1-pause-mixed.other.free-cset', 'g1-pause-young.parallel.gc-worker-start.avg', 
      'g1-pause-young.parallel.gc-worker-start.max', 'g1-pause-mixed.parallel.gc-worker-start.avg', 'g1-pause-mixed.parallel.gc-worker-start.max')

  def __init__ (self, metric_type, infile_list, hostname, outdir, resource_path, label, ts_start, ts_end, rule_strings,
                important_sub_metrics, **other_options):
    Metric.__init__(self, metric_type, infile_list, hostname, outdir, resource_path, label, ts_start, ts_end, rule_strings,
                    important_sub_metrics)
    if not self.important_sub_metrics:
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

  def parse(self):
    prefix = os.path.join(self.resource_directory, self.label)
    awk_cmd = os.path.join(self.bin_path, 'PrintGCStats')
    gc_metrics = set(self.val_types) & set(self.sub_metrics)
    if self.ts_start:
      awk_cmd += ' -v ts_start="' + naarad.utils.get_standardized_timestamp(self.ts_start, None) + '"'
    if self.ts_end:
      awk_cmd += ' -v ts_end="' + naarad.utils.get_standardized_timestamp(self.ts_end, None) + '"'
    cmd = awk_cmd + ' -v plot=' + ','.join(gc_metrics) + ' -v splitfiles=1 -v datestamps=1 -v plotcolumns=2 -v splitfileprefix=' + prefix + ' ' + ' '.join(self.infile_list)
    logger.info("Parsing GC metric with cmd: %s", cmd)
    os.system(cmd)
    for gc_sub_metric in gc_metrics:
      outcsv = self.get_csv(gc_sub_metric)
      if naarad.utils.is_valid_file(outcsv):
        self.csv_files.append(outcsv)
    return True
