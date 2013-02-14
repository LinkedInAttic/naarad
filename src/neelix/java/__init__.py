"""
  Java Helpers.
"""

import pkg_resources

def generate_jar_dir():
  """ Return the Java / JAR directory. """

  return pkg_resources.resource_filename('neelix.java', None)
