from nose.tools import *

import linkedin.neelix.metric as neelix
import linkedin.neelix.gc_metric as gc_metric

import datetime
import filecmp

#def test_get_clock_from_jvmts():
#  clock_format = '%Y-%m-%d %H:%M:%S'
#  begin_date = datetime.datetime.strptime('2012-02-23 21:29:35', clock_format)
#  begin_jvmts = 17.070 - 0.894
#  assert_equal( (str(gc_metric.get_clock_from_jvmts(begin_date, begin_jvmts, 6113.643))).split('.')[0], '2012-02-23 23:11:12')

def test_sanitize_string():
  str = "m/s or miles/hr"
  rightstr = "m-per-s or miles-per-hr"
  newstr = neelix.sanitize_string(str)
  assert_equal( newstr, rightstr)

def test_convert_to_24hr_1():
  ts = "8:00 PM"
  rightts = "20:00"
  newts = neelix.convert_to_24hr_format(ts)
  assert_equal(newts, rightts)

def test_convert_to_24hr_2():
  ts = "12:30 AM"
  rightts = "00:30"
  newts = neelix.convert_to_24hr_format(ts)
  assert_equal(newts, rightts)

#def test_nway_file_merge():
#  filelist = ["data/SAR-cpuusage.all.%sys.csv", "data/GC.alloc.csv"]
#  outfile = "/tmp/neelix-mergedfile.csv"
#  rightoutfile = "data/SAR-cpuusage.all.%sys-GC.alloc.csv"
#  filler='-999'
#  neelix.tscsv_nway_file_merge(outfile, filelist, filler)
#  assert_equal(filecmp.cmp(outfile, rightoutfile), True)
