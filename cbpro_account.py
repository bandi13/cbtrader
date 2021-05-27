import logging
import cbpro
from dotenv import get_key

class cbpro_account:
  def __init__(self,keysfile,url="https://api.pro.coinbase.com"):
    self.keysfile = keysfile
    self.passphrase = get_key(keysfile,'CB_PASSPHRASE')
    self.secret = get_key(keysfile,'CB_SECRET')
    self.key = get_key(keysfile, 'CB_KEY')
    self.base_currency = get_key(keysfile, 'BASE_CURRENCY')
    self.buying_currency = get_key(keysfile, 'BUYING_CURRENCY').split(',')
    self.selling_currency = get_key(keysfile, 'SELLING_CURRENCY').split(',')
    self.url = url
    self.client = cbpro.AuthenticatedClient(self.key, self.secret, self.passphrase, api_url=self.url)
    self.account_ids = dict()
    accounts = self.client.get_accounts()
    for acct in accounts:
      self.account_ids[acct['currency']] = acct['id']
    self.dca_price_cache = dict()

  def get_keysfile(self):
    return self.keysfile

  def get_client(self):
    return self.client

  def get_base_currency(self):
    return self.base_currency

  def get_product_ids(self):
    ret = []

    for currency in self.buying_currency:
      ret.append(currency+'-'+self.base_currency)

    for currency in self.selling_currency:
      ret.append(currency+'-'+self.base_currency)

    return sorted(set(ret)) # return unique set

  def getBaseFunds(self):
    return float(self.get_client().get_account(self.account_ids[self.base_currency])['available'])

  def roundFiatCurrency(self, value):
    if self.base_currency == "USD" or self.base_currency == "EUR":
      return round(value,2)
    return value

  def getDCAPrice(self,currency,available):
    if available == 0:
      return 0

    cache_key = currency + str(available)
    if cache_key in self.dca_price_cache:
      return self.dca_price_cache[cache_key]

    fills = self.get_client().get_fills(product_id=currency+'-'+self.base_currency)
    cost = 0
    totalSize = 0
    for fill in fills:
      if 'message' in fill:
        logging.error("Can not get_fills("+currency+'-'+self.base_currency+')')
        break
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
      self.dca_price_cache[cache_key] = 0
      return 0

    dcaPrice = self.roundFiatCurrency(cost / totalSize)
    logging.info("Currency=" + currency + ". Cost=" + str(cost) + ". TotalSize=" + str(totalSize) + ". Available=" + str(available) + ". DCAPrice=" + str(dcaPrice))
    self.dca_price_cache[cache_key] = dcaPrice
    return dcaPrice

  def getCurPrice(self,product_id):
    return float(self.get_client().get_product_ticker(product_id=product_id)['bid'])

  def getAvailable(self,currency):
    return float(self.get_client().get_account(self.account_ids[currency])['available'])

  def getInvestmentValue(self):
    accounts = self.get_client().get_accounts()
    total = 0
    for acct in accounts:
      if float(acct['available']) != 0 and (acct['currency'] in self.buying_currency or acct['currency'] in self.selling_currency):
        dcaPrice = self.getDCAPrice(acct['currency'],float(acct['available']))
        total = total + float(acct['available'])*dcaPrice
    return total

  def isInvesting(self, base, currency):
    return base == self.base_currency and (currency in self.buying_currency or currency in self.selling_currency)

  def doTransaction(self, base, currency, action, allowTrades=False):
    if not self.isInvesting(base, currency):
      logging.debug ("Not investing")
      return
    product_id = currency+'-'+self.base_currency
    if action == 'buy':
      if currency not in self.buying_currency:
        logging.debug ("Not buying")
        return
      baseFunds = self.getBaseFunds()
      if baseFunds < 10: # Not enough to invest
        logging.debug ("Too poor")
        return
      available = self.getAvailable(currency)
      dcaPrice = self.getDCAPrice(currency, available)
      portfolioValue = self.getInvestmentValue() + self.getBaseFunds()
      if 100 * (available * dcaPrice) / portfolioValue > 2 * 100 / len(self.buying_currency): # No one product_id may be more than 2x any other product_id
        logging.debug ("Have too many")
        return
      curPrice = self.getCurPrice(product_id)
      if dcaPrice != 0 and curPrice > dcaPrice: # Only buy if cheaper than before
        logging.debug ("Not good price")
        return
      amount = round(0.01 * baseFunds,2)
      if amount < 10: # Minimum amount
        amount = 10
      print ("Buying "+str(amount)+self.base_currency+" of "+currency+" at "+str(curPrice))
      if allowTrades == True:
        print (self.get_client().place_market_order(product_id=product_id,side='buy',funds=amount))
    elif action == 'sell':
      if currency not in self.selling_currency:
        logging.debug ("Not selling")
        return
      available = self.getAvailable(currency)
      if available == 0: # Has no money in it
        logging.debug ("None available to sell")
        return
      curPrice = self.getCurPrice(product_id)
      dcaPrice = self.getDCAPrice(currency,available)
      if curPrice <= dcaPrice*1.1: # Not Worthwhile selling (with fees)
        logging.debug ("Not Worthwhile")
        return
      print ("Selling "+str(available)+" of "+currency+" at "+str(curPrice)+" (dca="+str(dcaPrice)+"). Total: $"+str(curPrice * available))
      if allowTrades == True:
        print (self.get_client().place_market_order(product_id=product_id,side='sell',size=available))