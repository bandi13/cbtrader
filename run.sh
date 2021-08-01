docker build -t cbtrader . && \
docker run --rm -v $(pwd):/opt/cbtrader -w /opt/cbtrader cbtrader python3 cbtrader.py -b
