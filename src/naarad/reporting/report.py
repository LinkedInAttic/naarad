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

  def __init__(self, report_name, output_directory, metric_list, correlated_plots,  **other_options):
    self.report_templates = {
      'header': 'default_report_header.html',
      'summary': 'default_summary_page.html',
      'summary_content': 'summary_content.html',
      'metric': 'default_metric_page.html',
      'footer': 'default_report_footer.html'
    }
    if report_name == '':
      self.report_name = 'naarad analysis report'
    else:
      self.report_name = report_name
    self.output_directory = output_directory
    self.metric_list = metric_list
    self.correlated_plots = correlated_plots
    self.stylesheet_includes = ['http://yui.yahooapis.com/pure/0.3.0/pure-min.css', 'http://purecss.io/css/layouts/side-menu.css']
    self.javascript_includes = ['http://www.kryogenix.org/code/browser/sorttable/sorttable.js','http://purecss.io/js/ui.js', 'http://dygraphs.com/dygraph-combined.js']
    if other_options:
      for (key, val) in other_options.iteritems():
        setattr(self, key, val)
      if 'header_template' in other_options:
        self.report_templates['header'] = self.header_template
      if 'footer_template' in other_options:
        self.report_templates['footer'] = self.footer_template
      if 'metric_template' in other_options:
        self.report_templates['metric'] = self.metric_template
      if 'summary_template' in other_options:
        self.report_templates['summary'] = self.summary_template
      if 'summary_content_template' in other_options:
        self.report_templates['summary_content'] = self.summary_template

  def get_summary_table(self, summary_stats_file):
    summary_stats = []
    with open(summary_stats_file,'r') as stats_file:
      header = stats_file.readline().rstrip().rsplit(',')
      summary_stats.append(header)
      for line in stats_file:
        summary_stats.append(line.rstrip().rsplit(','))
    return summary_stats

  def is_correlated_image(self, image):
    if os.path.basename(image) in self.correlated_plots:
      return True
    else:
      return False

  def enable_summary_tab(self, output_directory):
    important_sub_metrics_list = glob.glob(os.path.join(output_directory, '*.important_sub_metrics.csv'))
    if len(important_sub_metrics_list) == 0:
      if len(self.correlated_plots) > 0:
        return True
      else:
        return False
    else:
      for metric_file in important_sub_metrics_list:
        if naarad.utils.is_valid_file(metric_file):
          return True
    return False

  def discover_metric_data(self, output_directory, metric):
    single_images = []
    correlated_images = []
    single_svgs = []
    correlated_svgs = []
    single_dygraphs = []
    correlated_dygraphs = []

    summary_stats = ''
    important_stats = ''
    if naarad.utils.is_valid_file(os.path.join(output_directory, metric + '.stats.csv')):
      summary_stats = os.path.join(output_directory, metric + '.stats.csv')
    if naarad.utils.is_valid_file(os.path.join(output_directory, metric + '.important_sub_metrics.csv')):
      important_stats = os.path.join(output_directory, metric + '.important_sub_metrics.csv')
    image_list = glob.glob(os.path.join(output_directory, metric + '.*.png'))
    for image in image_list:
      if naarad.utils.is_valid_file(image):
        if self.is_correlated_image(image):
          correlated_images.append(os.path.basename(image))
        else:
          single_images.append(os.path.basename(image))
    svg_list = glob.glob(os.path.join(output_directory, metric + '.*.svg'))
    for svg in svg_list:
      if naarad.utils.is_valid_file(svg):
        if self.is_correlated_image(svg):
          correlated_svgs.append(svg)
        else:
          single_svgs.append(svg)
    dygraph_list = glob.glob(os.path.join(output_directory, metric + '.*.dyg'))
    for dyg in dygraph_list:
      if naarad.utils.is_valid_file(dyg):
        if self.is_correlated_image(dyg):
          correlated_dygraphs.append(dyg)
        else:
          single_dygraphs.append(dyg)
    return summary_stats, important_stats, single_images, correlated_images, single_dygraphs, correlated_dygraphs, single_svgs, correlated_svgs

  def generate_summary_page(self, template_environment, summary_html_content):
    summary_html = template_environment.get_template(self.report_templates['header']).render(custom_stylesheet_includes=self.stylesheet_includes, custom_javascript_includes=self.javascript_includes) + '\n'
    summary_html += template_environment.get_template(self.report_templates['summary']).render(metric_list=sorted(self.metric_list), summary_html_content=summary_html_content, correlated_plots=self.correlated_plots) + '\n'
    summary_html += template_environment.get_template(self.report_templates['footer']).render()
    return summary_html

  def generate(self):
    template_loader = FileSystemLoader(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'templates')))
    template_environment = Environment(loader=template_loader)
    summary_html_content = ''
    summary_enabled = self.enable_summary_tab(self.output_directory)
    for metric in self.metric_list:
      metric_stats_file, summary_stats_file, metric_plots, metric_correlated_plots, single_dygraphs, \
      correlated_dygraphs, single_svgs, correlated_svgs = self.discover_metric_data(self.output_directory, metric)
      if len(single_dygraphs) > 0:
        dygraph_html = ''
        for single_dyg in single_dygraphs:
          with open(single_dyg,'r') as dyg_file:
            dygraph_html += '\n' + dyg_file.read()
      if summary_stats_file != '':
        summary_stats = self.get_summary_table(summary_stats_file)
        summary_html_content += template_environment.get_template(self.report_templates['summary_content']).render(metric_stats=summary_stats, metric=metric) + '\n'
      if metric_stats_file != '' or len(metric_plots) > 0:
        metric_stats = self.get_summary_table(metric_stats_file)
        metric_html = template_environment.get_template(self.report_templates['header']).render(custom_stylesheet_includes=self.stylesheet_includes, custom_javascript_includes=self.javascript_includes)
        metric_html += template_environment.get_template(self.report_templates['metric']).render(metric_stats=metric_stats, metric_plots=metric_plots, metric=metric, metric_list=sorted(self.metric_list), summary_enabled=summary_enabled, svg_plots=single_svgs, dyg_plots=dygraph_html)
        metric_html += template_environment.get_template(self.report_templates['footer']).render()
        with open(os.path.join(self.output_directory, metric + '_report.html'), 'w') as metric_report:
          metric_report.write(metric_html)
    if summary_enabled:
      with open(os.path.join(self.output_directory, 'summary_report.html'),'w') as summary_report:
        summary_report.write(self.generate_summary_page(template_environment, summary_html_content))