import numpy as np
from perceptron import NN
import logging
from cbpro_client import get_client

class Memoize:
  def __init__(self, fn):
    self.fn = fn
    self.memo = {}

  def __call__(self, *args):
    if args not in self.memo:
      self.memo[args] = self.fn(*args)
    return self.memo[args]

def trainPerceptron(NUMPOINTS=21, sensitivity=0.02):
  inputs = []
  outputs= []

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(float(i) / (NUMPOINTS - 1))
  val = 1

  logging.debug("f(x)=x : "+str(tmparr)+"->"+str(val))
  inputs.append(tmparr)
  outputs.append([val])
  #savePlot(range(NUMPOINTS),tmparr,'fx_x.png')

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(0.5 + np.sin(2 * np.pi * float(i) / (NUMPOINTS - 1)) / 2)
  val = 0.5

  logging.debug("f(x)=sin(2*pi*x) :"+str(tmparr)+"->"+str(val))
  inputs.append(tmparr)
  outputs.append([val])
  #savePlot(range(NUMPOINTS),tmparr,'fx_sin2pix.png')

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(0.5 + np.cos(2 * np.pi * float(i) / (NUMPOINTS - 1)) / 2)
  val = 0.5

  logging.debug("f(x)=cos(2*pi*x) :"+str(tmparr)+"->"+str(val))
  inputs.append(tmparr)
  outputs.append([val])
  #savePlot(range(NUMPOINTS),tmparr,'fx_cos2pix.png')

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(1.0 - float(i) / (NUMPOINTS - 1))
  val = 0

  logging.debug("f(x)=1-x : "+str(tmparr)+"->"+str(val))
  inputs.append(tmparr)
  outputs.append([val])
  #savePlot(range(NUMPOINTS),tmparr,'fx_1-x.png')

  inputs =np.array(inputs)
  outputs=np.array(outputs)

  n=NN(inputs, outputs, sensitivity=sensitivity)
  predictions = n.predict(inputs)
  logging.info("Predicted:"+str(predictions.T))
  logging.info("Expected: "+str(outputs.T))
  for i in range(len(outputs.T)):
    if abs(outputs.T[0][i] - predictions.T[0][i]) > sensitivity * 2:
      logging.warning("Training failure: i="+str(i))
      return None

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append((float(i) / (NUMPOINTS - 1)) / 2)
  predictions = n.predict(np.array(tmparr))
  #savePlot(range(NUMPOINTS),tmparr,'fx_x_2.png')
  if abs(predictions.T[0] - 1) > 0.25:
    logging.debug("f(x)=x/2 : "+str(tmparr)+"->"+str(predictions))
    logging.warning("Training failure: f(x)=x/2")
    return None

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(0)
  tmparr[NUMPOINTS - 3] = 0.75
  tmparr[NUMPOINTS - 2] = 1
  tmparr[NUMPOINTS - 1] = 0.75
  predictions = n.predict(np.array(tmparr))
  #savePlot(range(NUMPOINTS),tmparr,'fx_x-1.png')
  if abs(predictions.T[0] - 1) > 0.25:
    logging.debug("f(x)=(x=n-1)?1:0 : "+str(tmparr)+"->"+str(predictions))
    logging.warning("Training failure: f(x)=(x=n-1)?1:0")
    return None

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(0)
  predictions = n.predict(np.array(tmparr))
  #savePlot(range(NUMPOINTS),tmparr,'fx_0.png')
  if abs(predictions.T[0] - 0.5) > 0.25:
    logging.debug("f(x)=0 : "+str(tmparr)+"->"+str(predictions))
    logging.warning("Training failure: f(x)=0")
    return None

  return n

def buysell(nn, data, sensitivity, marketVolatility=0.1):
  minData = min(data)
  maxData = max(data)
  if (maxData - minData) / minData < marketVolatility: # No significant market change
    return "none"
#  print("min: ",minData, " max:", maxData)
  data = (np.array(data) - minData) / (maxData - minData)
  predict = nn.predict(data)
  logging.debug("Stocks : "+str(data)+"->"+str(predict))
  if predict > 1.0 - sensitivity:
    return "sell"
  elif predict < sensitivity:
    return "buy"
  else:
    return "none"

def column(matrix, i):
  return [row[i] for row in matrix]

def savePlot(x,y,filename,xAsEpoch=False):
  import matplotlib as mpl
  mpl.use('agg')
  import matplotlib.pyplot as plt
  import matplotlib.dates as mdate
  fig, ax = plt.subplots()
  if xAsEpoch == True:
    x = mdate.epoch2num(x)
    ax.plot_date(x,y)
    # Choose your xtick format string
    date_fmt = '%y-%m-%d %H:%M:%S'

    # Use a DateFormatter to set the data to the correct format.
    date_formatter = mdate.DateFormatter(date_fmt)
    ax.xaxis.set_major_formatter(date_formatter)

    # Sets the tick labels diagonal so they fit easier.
    fig.autofmt_xdate()
  else:
    ax.plot(x,y)

  fig.savefig(filename)

def getAction(product_id, nn, NUMPOINTS, doSavePlot=False):
  rates = get_client().get_product_historic_rates(product_id, granularity=3600)
  rates = rates[::-1] # reverse order so it goes in chronological order

  y = column(rates,3)[-NUMPOINTS:]

  action = buysell(nn, y, 0.06)
  logging.info("y ("+str(len(y))+"):"+str(y))
  logging.info("action: " + action)

  if doSavePlot == True:
    x = column(rates,0)[-NUMPOINTS:]
    logging.info("x ("+str(len(x))+"):"+str(x))
    savePlot(x,y,'prices-'+product_id+'.png',False)

  return action

