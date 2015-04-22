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

import logging

logger = logging.getLogger('naarad.run_steps.run_step')


class Run_Step(object):
  """
  Base class that holds information about different kinds of "run steps" like Workload kickoff, Pre-run setup scripts,
  Post-run setup scripts
  """

  def __init__(self, run_type, run_cmd, call_type, run_order, run_rank, should_wait=True, kill_after_seconds=None):
    """
    Init method
    :param run_type: Type of run_step: "workload" only for now
    :param run_cmd: Details of command to be run. It could be a command or API call
    :param call_type: Kind of call -- local or remote
    :param run_order: When to run this w.r.t analysis. One of ('pre', 'in', 'post')
    :param run_rank: In what order to run this
    :param should_wait: Boolean whether naarad should wait for the run command to finish or not before moving on
    :param kill_after_seconds: Seconds for which the command should be run before being killed
    :return: None
    """
    self.run_type = run_type
    self.run_cmd = run_cmd
    self.call_type = call_type
    self.run_order = run_order
    self.run_rank = run_rank
    self.should_wait = should_wait
    self.kill_after_seconds = kill_after_seconds
    self.timer = None
