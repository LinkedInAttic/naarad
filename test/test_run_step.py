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

import os
import sys
# add the path of ~/naarad/src;   the testing py is under ~/naarad/test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')))

from naarad.run_steps.run_step import Run_Step
from naarad.run_steps.local_cmd import Local_Cmd
import naarad.utils
import naarad.naarad_constants as CONSTANTS

local_cmd_obj = None


def setup_module():
  global local_cmd_obj
  run_cmd = "sleep 10"
  run_rank = 1
  run_type = CONSTANTS.RUN_TYPE_WORKLOAD
  run_order = CONSTANTS.PRE_ANALYSIS_RUN
  call_type = 'local'
  local_cmd_obj = Local_Cmd(run_type, run_cmd, call_type, run_order, run_rank)


def test_run_local_cmd():
  """
  Test whether local command works as expected
  :return: None
  """
  global local_cmd_obj
  local_cmd_obj.run()
  ts_diff = naarad.utils.convert_to_unixts(local_cmd_obj.ts_end) - naarad.utils.convert_to_unixts(local_cmd_obj.ts_start)
  ts_diff /= 1000
  assert ts_diff == 10.0


def test_run_local_cmd_with_kill():
  """
  Test whether local command works as expected when kill is specified
  :return: None
  """
  global local_cmd_obj
  local_cmd_obj.kill_after_seconds = 5
  local_cmd_obj.run()
  ts_diff = naarad.utils.convert_to_unixts(local_cmd_obj.ts_end) - naarad.utils.convert_to_unixts(local_cmd_obj.ts_start)
  ts_diff /= 1000
  assert ts_diff == 5.0
