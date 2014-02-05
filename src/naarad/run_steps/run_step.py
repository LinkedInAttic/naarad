# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

import logging

logger = logging.getLogger('naarad.run_steps.run_step')

class Run_Step(object):

  def __init__(self, run_type, run_cmd, call_type, should_wait=True, should_kill=False, duration=None):
    self.run_type = run_type
    self.run_cmd = run_cmd
    self.call_type = call_type
    self.should_wait = should_wait
    self.should_kill = should_kill
    self.duration = duration
