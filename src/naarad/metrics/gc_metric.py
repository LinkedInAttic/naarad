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
      'g1-pause-young.parallel.gc-worker-start.max', 'g1-pause-mixed.parallel.gc-worker-start.avg', 'g1-pause-mixed.parallel.gc-worker-start.max',
      'g1-eden-occupancy-before-gc', 'g1-eden-capacity-before-gc', 'g1-eden-occupancy-after-gc', 'g1-eden-capacity-after-gc', 'g1-survivor-before-gc',
      'g1-survivor-after-gc', 'g1-heap-occupancy-before-gc', 'g1-heap-capacity-before-gc', 'g1-heap-occupancy-after-gc', 'g1-heap-capacity-after-gc',
      'g1-young-cpu.sys', 'g1-young-cpu.usr', 'g1-young-cpu.real', 'g1-mixed-cpu.usr', 'g1-mixed-cpu.sys', 'g1-mixed-cpu.real')

  def __init__(self, metric_type, infile_list, hostname, outdir, resource_path, label, ts_start, ts_end, rule_strings,
               important_sub_metrics, anomaly_detection_metrics, **other_options):
    Metric.__init__(self, metric_type, infile_list, hostname, outdir, resource_path, label, ts_start, ts_end, rule_strings,
                    important_sub_metrics, anomaly_detection_metrics)
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
        'gen0': 'young gen collection time, excluding gc_prologue & gc_epilogue',
        'gen0t': 'young gen collection time, including gc_prologue & gc_epilogue',
        'gen0usr': 'young gen collection time in cpu user secs',
        'gen0sys': 'young gen collection time in cpu sys secs',
        'gen0real': 'young gen collection time in elapsed secs',
        'gen1i': 'train generation incremental collection',
        'gen1t': 'old generation collection or full GC',
        'cmsIM': 'CMS initial mark pause',
        'cmsRM': 'CMS remark pause',
        'cmsRS': 'CMS resize pause',
        'GCPause': 'all stop-the-world GC pauses',
        'cmsCM': 'CMS concurrent mark phase',
        'cmsCP': 'CMS concurrent preclean phase',
        'cmsCS': 'CMS concurrent sweep phase',
        'cmsCR': 'CMS concurrent reset phase',
        'alloc': 'object allocation in MB (approximate***)',
        'promo': 'object promotion in MB (approximate***)',
        'used0': 'young gen used memory size (before gc)',
        'used1': 'old gen used memory size (before gc)',
        'used': 'heap space used memory size (before gc) (excludes perm gen)',
        'commit0': 'young gen committed memory size (after gc)',
        'commit1': 'old gen committed memory size (after gc)',
        'commit': 'heap committed memory size (after gc) (excludes perm gen)',
        'apptime': 'amount of time application threads were running',
        'safept': 'amount of time the VM spent at safepoints (app threads stopped)',
        'used0AfterGC': 'young gen used memory size (after gc)',
        'used1AfterGC': 'old gen used memory size (after gc)',
        'usedAfterGC': 'heap space used memory size (after gc)',
        'g1-pause-young': 'G1 Young GC Pause (seconds)',
        'g1-pause-mixed': 'G1 Mixed GC Pause (seconds)',
        'g1-pause-remark': 'G1 Remark Pause (seconds)',
        'g1-pause-cleanup': 'G1 Cleanup Pause (seconds)',
        'g1-pause-remark.ref-proc': 'G1 Remark: Reference Processing (seconds)',
        'g1-pause-young.parallel': 'G1 Young GC Pause: Parallel Operations (ms)',
        'g1-pause-young.parallel.gcworkers': 'G1 Young GC Pause: Number of Parallel GC Workers',
        'g1-pause-young.parallel.gc-worker-start.avg': 'G1 Young GC Pause : Parallel : Avg Time spent in GC worker start (ms)',
        'g1-pause-young.parallel.gc-worker-start.max': 'G1 Young GC Pause : Parallel : Max Time spent in GC worker start (ms)',
        'g1-pause-young.parallel.ext-root-scanning.avg': 'G1 Young GC Pause: Avg Time spent in ext-root-scanning',
        'g1-pause-young.parallel.ext-root-scanning.max': 'G1 Young GC Pause: Max Time spent in ext-root-scanning',
        'g1-pause-young.parallel.update-rs.avg': 'G1 Young GC Pause: Parallel : Avg Time spent in updating Rsets',
        'g1-pause-young.parallel.update-rs.max': 'G1 Young GC Pause: Parallel : Max Time spent in updating Rsets',
        'g1-pause-young.parallel.update-rs.processed-buffers.avg': 'G1 Young GC Pause : Parallel : Update Rset : Avg number of processed buffers',
        'g1-pause-young.parallel.update-rs.processed-buffers.max': 'G1 Young GC Pause : Parallel : Update Rset : Max number of processed buffers',
        'g1-pause-young.parallel.scan-rs.avg': 'G1 Young GC Pause: Parallel : Avg Time spent in scanning Rsets',
        'g1-pause-young.parallel.scan-rs.max': 'G1 Young GC Pause: Parallel : Max Time spent in scannning Rsets',
        'g1-pause-young.parallel.object-copy-rs.avg': 'G1 Young GC Pause : Parallel : Avg Time spent in Object Copy',
        'g1-pause-young.parallel.object-copy-rs.max': 'G1 Young GC Pause : Parallel : Max Time spent in Object Copy',
        'g1-pause-young.parallel.termination.avg': 'G1 Young GC Pause : Parallel : Avg Time spent in termination',
        'g1-pause-young.parallel.termination.max': 'G1 Young GC Pause : Parallel : Max Time spent in termination',
        'g1-pause-young.parallel.gc-worker-other.avg': 'G1 Young GC Pause : Parallel : Avg Time spent in other',
        'g1-pause-young.parallel.gc-worker-other.max': 'G1 Young GC Pause : Parallel : Max Time spent in other',
        'g1-pause-young.parallel.gc-worker-total.avg': 'G1 Young GC Pause : Parallel : Avg Total time for GC worker',
        'g1-pause-young.parallel.gc-worker-total.max': 'G1 Young GC Pause : Parallel : Max Total time for GC worker',
        'g1-pause-young.parallel.gc-worker-end.avg': 'G1 Young GC Pause : Parallel : Avg Time for GC worker end',
        'g1-pause-young.parallel.gc-worker-end.max': 'G1 Young GC Pause : Parallel : Max Time for GC worker end',
        'g1-pause-young.code-root-fixup': 'G1 Young GC Pause : Time spent in code root fixup (ms)',
        'g1-pause-young.clear-ct': 'G1 Young GC Pause: Time spent in clear ct (ms)',
        'g1-pause-young.other': 'G1 Young GC Pause: Time spent in other (ms)',
        'g1-pause-young.other.choose-cset': 'G1 Young GC Pause : Other : Time spent in choosing CSet (ms)',
        'g1-pause-young.other.ref-proc': 'G1 Young GC Pause : Other : Time spent in reference processing (ms)',
        'g1-pause-young.other.reg-enq': 'G1 Young GC Pause : Other : Time spent in reg-enq(ms)',
        'g1-pause-young.other.free-cset': 'G1 Young GC Pause : Other : Time spent in processing free Cset(ms)',
        'g1-pause-mixed.parallel': 'G1 Mixed GC Pause: Parallel Operations (ms)',
        'g1-pause-mixed.parallel.gcworkers': 'G1 Mixed GC Pause: Number of Parallel GC Workers',
        'g1-pause-mixed.parallel.gc-worker-start.avg': 'G1 Mixed GC Pause : Parallel : Avg Time spent in GC worker start (ms)',
        'g1-pause-mixed.parallel.gc-worker-start.max': 'G1 Mixed GC Pause : Parallel : Max Time spent in GC worker start (ms)',
        'g1-pause-mixed.parallel.ext-root-scanning.avg': 'G1 Mixed GC Pause: Avg Time spent in ext-root-scanning',
        'g1-pause-mixed.parallel.ext-root-scanning.max': 'G1 Mixed GC Pause: Max Time spent in ext-root-scanning',
        'g1-pause-mixed.parallel.update-rs.avg': 'G1 Mixed GC Pause: Parallel : Avg Time spent in updating Rsets',
        'g1-pause-mixed.parallel.update-rs.max': 'G1 Mixed GC Pause: Parallel : Max Time spent in updating Rsets',
        'g1-pause-mixed.parallel.update-rs.processed-buffers.avg': 'G1 Mixed GC Pause : Parallel : Update Rset : Avg number of processed buffers',
        'g1-pause-mixed.parallel.update-rs.processed-buffers.max': 'G1 Mixed GC Pause : Parallel : Update Rset : Max number of processed buffers',
        'g1-pause-mixed.parallel.scan-rs.avg': 'G1 Mixed GC Pause: Parallel : Avg Time spent in scanning Rsets',
        'g1-pause-mixed.parallel.scan-rs.max': 'G1 Mixed GC Pause: Parallel : Max Time spent in scannning Rsets',
        'g1-pause-mixed.parallel.object-copy-rs.avg': 'G1 Mixed GC Pause : Parallel : Avg Time spent in Object Copy',
        'g1-pause-mixed.parallel.object-copy-rs.max': 'G1 Mixed GC Pause : Parallel : Max Time spent in Object Copy',
        'g1-pause-mixed.parallel.termination.avg': 'G1 Mixed GC Pause : Parallel : Avg Time spent in termination',
        'g1-pause-mixed.parallel.termination.max': 'G1 Mixed GC Pause : Parallel : Max Time spent in termination',
        'g1-pause-mixed.parallel.gc-worker-other.avg': 'G1 Mixed GC Pause : Parallel : Avg Time spent in other',
        'g1-pause-mixed.parallel.gc-worker-other.max': 'G1 Mixed GC Pause : Parallel : Max Time spent in other',
        'g1-pause-mixed.parallel.gc-worker-total.avg': 'G1 Mixed GC Pause : Parallel : Avg Total time for GC worker',
        'g1-pause-mixed.parallel.gc-worker-total.max': 'G1 Mixed GC Pause : Parallel : Max Total time for GC worker',
        'g1-pause-mixed.parallel.gc-worker-end.avg': 'G1 Mixed GC Pause : Parallel : Avg Time for GC worker end',
        'g1-pause-mixed.parallel.gc-worker-end.max': 'G1 Mixed GC Pause : Parallel : Max Time for GC worker end',
        'g1-pause-mixed.code-root-fixup': 'G1 Mixed GC Pause : Time spent in code root fixup (ms)',
        'g1-pause-mixed.clear-ct': 'G1 Mixed GC Pause: Time spent in clear ct (ms)',
        'g1-pause-mixed.other': 'G1 Mixed GC Pause: Time spent in other (ms)',
        'g1-pause-mixed.other.choose-cset': 'G1 Mixed GC Pause : Other : Time spent in choosing CSet (ms)',
        'g1-pause-mixed.other.ref-proc': 'G1 Mixed GC Pause : Other : Time spent in reference processing (ms)',
        'g1-pause-mixed.other.reg-enq': 'G1 Mixed GC Pause : Other : Time spent in reg-enq(ms)',
        'g1-pause-mixed.other.free-cset': 'G1 Mixed GC Pause : Other : Time spent in processing free Cset(ms)',
        'g1-eden-occupancy-before-gc': 'G1 Eden Occupancy (MB) (Before GC)',
        'g1-eden-capacity-before-gc': 'G1 Eden Capacity (MB) (Before GC)',
        'g1-eden-occupancy-after-gc': 'G1 Eden Occupancy (MB) (After GC)',
        'g1-eden-capacity-after-gc': 'G1 Eden Capacity (MB) (After GC)',
        'g1-survivor-before-gc': 'G1 Survivor Size (MB) (Before GC)',
        'g1-survivor-after-gc': 'G1 Survivor Size (MB) (After GC)',
        'g1-heap-occupancy-before-gc': 'G1 Heap Occupancy (MB) (Before GC)',
        'g1-heap-capacity-before-gc': 'G1 Heap Capacity (MB) (Before GC)',
        'g1-heap-occupancy-after-gc': 'G1 Heap Occupancy (MB) (After GC)',
        'g1-heap-capacity-after-gc': 'G1 Heap Capacity (MB) (After GC)',
        'g1-young-cpu.sys': 'G1 Young GC : sys cpu time (seconds)',
        'g1-young-cpu.usr': 'G1 Young GC : usr cpu time (seconds)',
        'g1-young-cpu.real': 'G1 Young GC : elapsed time (seconds)',
        'g1-mixed-cpu.usr': 'G1 Mixed GC : usr cpu time (seconds)',
        'g1-mixed-cpu.sys': 'G1 Mixed GC : sys cpu time (seconds)',
        'g1-mixed-cpu.real': 'G1 Mixed GC : elapsed time (seconds)'
    }

  def parse(self):
    prefix = os.path.join(self.resource_directory, self.label)
    awk_cmd = os.path.join(self.bin_path, 'PrintGCStats')
    gc_metrics = set(self.val_types) & set(self.sub_metrics)
    if self.ts_start:
      awk_cmd += ' -v ts_start="' + naarad.utils.get_standardized_timestamp(self.ts_start, None) + '"'
    if self.ts_end:
      awk_cmd += ' -v ts_end="' + naarad.utils.get_standardized_timestamp(self.ts_end, None) + '"'
    cmd = "{0} -v plot={1} -v splitfiles=1 -v datestamps=1 -v plotcolumns=2 -v splitfileprefix={2} {3}".format(awk_cmd, ','.join(gc_metrics), prefix,
                                                                                                               ' '.join(self.infile_list))
    logger.info("Parsing GC metric with cmd: %s", cmd)
    os.system(cmd)
    for gc_sub_metric in gc_metrics:
      outcsv = self.get_csv(gc_sub_metric)
      if naarad.utils.is_valid_file(outcsv):
        self.csv_files.append(outcsv)
    return True
