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

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(1.0 - float(i) / (NUMPOINTS - 1))
  val = 0

  logging.debug("f(x)=1-x : ", tmparr, "->", val)
  inputs.append(tmparr)
  outputs.append([val])

  inputs =np.array(inputs)
  outputs=np.array(outputs)

  sensitivity = 0.02
  n=NN(inputs, outputs, sensitivity=sensitivity)
  predictions = n.predict(inputs)
  logging.info("Predicted:"+str(predictions.T))
  logging.info("Expected: "+str(outputs.T))
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

def buysell(nn, data, sensitivity):
  minData = min(data)
  maxData = max(data)
  if maxData == minData:
    return "none"
#  print("min: ",minData, " max:", maxData)
  data = (np.array(data) - minData) / (maxData - minData)
  predict = nn.predict(data)
  logging.debug("Stocks : ", data, "->", predict)
  if predict > 1.0 - sensitivity:
    return "sell"
  elif predict < sensitivity:
    return "buy"
  else:
    return "none"

def column(matrix, i):
  return [row[i] for row in matrix]

def getAction(client, exchange, nn, NUMPOINTS, savePlot=False):
  rates = client.get_product_historic_rates(exchange, granularity=3600)
  rates = rates[::-1] # reverse order so it goes in chronological order

  y = column(rates,3)[-NUMPOINTS:]

  action = buysell(nn, y, 0.06)
  logging.info("y ("+str(len(y))+"):"+str(y))
  logging.info("action: " + action)

  if savePlot == True:
    import matplotlib as mpl
    mpl.use('agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdate
    x = mdate.epoch2num(column(rates,0)[-NUMPOINTS:])
    logging.info("x ("+str(len(x))+"):"+str(x))
    fig, ax = plt.subplots()
    ax.plot_date(x,y)
    # Choose your xtick format string
    date_fmt = '%y-%m-%d %H:%M:%S'

    # Use a DateFormatter to set the data to the correct format.
    date_formatter = mdate.DateFormatter(date_fmt)
    ax.xaxis.set_major_formatter(date_formatter)

    # Sets the tick labels diagonal so they fit easier.
    fig.autofmt_xdate()
    fig.savefig(exchange+'.png')

  return action

def mainFunc():
  logging.info("Loading Perceptron...")
  try:
    import cPickle as pickle
  except ModuleNotFoundError:
    import pickle

  filename='perceptron.obj'
  import os.path
  if os.path.exists(filename):
    logging.info("Using existing perceptron from "+filename)
    with open(filename,'rb') as input:
      n = pickle.load(input)
  else:
    logging.info("Using new perceptron")
    NUMPOINTS = 40
    n = trainPerceptron(NUMPOINTS)
    with open(filename, 'wb') as output:
      pickle.dump(n, output)

  #n.printNN()

  logging.info("Connecting to Coinbase...")
  from cbpro_client import get_client
  client = get_client()

  logging.info("Calculating actions...")
  for exchange in ['BTC-USD', 'ETH-USD', 'ADA-USD', 'LINK-USD', 'KNC-USD', 'DASH-USD']:
    action = getAction(client, exchange, n, n.getNumPoints(), True)
    print (exchange,"->",action)

logging.basicConfig(level=logging.INFO)

float_formatter = "{:.2f}".format
np.set_printoptions(formatter={'float_kind':float_formatter})

mainFunc()