#! /usr/bin/python

import os
from setuptools import setup, find_packages

with open('requirements.txt') as f:
      required = f.read().splitlines()

setup(name="naarad",
      description='https://github.com/linkedin/naarad',
      url='https://github.com/linkedin/naarad',
      version='1.0',
      packages=['naarad', 'naarad.metrics', 'naarad.graphing', 'naarad.reporting', 'naarad.run_steps', 'naarad.resources'],  
      #packages = find_packages(),
      scripts = ['bin/naarad', 'bin/PrintGCStats'],
      package_dir={ '' : 'src'},
      #package_data={ '' : ['src/naarad/resources/*.html']},
      include_package_data=True,
      install_requires=required,
      )
