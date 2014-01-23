
- The perf-stat-collector package keeps collecting performance data and dumps them into a directory specified in the config file

- To run it:  python start.py  stat-collect.conf

- Internally, it reads a configure file, and creates a thread for each module (e.g., SAR-DEV)

- Every day's data are dumpled into a sub-directory named with the date (e.g., 2014-01-01)

- It deletes old data to save space
