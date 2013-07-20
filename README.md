# Neelix #
Neelix is a highly configurable command line tool that parses and plots timeseries data for better visual correlation. It can be used for performance debugging for your service/application. You collect data for the metrics you want to monitor and:

* Neelix parses JVM Garbage Collection (GC), System (SAR) and Mysql (Innotop) logs
* Neelix reads other metrics you have pre-processed and written in CSV format
* Neelix plots the metrics you specify.

The power of Neelix is in its configurablity. You can use it to glance at various metrics and then choose the important metrics to plot to visually correlate the metrics together. An example use-case is when your application's throughput dropped, you want to know if it was because of some GC activity or a spike in CPU usage or disk I/O. Neelix can help you investigate such issue better.

Neelix features:

* Configurable input format, so you can specify which metrics to inspect. GC, SAR and Innotop logs supported currently, with support for more metrics coming in near future. 
* Logs for the supported metrics are parsed by Neelix.
* Also supports generic metric logs in csv format. 
* Pick 'n Choose which metrics to plot together for visual correlation.
* Html report with all the plots for a visual inspection of your application's performance profile.

## Installation ##

1. Check out Neelix code:
<pre> git clone git://gitli.corp.linkedin.com/neelix/neelix.git </pre>
2. Make sure you have python, [pip](http://www.pip-installer.org/en/latest/installing.html) and awk.
3. Install the necessary Python libraries using PIP.
    <pre>cd neelix; pip install -r requirements.txt</pre>

## Usage ##

Neelix needs a config file that lists all the metrics and the graphing options. Example config files can be found in neelix/examples/conf directory. Here is a sample config:

<pre>
[GC]
infile=/home/rmaheshw/logs/gc.log
gc-options=GC appstop alloc promo used0 used1 used commit0 commit1 commit gen0 gen0t gen0usr gen0sys cmsIM cmsRM cmsRS GC cmsCM
access=local

[SAR-cpuusage]
access=local
infile=/home/rmaheshw/logs/sar.cpuusage.out
 
[GRAPH]
outdir=/home/rmaheshw/neelix-out
</pre>

 The config is in INI format with each section describing details about each metric and a special section called GRAPH specifying details about the graphing options.

 Once you have a config describing all your metrics, parsing and plotting needs, just call neelix with the config file as its argument and it should produce all the plots in a basic html report in the outdir specified in config

<pre> neelix config</pre>
 
 Neelix can also take command line arguments: -i or --input_dir and -o or --output_dir. If input_dir is specified, all the infile options in the config are assumed to be relative to input_dir. User can also specify output_dir on command line and skip specifying the outdir option in the config. But if outdir is specified in the config, that takes precedence.

 So you could have a shorter config file:

<pre>
[GC]
infile=gc.log
gc-options=GC appstop alloc promo used0 used1 used commit0 commit1 commit gen0 gen0t gen0usr gen0sys cmsIM cmsRM cmsRS GC cmsCM
access=local

[SAR-cpuusage]
access=local
infile=sar.cpuusage.out

[GRAPH]
graphs=GC.GC,all GC.cmsRM,GC.cmsIM,GC.gen0t GC.promo,GC.alloc
</pre>

And run it as:

<pre> neelix config -i /home/rmaheshw/logs -o /home/rmaheshw/neelix-out</pre>

### Included examples ###

Some logs and config files are included in the source code. You can run these commands to test neelix. 

GC example:

<pre>bin/neelix -i examples/logs/ -o ~/tmp/neelix examples/conf/config-gc</pre>

This generates a results in ~/tmp/neelix. Fire up a browser to view ~/tmp/neelix/Report.html to see all the plots in one place.

SAR example:

<pre>bin/neelix -i test/data/logs/ -o ~/tmp/neelix test/conf/config-sar </pre>

View Results.html in firefox (Chrome complains about cross-domain issues). Note that the sar config specifies plotting graphs using dygraphs.

### Templates ###

Neelix comes with pre-built configs that you can use directly for simple cases. The templates are for GC, SAR and Innotop logs and can be used as:

<pre>bin/neelix --i test/data/logs/ -o ~/tmp/neelix template:gc</pre>
<pre>bin/neelix --i test/data/logs/ -o ~/tmp/neelix template:sar</pre>
<pre>bin/neelix --i test/data/logs/ -o ~/tmp/neelix template:innotop</pre>

