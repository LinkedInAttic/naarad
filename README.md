# Naarad #

## What is Naarad? ##

Naarad is a framework for performance analysis & rating of sharded & stateful services

## Why Naarad? ##

Use-cases:
* Scalability / Headroom Rating 
* Continuous Integration ( Performance )
* Performance Investigation 

Naarad is a highly configurable system analysis tool that parses and plots timeseries data for better visual correlation. 
It can be used for performance analysis of your service/application.
You collect data for the metrics you want to monitor and:

* Naarad parses JVM Garbage Collection (GC), System/Network (SAR), Mysql (Innotop), Jmeter (JTL/XML) logs, VMStat, ZoneInfo, and MemInfo
* Naarad reads other metrics you have pre-processed and written in CSV format
* Naarad plots the metrics you specify.

The power of Naarad is in its configurablity. You can use it to glance at various metrics and then choose the important metrics to plot to visually correlate the metrics together. An example use-case is when your application's throughput dropped, you want to know if it was because of some GC activity or a spike in CPU usage or disk I/O. Naarad can help you investigate such issue better.

## Features ##

* Configurable input format, so you can specify which metrics to inspect. GC, SAR and Innotop logs supported currently, with support for more metrics coming in near future. 
* Logs for the supported metrics are parsed by Naarad.
* Also supports generic metric logs in csv format. 
* Pick 'n Choose which metrics to plot together for visual correlation.
* Html report with all the plots for a visual inspection of your application's performance profile.
* Grading support
* Diff support. Ability to diff two naarad reports. Reports generated with naarad version < 1.0.5 are not supported for diff functionality.

## How is it different? ##

Many tools and frameworks like Zenoss, rrdtool etc have solved the use-case of metric collection, parsing and plotting. Naarad has an overlap in functionality with these tools, but the main advantage of naarad is in its flexibility, which lets it be a powerful tool for performance investigations. Naarad users are performance experts who need to look for 'needle in a haystack'. Naarad was built to support this use-case. 

## Installation ##

1. Check out Naarad code:

        git clone https://github.com/linkedin/naarad.git

2. Make sure you have python (2.6 or 2.7), [pip](http://www.pip-installer.org/en/latest/installing.html) and awk.
3. Install the necessary Python libraries using PIP.

        cd naarad; pip install -r requirements.txt
4. For problems in installation, check out our [troubleshooting wiki](https://github.com/linkedin/naarad/wiki/Troubleshooting)

# More details #

Please check out our [wiki](https://github.com/linkedin/naarad/wiki) page for more details on Naarad's usage, supported metrics etc.
