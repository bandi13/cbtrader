import numpy as np
from perceptron import NN
import logging
import os
import cbpro
from cbpro_account import cbpro_account

def train_perceptron(NUMPOINTS=21, sensitivity=0.02):
  inputs = []
  outputs= []

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(float(i) / (NUMPOINTS - 1))
  val = 1

  logging.debug("f(x)=x : "+str(tmparr)+"->"+str(val))
  inputs.append(tmparr)
  outputs.append([val])
  #save_plot(range(NUMPOINTS),tmparr,'fx_x.png')

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(0.5 + np.sin(2 * np.pi * float(i) / (NUMPOINTS - 1)) / 2)
  val = 0.5

  logging.debug("f(x)=sin(2*pi*x) :"+str(tmparr)+"->"+str(val))
  inputs.append(tmparr)
  outputs.append([val])
  #save_plot(range(NUMPOINTS),tmparr,'fx_sin2pix.png')

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(0.5 + np.cos(2 * np.pi * float(i) / (NUMPOINTS - 1)) / 2)
  val = 0.5

  logging.debug("f(x)=cos(2*pi*x) :"+str(tmparr)+"->"+str(val))
  inputs.append(tmparr)
  outputs.append([val])
  #save_plot(range(NUMPOINTS),tmparr,'fx_cos2pix.png')

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(1.0 - float(i) / (NUMPOINTS - 1))
  val = 0

  logging.debug("f(x)=1-x : "+str(tmparr)+"->"+str(val))
  inputs.append(tmparr)
  outputs.append([val])
  #save_plot(range(NUMPOINTS),tmparr,'fx_1-x.png')

  inputs =np.array(inputs)
  outputs=np.array(outputs)

  n=NN(inputs, outputs, sensitivity=sensitivity)
  predictions = n.predict(inputs)
  logging.debug("Predicted:"+str(predictions.T))
  logging.debug("Expected: "+str(outputs.T))
  for i in range(len(outputs.T)):
    if abs(outputs.T[0][i] - predictions.T[0][i]) > sensitivity * 2:
      logging.warning("Training failure: i="+str(i))
      return None

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append((float(i) / (NUMPOINTS - 1)) / 2)
  predictions = n.predict(np.array(tmparr))
  #save_plot(range(NUMPOINTS),tmparr,'fx_x_2.png')
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
  #save_plot(range(NUMPOINTS),tmparr,'fx_x-1.png')
  if abs(predictions.T[0] - 1) > 0.25:
    logging.debug("f(x)=(x=n-1)?1:0 : "+str(tmparr)+"->"+str(predictions))
    logging.warning("Training failure: f(x)=(x=n-1)?1:0")
    return None

  tmparr = []
  for i in range(NUMPOINTS):
      tmparr.append(0)
  predictions = n.predict(np.array(tmparr))
  #save_plot(range(NUMPOINTS),tmparr,'fx_0.png')
  if abs(predictions.T[0] - 0.5) > 0.25:
    logging.debug("f(x)=0 : "+str(tmparr)+"->"+str(predictions))
    logging.warning("Training failure: f(x)=0")
    return None

  return n

def buy_sell(nn, data, sensitivity, marketVolatility=0.1):
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

def save_plot(x,y,filename,xAsEpoch=False):
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

def get_action(cbpro_public_client,product_id, nn, NUMPOINTS, doSavePlot=False):
  rates = cbpro_public_client.get_product_historic_rates(product_id, granularity=3600)
  rates = rates[::-1] # reverse order so it goes in chronological order

  y = column(rates,3)[-NUMPOINTS:]

  action = buy_sell(nn, y, 0.06)
  logging.debug("y ("+str(len(y))+"):"+str(y))
  logging.debug("action: " + action)

  if doSavePlot == True:
    x = column(rates,0)[-NUMPOINTS:]
    logging.debug("x ("+str(len(x))+"):"+str(x))
    save_plot(x,y,'prices-'+product_id+'.png',False)

  return action

def main_func(clients):
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
    n = train_perceptron(NUMPOINTS,0.01)
    if n is None:
      return
    with open(filename, 'wb') as output:
      pickle.dump(n, output)

  #n.printNN()

  cbpro_public_client = cbpro.PublicClient()

  logging.info("Calculating actions...")
  product_ids = []
  for client in clients:
    product_ids.extend(client.get_product_ids())
  product_ids = sorted(set(product_ids)) # create unique list

  for product_id in product_ids:
    action = get_action(cbpro_public_client, product_id, n, n.getNumPoints(), False)
    print (product_id,"->",action)
    currencies = product_id.split('-')
    for client in clients:
      client.do_transaction(currencies[1],currencies[0],action,True)

def print_portfolio(cbclients):
  for cbclient in cbclients:
    print ("Client: " + cbclient.get_config_file_name())
    baseFunds = cbclient.get_base_funds()
    print ("Funds available: "+str(cbclient.round_fiat_currency(baseFunds))+cbclient.get_base_currency())
    portfolioValue = cbclient.get_portfolio_value()
    print ("Starting portfolio: "+str(cbclient.round_fiat_currency(portfolioValue))+cbclient.get_base_currency())
    accounts = cbclient.get_client().get_accounts()
    for acct in accounts:
      available = float(acct['available'])
      if available != 0 and cbclient.is_investing(cbclient.get_base_currency(),acct['currency']):
        dcaPrice = cbclient.get_dca_price(acct['currency'],available)
        value = available*dcaPrice
        print (acct['currency']+": "+acct['available']+" @ "+str(dcaPrice)+" = "+str(cbclient.round_fiat_currency(value))+" ("+str(round(100 * value / portfolioValue,2))+"%)")

logging.basicConfig(level=logging.WARNING)

float_formatter = "{:.2f}".format
np.set_printoptions(formatter={'float_kind':float_formatter})

cbclients = []
for filename in os.listdir("client_configs"):
  cbclients.append(cbpro_account("client_configs/"+filename))
main_func(cbclients)
if logging.getLogger().isEnabledFor(logging.INFO):
  print_portfolio(cbclients)
