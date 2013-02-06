from matplotlib import pyplot as plt, dates as mdates
import numpy as np
import os

def convert_to_mdate(date_str):
  try:
    mdate = mdates.strpdate2num('%Y-%m-%d %H:%M:%S.%f')(date_str)
  except:
    mdate = mdates.strpdate2num('%Y-%m-%d %H:%M:%S')(date_str)
  return mdate


def graph_csv(output_directory, csv_file, plot_title, output_filename, y_label=None, precision=None, graph_height="600", graph_width="1500", graph_type="line", graph_color="black"):
  """ Single metric graphing function using matplotlib"""
  if not os.path.getsize(csv_file):
    return False
  y_label = y_label or plot_title
  days, impressions = np.loadtxt(csv_file, unpack=True, delimiter=",", converters={ 0: convert_to_mdate})
  fig = plt.figure()
  fig.set_size_inches(float(graph_width) / 80, float(graph_height) / 80)
  if graph_type == "line":
    line_style = "-"
    marker = None
  else:
    marker = "."
    line_style = None

  plt.plot_date(x=days, y=impressions, linestyle=line_style, marker=marker, color=graph_color)
  plt.title(plot_title)
  plt.ylabel(y_label)
  plt.grid(True)
  # Get current axis and its xtick labels
  labels = plt.gca().get_xticklabels()
  for label in labels:
    label.set_rotation(30)
  plot_file_name = os.path.join(output_directory, output_filename + ".png")
  fig.savefig(plot_file_name)
  return (True, None)
