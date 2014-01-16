#preferred user to run the pkg
USER=app
if id -u $USER >/dev/null 2>&1
then
  chown -R app:app /export/content/data/perf
else
  #$USER does not exist, change cron.d script to root
  sed -i 's/*\ app\ /*\ root\ /g' /etc/cron.d/stats-collector
fi

#make the logs readable by others
chmod -R 755 /export/content/data/perf

chown root:root /etc/cron.d/stats-collector
