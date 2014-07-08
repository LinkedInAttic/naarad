#! /usr/bin/python

from setuptools import setup, find_packages

naarad_version = '1.0.8'

with open('requirements.txt') as f:
      required = f.read().splitlines()

setup(name="naarad",
      description='https://github.com/linkedin/naarad',
      url='https://github.com/linkedin/naarad',
      version=naarad_version,
      packages=['naarad', 'naarad.metrics', 'naarad.graphing', 'naarad.reporting', 'naarad.run_steps', 'naarad.resources'],  
      scripts = ['bin/naarad', 'bin/PrintGCStats'],
      package_dir={ '' : 'src'},
      package_data={ '' : ['src/naarad/resources/*.html']},
      include_package_data=True,
      install_requires=required,
      license='https://raw.githubusercontent.com/linkedin/naarad/master/LICENSE',
      download_url='https://github.com/linkedin/naarad/archive/v' + naarad_version + '.zip'
      )
