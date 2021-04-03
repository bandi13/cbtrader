import cbpro

GLOBAL_CLIENT = None

def get_client():
    """Returns the cbpro AuthenticatedClient using the credentials from the parameters dict"""
    global GLOBAL_CLIENT

    if GLOBAL_CLIENT is None:
        from config import CB_CREDENTIALS
        GLOBAL_CLIENT = cbpro.AuthenticatedClient(CB_CREDENTIALS['KEY'], CB_CREDENTIALS['SECRET'], CB_CREDENTIALS['PASSPHRASE'], api_url=CB_CREDENTIALS['URL'])

    return GLOBAL_CLIENT

def cbpro_client(func):
    def function_wrapper(*args, **kwargs):
        cbpro_client = get_client()
        resp = func(cbpro_client = cbpro_client, *args, **kwargs)

        return resp

    return function_wrapper
