docker build -t cbtrader . && \
docker run --rm -it -v $(pwd):/opt/cbtrader -w /opt/cbtrader cbtrader python3 wsfeed.py
