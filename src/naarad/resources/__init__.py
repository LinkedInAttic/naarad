import pkg_resources


def get_dir():
  """Return the location of resources for report"""
  return pkg_resources.resource_filename('naarad.resources', None)
