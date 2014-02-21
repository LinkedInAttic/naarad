# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

from naarad.graphing import matplotlib_naarad
from naarad.graphing import pygal_naarad
from naarad.metrics.android_rum_metric import AndroidRumMetric
from naarad.metrics.jmeter_metric import JmeterMetric
from naarad.metrics.procvmstat_metric import ProcVmstatMetric
from naarad.metrics.procmeminfo_metric import ProcMeminfoMetric
from naarad.metrics.proczoneinfo_metric import ProcZoneinfoMetric
from naarad.reporting.report import Report

#Custom metrics
metric_classes = {
    #'MyMetric' : MyMetricParserClass
    'JMETER' : JmeterMetric,
    'ANDROIDRUM' : AndroidRumMetric, 
    'PROCVMSTAT' : ProcVmstatMetric,
    'PROCMEMINFO' : ProcMeminfoMetric, 
    'PROCZONEINFO' : ProcZoneinfoMetric
    }

graphing_modules = {
    'matplotlib': matplotlib_naarad,
    'svg': pygal_naarad
    }

reporting_modules = {
    'report': Report
}

important_sub_metrics_import = {
    'GC': ('GCPause', 'used'),
    'ANDROIDRUM': ('launch_time', 'nus_update_time'),
    'SAR-cpuusage': ('%sys', '%usr'),
    'SAR-device': ('%util', 'await'),
    'JMETER': ('Overall_Summary.ResponseTime', 'Overall_Summary.DataThroughput', 'Overall_Summary.qps')
}

device_type_metrics = ('SAR-cpuusage', 'SAR-cpuhz', 'SAR-device', 'SAR-dev', 'SAR-edev')
