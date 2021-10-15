cbtrader

Create a config file with the following:
>>>>
CB_KEY=
CB_PASSPHRASE=
CB_SECRET=
BASE_CURRENCY=
BUYING_CURRENCY=
SELLING_CURRENCY=
<<<<

Then you can use the 'run.sh' to execute the bot.

Add the following to /etc/crontab to have it run every 15 minutes:
 0 * * * * root script -c "docker run --rm -v /home/pi/cbtrader:/opt/cbtrader -w /opt/cbtrader cbtrader python3 cbtrader.py" -a /var/log/cbtrader.log
15 * * * * root script -c "docker run --rm -v /home/pi/cbtrader:/opt/cbtrader -w /opt/cbtrader cbtrader python3 cbtrader.py -b" -a /var/log/cbtrader.log
30 * * * * root script -c "docker run --rm -v /home/pi/cbtrader:/opt/cbtrader -w /opt/cbtrader cbtrader python3 cbtrader.py" -a /var/log/cbtrader.log
45 * * * * root script -c "docker run --rm -v /home/pi/cbtrader:/opt/cbtrader -w /opt/cbtrader cbtrader python3 cbtrader.py" -a /var/log/cbtrader.log

