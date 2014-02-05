# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

import logging
import shlex
import subprocess
from naarad.run_steps.run_step import Run_Step

logger = logging.getLogger('naarad.run_steps.local_cmd')

class Local_Cmd(Run_Step):

  def __init__(self, run_type, run_cmd, should_wait=True):
    Run_Step.__init__(self, run_type, run_cmd, should_wait)

  def run(self):
    cmd_args = shlex.split(self.run_cmd)
    logger.info('Running subprocess command with following args: ' + str(cmd_args))

    #TODO: Add try catch blocks. Kill process on CTRL-C
    #TODO: Add inferring time periodß
    #TODO: Add docstrings

    process = subprocess.Popen(cmd_args, stdout=subprocess.PIPE)
    (stdoutdata, stderrdata) = process.communicate()
    logger.info('subprocess finished')
    if stdoutdata: logger.info('stdout: ' + stdoutdata)
    if stderrdata: logger.info('stderr: ' + stderrdata)


