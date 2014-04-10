# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
# Metric Constants
DEFAULT_SUMMARY_STATS = ['mean', 'std', 'p50', 'p75', 'p90', 'p95', 'p99', 'min', 'max']
OK = 0
SLA_FAILED = 1
COLLECT_FAILED = 2
PARSE_FAILED = 3
GRAPH_FAILED = 4
REPORT_FAILED = 5

# Report Constants
DEFAULT_REPORT_TITLE = 'naarad analysis report'
STYLESHEET_INCLUDES = ['bootstrap.min.css', 'inversion.css']
JAVASCRIPT_INCLUDES = ['jquery-1.7.1.min.js', 'dygraph-combined.js', 'bootstrap.js', 'sorttable.js', 'naarad.js']
PLOTS_CSV_LIST_FILE = 'list.txt'
CDF_PLOTS_CSV_LIST_FILE = 'cdf_list.txt'
STATS_CSV_LIST_FILE = 'stats.txt'
SUMMARY_REPORT_FILE = 'summary_report.html'
CLIENT_CHARTING_FILE = 'report.html'
DIFF_REPORT_FILE = 'diff_report.html'
METRIC_REPORT_SUFFIX = '_report.html'
TEMPLATE_HEADER = 'default_report_header.html'
TEMPLATE_FOOTER = 'default_report_footer.html'
TEMPLATE_SUMMARY_CONTENT = 'default_summary_content.html'
TEMPLATE_SUMMARY_PAGE = 'default_summary_page.html'
TEMPLATE_METRIC_PAGE = 'default_metric_page.html'
TEMPLATE_CLIENT_CHARTING = 'default_client_charting_page.html'
TEMPLATE_DIFF_CLIENT_CHARTING = 'default_diff_client_charting_page.html'
TEMPLATE_DIFF_PAGE = 'default_diff_page.html'
SUBMETRIC_HEADER = 'sub_metric'

# Matplotlib Constants
COLOR_PALETTE = ['black', 'steelblue', 'm', 'red', 'cyan', 'g', 'orange', 'gray']
SUBPLOT_BOTTOM_OFFSET = 0.1
SUBPLOT_LEFT_OFFSET = 0.05
SUBPLOT_RIGHT_OFFSET = 0.95
SUBPLOT_TOP_OFFSET = 0
X_TICKS_FONTSIZE = 8
X_TICKS_DATEFORMAT = '%H:%M:%S'
Y_AXIS_OFFSET = 0.06
Y_LABEL_FONTSIZE = 10
Y_TICKS_FONTSIZE = 8
ZOOM_FACTOR = 0

# LinkedIn_Android_RUM Constants
LIA_TIMING_NAME = 'timingName'
LIA_TIMING_VALUE = 'timingValue'
LIA_START = 'start'
LIA_APP_ON_CREATE = 'linkedin_android_app_oncreate_time'
LIA_LAUNCH_ACTIVITY = 'linkedin_android_app_launch_activity_time'
LIA_NUS_ON_CREATE = 'linkedin_android_app_nus_oncreate_time'
LIA_NUS_UPDATE = 'linkedin_android_nus_update_time'
LIA_LONG = 'long'
LIA_NATIVE_TIMINGS = 'nativeTimings'
LIA_ARRAY = 'array'

# Narrad Exit Code
SLA_FAILURE = 1

# RUN STEPS constants
PRE_ANALYSIS_RUN = 'pre'
DURING_ANALYSIS_RUN = 'in'
POST_ANALYSIS_RUN = 'post'
RUN_TYPE_WORKLOAD = 'workload'
SECONDS_TO_KILL_AFTER_SIGTERM = 5