def getBaseFunds(base):
  accounts = get_client().get_accounts()
  for acct in accounts:
    if acct['currency'] == base:
      return float(acct['available'])
  return -1

def roundFiatCurrency(base, value):
  if base == "USD" or base == "EUR":
    return round(value,2)
  return value

@Memoize
def getDCAPrice(base,currency,available):
  if available == 0:
    return 0

  fills = get_client().get_fills(product_id=currency+'-'+base)
  cost = 0
  totalSize = 0
  for fill in fills:
    if totalSize >= available:
      break
    if fill['side'] == "buy":
      logging.debug("bought " + currency + ": " + fill['size'] + " @ " + fill['price'] + " + " + fill['fee'])
      curSize = float(fill['size'])
      if curSize > available - totalSize:
        curSize = available - totalSize
      cost = cost + float(fill['price']) * curSize + float(fill['fee'])
      totalSize = totalSize + curSize

  if totalSize < available:
    logging.warning("Unreliable price for "+currency+". Using $0.")
    return 0

  dcaPrice = roundFiatCurrency(base, cost / totalSize)
  logging.info("Currency=" + currency + ". Cost=" + str(cost) + ". TotalSize=" + str(totalSize) + ". Available=" + str(available) + ". DCAPrice=" + str(dcaPrice))
  return dcaPrice

def getCurPrice(product_id):
  return float(get_client().get_product_ticker(product_id=product_id)['bid'])

def getAvailable(currency):
  accounts = get_client().get_accounts()
  for acct in accounts:
    if acct['currency'] == currency: # Found it
      return float(acct['available'])
  return 0

def getInvestmentValue(exchanges):
  accounts = get_client().get_accounts()
  total = 0
  for acct in accounts:
    if float(acct['available']) != 0 and acct['currency'] in exchanges:
      dcaPrice = getDCAPrice(base,acct['currency'],float(acct['available']))
      total = total + float(acct['available'])*dcaPrice
  return total

def mainFunc(base, exchanges, allowTrades=False):
  logging.info("Loading Perceptron...")
  try:
    import cPickle as pickle
  except ModuleNotFoundError:
    import pickle

  filename='.perceptron.obj'
  import os.path
  if os.path.exists(filename):
    logging.info("Using existing perceptron from "+filename)
    with open(filename,'rb') as input:
      n = pickle.load(input)
  else:
    logging.info("Using new perceptron")
    NUMPOINTS = 40
    n = trainPerceptron(NUMPOINTS,0.01)
    if n is None:
      return
    with open(filename, 'wb') as output:
      pickle.dump(n, output)

  #n.printNN()

  logging.info("Calculating actions...")
  portfolioValue = getInvestmentValue(exchanges) + getBaseFunds(base)
  for exchange in exchanges:
    product_id = exchange+'-'+base
    action = getAction(product_id, n, n.getNumPoints(), True)
    print (product_id,"->",action)
    if action == 'buy':
      baseFunds = getBaseFunds(base)
      if baseFunds < 10: # Not enough to invest
        continue
      available = getAvailable(exchange)
      if 100 * (available * getDCAPrice(base, exchange, available)) / portfolioValue < 2 * 100 / len(exchanges): # No one product_id may be more than 2x any other product_id
        amount = round(0.01 * baseFunds,2)
        if amount < 10: # Minimum amount
          amount = 10
        print ("Buying "+str(amount)+base+" of "+exchange+" at "+str(getCurPrice(product_id)))
        if allowTrades == True:
          print (get_client().place_market_order(product_id=product_id,side='buy',funds=amount))
    elif action == 'sell':
      available = getAvailable(exchange)
      if available != 0: # Has money in it
        curPrice = getCurPrice(product_id)
        dcaPrice = getDCAPrice(base,exchange,available)
        if curPrice > dcaPrice*1.1: # Worthwhile selling (with fees)
          print ("Selling "+str(available)+" of "+exchange+" at "+str(curPrice)+" (dca="+str(dcaPrice)+"). Total: $"+str(curPrice * available))
          if allowTrades == True:
            print (get_client().place_market_order(product_id=product_id,side='sell',size=available))

def printPortfolio(base, exchanges):
  baseFunds = getBaseFunds(base)
  print ("Funds available: "+str(roundFiatCurrency(base,baseFunds))+base)
  portfolioValue = getInvestmentValue(exchanges) + baseFunds
  accounts = get_client().get_accounts()
  for acct in accounts:
    available = float(acct['available'])
    if available != 0 and acct['currency'] in exchanges:
      dcaPrice = getDCAPrice(base,acct['currency'],available)
      value = available*dcaPrice
      print (acct['currency']+": "+acct['available']+" @ "+str(dcaPrice)+" = "+str(roundFiatCurrency(base,value))+" ("+str(round(100 * value / portfolioValue,2))+"%)")
  print ("Total portfolio: "+str(roundFiatCurrency(base,portfolioValue))+base)

logging.basicConfig(level=logging.WARNING)

float_formatter = "{:.2f}".format
np.set_printoptions(formatter={'float_kind':float_formatter})

base = 'USD'
exchanges = ['BTC', 'ETH', 'ADA', 'LINK', 'KNC', 'DASH', 'SUSHI', 'OMG', 'UNI']
mainFunc(base, exchanges,True)
printPortfolio(base, exchanges)
