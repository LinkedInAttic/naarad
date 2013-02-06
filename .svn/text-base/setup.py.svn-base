#!/usr/bin/env python

import os
import setuptools

from linkedin.python.setuptools import find_bin_files

# Don't install deps for development mode.
setuptools.bootstrap_install_from = None

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, "README.txt")).read()

setuptools.setup(
  name = 'neelix',
  version = '0.2',
  url = 'http://go/neelix',
  author = "Ritesh Maheshwari",
  author_email = "rmaheshw@linkedin.com",
  platforms = 'any',

  description = README,

  # What are we packaging up?
  package_dir = {'': 'src'},
  packages = setuptools.find_packages('src'),
  include_package_data = True,

  scripts = find_bin_files(),

  zip_safe = False,
  verbose = False,
)
