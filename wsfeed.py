import cbpro, time
import numpy as np
from perceptron import NN
import logging

def trainPerceptron(NUMPOINTS=21):
  inputs = []
  outputs= []

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(float(i) / (NUMPOINTS - 1))
  val = 1

  logging.debug("f(x)=x : ",tmparr, "->", val)
  inputs.append(tmparr)
  outputs.append([val])

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(0.5 + np.sin(2 * np.pi * float(i) / (NUMPOINTS - 1)) / 2)
  val = 0.5

  logging.debug("f(x)=sin(2*pi*x) :", tmparr, "->", val)
  inputs.append(tmparr)
  outputs.append([val])

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(0.5 + np.cos(2 * np.pi * float(i) / (NUMPOINTS - 1)) / 2)
  val = 0.5

  logging.debug("f(x)=cos(2*pi*x) :", tmparr, "->", val)
  inputs.append(tmparr)
  outputs.append([val])

  # tmparr = []
  # for i in range(NUMPOINTS):
  #     tmparr.append(0.5)
  # val = 0.5

  # logging.debug("f(x)=0.5 : ", tmparr, "->", val)
  # inputs.append(tmparr)
  # outputs.append([val])

  # tmparr = []
  # for i in range(NUMPOINTS):
  #     tmparr.append(0)
  # val = 0.5

  # logging.debug("f(x)=0 : ", tmparr, "->", val)
  # inputs.append(tmparr)
  # outputs.append([val])

  # tmparr = []
  # for i in range(NUMPOINTS):
  #     tmparr.append(1)
  # val = 0.5

  # logging.debug("f(x)=1 : ", tmparr, "->", val)
  # inputs.append(tmparr)
  # outputs.append([val])

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(1.0 - float(i) / (NUMPOINTS - 1))
  val = 0

  logging.debug("f(x)=1-x : ", tmparr, "->", val)
  inputs.append(tmparr)
  outputs.append([val])

  inputs =np.array(inputs)
  outputs=np.array(outputs)

  n=NN(inputs)
  # print(n.predict(inputs).T) # Before training
  sensitivity = 0.02
  n.train(inputs, outputs, sensitivity=sensitivity)
  predictions = n.predict(inputs)
  logging.info("Predicted:",predictions.T)
  logging.info("Expected: ",outputs.T)
  for i in range(len(outputs.T)):
    if abs(outputs.T[0][i] - predictions.T[0][i]) > sensitivity + 0.01:
      logging.warning("Training failure: i=",i)
      return None

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append((float(i) / (NUMPOINTS - 1)) / 2)
  predictions = n.predict(np.array(tmparr))
  if abs(predictions.T[0] - 1) > 0.25:
    logging.debug("f(x)=x/2 : ", tmparr, "->", predictions)
    logging.warning("Training failure: f(x)=x/2")
    return None

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(0)
  tmparr[NUMPOINTS - 2] = 1
  tmparr[NUMPOINTS - 1] = 0.75
  predictions = n.predict(np.array(tmparr))
  if abs(predictions.T[0] - 1) > 0.25:
    logging.debug("f(x)=(x=n-1)?1:0 : ", tmparr, "->", predictions)
    logging.warning("Training failure: f(x)=(x=n-1)?1:0")
    return None

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(0)
  predictions = n.predict(np.array(tmparr))
  if abs(predictions.T[0] - 0.5) > 0.25:
    logging.debug("f(x)=0 : ", tmparr, "->", predictions)
    logging.warning("Training failure: f(x)=0")
    return None

  return n

def buysell(data, sensitivity):
  minData = min(data)
  maxData = max(data)
  if maxData == minData:
    return "none"
#  print("min: ",minData, " max:", maxData)
  data = (np.array(data) - minData) / (maxData - minData)
  predict = n.predict(data)
  logging.info("Stocks : ", data, "->", predict)
  if predict > 1.0 - sensitivity:
    return "sell"
  elif predict < sensitivity:
    return "buy"
  else:
    return "none"

