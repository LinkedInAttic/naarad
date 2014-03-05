# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

import logging
import shlex
import subprocess
import time
from naarad.run_steps.run_step import Run_Step

logger = logging.getLogger('naarad.run_steps.local_cmd')

class Local_Cmd(Run_Step):
  """
  Class for a local command as run step.
  This type will be most likely used when running workload from the same machine running naarad
  """

  def __init__(self, run_type, run_cmd, call_type, run_order, run_rank, should_wait=True):
    Run_Step.__init__(self, run_type, run_cmd, call_type, run_order, run_rank, should_wait)

  def run(self):
    """
    Run the command, infer time period to be used in metric analysis phase.
    :return: None
    """
    cmd_args = shlex.split(self.run_cmd)
    logger.info('Local command RUN-STEP starting with rank %d', self.run_rank)
    logger.info('Running subprocess command with following args: ' + str(cmd_args))

    #TODO: Add try catch blocks. Kill process on CTRL-C
    # Infer time period for analysis. Assume same timezone between client and servers.
    self.ts_start = time.strftime("%Y-%m-%d %H:%M:%S")
    process = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
    #Using 2nd method here to stream output:
    # http://stackoverflow.com/questions/2715847/python-read-streaming-input-from-subprocess-communicate
    for line in iter(process.stdout.readline, b''):
      logger.info(line)
    process.communicate()
    self.ts_end = time.strftime("%Y-%m-%d %H:%M:%S")
    logger.info('subprocess finished')
    logger.info('run_step started at ' + self.ts_start + ' and ended at ' + self.ts_end)
