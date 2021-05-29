import logging
import cbpro
from dotenv import get_key

class cbpro_account:
  def __init__(self,config_file,url="https://api.pro.coinbase.com"):
    self.config_file = config_file
    self.passphrase = get_key(config_file,'CB_PASSPHRASE')
    self.secret = get_key(config_file,'CB_SECRET')
    self.key = get_key(config_file, 'CB_KEY')
    self.base_currency = get_key(config_file, 'BASE_CURRENCY')
    self.buying_currency = get_key(config_file, 'BUYING_CURRENCY').split(',')
    self.selling_currency = get_key(config_file, 'SELLING_CURRENCY').split(',')
    self.url = url
    self.client = cbpro.AuthenticatedClient(self.key, self.secret, self.passphrase, api_url=self.url)
    self.account_ids = dict()
    accounts = self.client.get_accounts()
    for acct in accounts:
      self.account_ids[acct['currency']] = acct['id']
    self.dca_price_cache = dict()

  def get_config_file_name(self):
    return self.config_file

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

  def get_base_funds(self):
    return float(self.get_client().get_account(self.account_ids[self.base_currency])['available'])

  def round_fiat_currency(self, value):
    if self.base_currency == "USD" or self.base_currency == "EUR":
      return round(value,2)
    return value

  # Note: This is a memoized function
  def get_dca_price(self,currency,available):
    if available == 0:
      return 0

    cache_key = currency + str(available)
    if cache_key in self.dca_price_cache:
      return self.dca_price_cache[cache_key]

    fills = self.get_client().get_fills(product_id=currency+'-'+self.base_currency)
    cost = 0
    total_size = 0
    for fill in fills:
      if 'message' in fill:
        logging.error(self.config_file+": Can not get_fills("+currency+'-'+self.base_currency+')')
        break
      if total_size >= available:
        break
      if fill['side'] == "buy":
        logging.debug(self.config_file+": bought " + currency + ": " + fill['size'] + " @ " + fill['price'] + " + " + fill['fee'])
        curSize = float(fill['size'])
        if curSize > available - total_size:
          curSize = available - total_size
        cost = cost + float(fill['price']) * curSize + float(fill['fee'])
        total_size = total_size + curSize

    if total_size < available:
      logging.warning(self.config_file+": Unreliable price for "+currency+". Using $0.")
      self.dca_price_cache[cache_key] = 0
      return 0

    dca_price = self.round_fiat_currency(cost / total_size)
    logging.info(self.config_file+": Currency=" + currency + ". Cost=" + str(cost) + ". TotalSize=" + str(total_size) + ". Available=" + str(available) + ". DCAPrice=" + str(dca_price))
    self.dca_price_cache[cache_key] = dca_price
    return dca_price

  def get_current_price(self,product_id):
    return float(self.get_client().get_product_ticker(product_id=product_id)['bid'])

  def get_available(self,currency):
    return float(self.get_client().get_account(self.account_ids[currency])['available'])

  def get_investment_value(self):
    accounts = self.get_client().get_accounts()
    total = 0
    for acct in accounts:
      if float(acct['available']) != 0 and (acct['currency'] in self.buying_currency or acct['currency'] in self.selling_currency):
        dca_price = self.get_dca_price(acct['currency'],float(acct['available']))
        total = total + float(acct['available'])*dca_price
    return total

  def is_investing(self, base, currency):
    return base == self.base_currency and (currency in self.buying_currency or currency in self.selling_currency)

  def do_transaction(self, base, currency, action, allowTrades=False):
    if not self.is_investing(base, currency):
      logging.debug (self.config_file+": Not investing")
      return
    product_id = currency+'-'+self.base_currency
    if action == 'buy':
      if currency not in self.buying_currency:
        logging.debug (self.config_file+": Not buying")
        return
      baseFunds = self.get_base_funds()
      if baseFunds < 10: # Not enough to invest
        logging.debug (self.config_file+": Too poor")
        return
      available = self.get_available(currency)
      dca_price = self.get_dca_price(currency, available)
      portfolio_value = self.get_investment_value() + self.get_base_funds()
      if 100 * (available * dca_price) / portfolio_value > 2 * 100 / len(self.buying_currency): # No one product_id may be more than 20% of portfolio
        logging.debug (self.config_file+": Have too many")
        return
      current_price = self.get_current_price(product_id)
      if dca_price != 0 and current_price > dca_price: # Only buy if cheaper than before
        logging.debug (self.config_file+": Not good price")
        return
      amount = round(0.01 * baseFunds,2)
      if amount < 10: # Minimum amount
        amount = 10
      logging.info (self.config_file+": Buying "+str(amount)+self.base_currency+" of "+currency+" at "+str(current_price))
      if allowTrades == True:
        order = self.get_client().place_market_order(product_id=product_id,side='buy',funds=amount)
        logging.info(self.config_file+": "+str(order))
    elif action == 'sell':
      if currency not in self.selling_currency:
        logging.debug (self.config_file+": Not selling")
        return
      available = self.get_available(currency)
      if available == 0: # Has no money in it
        logging.debug (self.config_file+": None available to sell")
        return
      current_price = self.get_current_price(product_id)
      dca_price = self.get_dca_price(currency,available)
      if current_price <= dca_price*1.1: # Not Worthwhile selling (with fees)
        logging.debug (self.config_file+": Not Worthwhile")
        return
      logging.info (self.config_file+": Selling "+str(available)+" of "+currency+" at "+str(current_price)+" (dca="+str(dca_price)+"). Total: $"+str(current_price * available))
      if allowTrades == True:
        order = self.get_client().place_market_order(product_id=product_id,side='sell',size=available)
        logging.info(self.config_file+": "+str(order))