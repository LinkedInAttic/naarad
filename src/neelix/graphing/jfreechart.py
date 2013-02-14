import os

from linkedin.utils.java import JavaEnvironment, jar_dir_classpath
import neelix.java

#TODO(rmaheshw): use kwargs in all graph_csv methods
def graph_csv(output_directory, csv_file, plot_title, output_filename, y_label=None, precision=None):
  """ Single metric graphing function """
  if not os.path.getsize(csv_file):
    return False, None
  y_label = y_label or plot_title

  jar_dir = neelix.java.generate_jar_dir()
  java_repository = JavaEnvironment(jar_dir_classpath(jar_dir))
  if precision and precision == 'ms':
    java_repository.call('com.linkedin.util.PlotGC',
      "-charts", plot_title, "-cols", y_label,"-in", csv_file, "-out", output_directory,
      "-plotonsamegraph", "true", "-granularity", "ms", "-pngnames", output_filename)
  else:
    java_repository.call('com.linkedin.util.PlotGC',
      "-charts", plot_title, "-cols", y_label,"-in", csv_file, "-out", output_directory,
      "-plotonsamegraph", "true", "-pngnames", output_filename)
  return True, None

def graph_csv_n(output_directory, csv_file, plot_title, output_filename, columns):
  """ graph a csv file with n columns """
  jar_dir = neelix.java.generate_jar_dir()
  java_repository = JavaEnvironment(jar_dir_classpath(jar_dir))

  java_repository.call('com.linkedin.util.PlotGC',
      '-charts', plot_title, '-cols', ','.join(columns),'-in', csv_file, '-out', output_directory,
      '-plotonsamegraph', 'true', '-pngnames', output_filename)