class myWebsocketClient(cbpro.WebsocketClient):
  def __init__(self):
    super(myWebsocketClient,self).__init__()
    self.data = []
    self.lastBuyPriceBTC = 0.0
    self.currentPriceBTCUSD = 0.0
    self.buyCount = 0
    self.fee = 20 # in USD
  def on_open(self):
      self.url = "wss://ws-feed.pro.coinbase.com/"
      self.products = ["BTC-USD"]
      self.channels = ["ticker"]
      self.message_count = 0
      print("Lets count the messages!")
  def on_message(self, msg):
      global currentUSD
      global currentBTC
      self.message_count += 1
      if 'type' in msg:
        if msg["type"] == "error":
          print ("Error: ", msg)
        elif msg["type"] == "ticker":
          self.currentPriceBTCUSD = float(msg["price"])
          with open('prices.txt','a') as f:
            print (msg["product_id"], " ", msg["side"], "\t@ {:.3f}".format(self.currentPriceBTCUSD), file=f)
          self.data.append(self.currentPriceBTCUSD)
          if len(self.data) > NUMPOINTS:
            self.data = self.data[-NUMPOINTS:] # last NUMPOINTS elements
            action = buysell(self.data, 0.1)
            if action == "buy":
              if (currentUSD != 0) and ((self.lastBuyPriceBTC == 0) or (self.currentPriceBTCUSD - self.fee < self.lastBuyPriceBTC + self.fee)):
                self.buyCount = self.buyCount + 1
                if self.buyCount > NUMPOINTS / 10:
                  currentBTC = currentUSD / (self.currentPriceBTCUSD + self.fee)
                  currentUSD = 0.0
                  self.lastBuyPriceBTC = self.currentPriceBTCUSD
                  print("bought ", currentBTC, "BTC for ", self.currentPriceBTCUSD + self.fee)
            elif action == "sell":
              self.buyCount = 0
              if (currentBTC != 0) and (self.currentPriceBTCUSD - self.fee > self.lastBuyPriceBTC + self.fee):
                currentUSD = round(currentBTC * (self.currentPriceBTCUSD - self.fee),2)
                currentBTC = 0.0
                print("sold for $", currentUSD, " at ", self.currentPriceBTCUSD - self.fee)
            else:
              self.buyCount = 0
        else:
          print ("Unknown type: ", msg["type"])
  def on_close(self):
      print("-- Goodbye! --")


logging.basicConfig(level=logging.WARNING)

float_formatter = "{:.2f}".format
np.set_printoptions(formatter={'float_kind':float_formatter})

NUMPOINTS = 40
n = trainPerceptron(NUMPOINTS)

#currentUSD = 100.0
#currentBTC = 0.0

#rates = cbpro_client.get_product_historic_rates('BTC-USD')
#print ("Rates=",rates)

from cbpro_client import get_client

client = get_client()

def column(matrix, i):
  return [row[i] for row in matrix]

rates = client.get_product_historic_rates('ETH-USD', granularity=3600)
rates = rates[::-1] # reverse order so it goes in chronological order

import matplotlib as mpl
mpl.use('agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdate
x = mdate.epoch2num(column(rates,0)[0:NUMPOINTS])
y = column(rates,3)[0:NUMPOINTS]
action = buysell(y, 0.06)
logging.info("x (",len(x),"):", x)
logging.info("y (",len(y),"):", y)
logging.info("action: ", action)
fig, ax = plt.subplots()
ax.plot_date(x,y)
# Choose your xtick format string
date_fmt = '%y-%m-%d %H:%M:%S'

# Use a DateFormatter to set the data to the correct format.
date_formatter = mdate.DateFormatter(date_fmt)
ax.xaxis.set_major_formatter(date_formatter)

# Sets the tick labels diagonal so they fit easier.
fig.autofmt_xdate()
plt.savefig('tmp.png')


#wsClient = myWebsocketClient()
#wsClient.start()
#print(wsClient.url, wsClient.products)
#while (1):
#  print ("message_count =", "{}".format(wsClient.message_count),". Assets: $", "{:.2f}".format(currentUSD + wsClient.currentPriceBTCUSD * currentBTC))
#  time.sleep(10)
#wsClient.close()

