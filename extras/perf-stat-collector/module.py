# coding=utf-8
"""
© 2014 LinkedIn Corp. All rights reserved.

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

import os
import sys

class Module(object):

  def __init__(self, name, command, interval, out_file, isOn=True):
    """
    create the perf monitoring module
    :param str command: the shell command, invoked once only (mandatory)
    :param int interval: seconds 
    :param str out_file: the writing file name  (mandatory)
    :param bool isOn: whether it is on or not
    """
    
    self.name = name
    self.command = command
    self.interval = interval 
    self.isOn = isOn
    self.out_file = out_file
