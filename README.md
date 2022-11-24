cbtrader - A Coinbase trading bot

# Description
This is a simple trading bot that uses a Perceptron network to determine if the price of something is near a local peak. It is simple enough to run on a Raspberry Pi in a couple seconds. Most of the time is in downloading of the trading history. The bot runs within a Docker container to make it easier to have multiple projects hosted on the same machine without having a dependency problem.

# How to run

Create a config file with the following:
```
CB_KEY=
CB_PASSPHRASE=
CB_SECRET=
BASE_CURRENCY=
BUYING_CURRENCY=
SELLING_CURRENCY=
```

Then you can use the 'run.sh' to execute the bot.

Add the following to /etc/crontab to have it run every 15 minutes:
```
 0 * * * * root script -c "docker run --rm -v /home/pi/cbtrader:/opt/cbtrader -w /opt/cbtrader cbtrader python3 cbtrader.py" -a /var/log/cbtrader.log
15 * * * * root script -c "docker run --rm -v /home/pi/cbtrader:/opt/cbtrader -w /opt/cbtrader cbtrader python3 cbtrader.py -b" -a /var/log/cbtrader.log
30 * * * * root script -c "docker run --rm -v /home/pi/cbtrader:/opt/cbtrader -w /opt/cbtrader cbtrader python3 cbtrader.py" -a /var/log/cbtrader.log
45 * * * * root script -c "docker run --rm -v /home/pi/cbtrader:/opt/cbtrader -w /opt/cbtrader cbtrader python3 cbtrader.py" -a /var/log/cbtrader.log
```

# Support
You can support me and work similar to this with:
[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoff.ee/bandi13)
