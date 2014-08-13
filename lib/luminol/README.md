# luminol #

## What is luminol? ##
luminol is a library that aids in root cause analysis for time series data. It includes algorithms for anomaly detection and correlation, which identify when "events" occured in one or more timeseries and how they correlate to other timeseries. Future releases will include the ability to not just correlate but also do automated root cause analysis. luminol was developed to aid application and system performance analysis, however it is generic enough to be used with any time series data.

## detector module (detector.py) APIs ##
detector.detector(data_or_data_path, baseline_data_or_data_path=None)
param: data_or_data_path: either a time series in list format or a path to a csv file
param: (optional)baseline_data_or_data_path: either a baseline time series in list format or a path to a csv file
return: a detector object
detector.get_all_scores()
return: the anomaly score time series
detector.get_anomalies()
a list of anomaly object

## correlator module(correlator.py) APIs ##
correlator.correlator(a, b)
param: a: time series a
param: b: time series b
return: a correlator object
correlator.get_correlation()
return a correlation object
correlator.is_correlated(threshold=None)
param: (optional)threshold: a numeric threshold above which is considered correlated.
return: a correlation object if the threshold is reached otherwise false

## Objects ##

### anomaly ###
attribute: start_time: where the anomaly period start
attribute: end_time: where the anomaly period end
attribute: score: the score of the anomaly detected
attribute: exact_time: the time point inside the window where this highest anomaly score is reached

### correlation ###
attribute: shift: the amount of shift if there is any
coefficient: the correlation coefficient

## additional tuning variables ##
There is some additional parameter you can set to tune the detector and correlation which resides in settings.py.
