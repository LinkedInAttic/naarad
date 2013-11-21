# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import logging
import os
import glob
import re
import naarad.utils
from jinja2 import Template, Environment, PackageLoader, FileSystemLoader
from collections import defaultdict


logger = logging.getLogger('naarad.reporting.Report')

class Report(object):

  def __init__(self, report_name, output_directory, metric_list,  **other_options):
    self.report_templates = {
      'header': 'default_report_header.html',
      'summary': 'default_summary_page.html',
      'metric': 'default_metric_page.html',
      'footer': 'default_report_footer.html'
    }
    if report_name == '':
      self.report_name = 'naarad analysis report'
    else:
      self.report_name = report_name
    self.output_directory = output_directory
    self.metric_list = metric_list
    if other_options:
      for (key, val) in other_options.iteritems():
        setattr(self, key, val)

  def get_summary_table(self, summary_stats_file):
    summary_stats = []
    with open(summary_stats_file,'r') as stats_file:
      header = stats_file.readline().rstrip().rsplit(',')
      summary_stats.append(header)
      for line in stats_file:
        summary_stats.append(line.rstrip().rsplit(','))
    return summary_stats

  def is_correlated_image(self, image, metric):
    # regex is based on the naming convention in naarad.utils.get_merged_png_name
    if re.match(r'.*/' + metric + '.[^/]+-' + metric + '..*', image):
      return True
    else:
      return False

  def discover_metric_data(self, output_directory, metric):
    single_images = []
    correlated_images = []
    summary_stats = ''
    important_stats = ''
    if naarad.utils.is_valid_file(os.path.join(output_directory, metric + '.stats.csv')):
      summary_stats = os.path.join(output_directory, metric + '.stats.csv')
    if naarad.utils.is_valid_file(os.path.join(output_directory, metric + '.important_sub_metrics.csv')):
      important_stats = os.path.join(output_directory, metric + '.important_sub_metrics.csv')
    image_list = glob.glob(os.path.join(output_directory, metric + '.*.png'))
    for image in image_list:
      if naarad.utils.is_valid_file(image):
        if self.is_correlated_image(image, metric):
          correlated_images.append(os.path.basename(image))
        else:
          single_images.append(os.path.basename(image))
    return summary_stats, important_stats, single_images, correlated_images

  def generate(self):
    template_loader = FileSystemLoader(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'templates')))
    template_environment = Environment(loader=template_loader)
    for metric in self.metric_list:
      metric_stats_file, summary_stats, metric_plots, correlated_plots = self.discover_metric_data(self.output_directory, metric)
      metric_stats = self.get_summary_table(metric_stats_file)
      metric_html = template_environment.get_template(self.report_templates['header']).render(custom_javascript_includes=["http://www.kryogenix.org/code/browser/sorttable/sorttable.js"])
      metric_html += template_environment.get_template(self.report_templates['metric']).render(metric_stats=metric_stats, metric_plots=metric_plots, correlated_plots=correlated_plots, metric=metric)
      metric_html += template_environment.get_template(self.report_templates['footer']).render()
      with open(os.path.join(self.output_directory, metric + '_report.html'),'w') as metric_report:
        metric_report.write(metric_html)
