#! /usr/bin/python

from setuptools import setup, find_packages

with open('VERSION') as f:
      naarad_version = f.read().strip()

with open('requirements.txt') as f:
      required = f.read().splitlines()

setup(name="naarad",
      description='Naarad is a Performance Analysis tool',
      url='https://github.com/linkedin/naarad',
      author='Naarad Developers',
      author_email='naarad-dev@googlegroups.com',
      version=naarad_version,
      packages=['naarad', 'naarad.metrics', 'naarad.graphing', 'naarad.reporting', 'naarad.run_steps', 'naarad.resources'],
      scripts = ['bin/naarad', 'bin/PrintGCStats', 'bin/naarad_metric_collector.sh', 'bin/addDateStampToGC'],
      package_dir={ '' : 'src'},
      package_data={ '' : ['src/naarad/resources/*.html']},
      include_package_data=True,
      install_requires=required,
      license='Apache 2.0',
      )
