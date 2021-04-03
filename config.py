import os

# Read key parameters from .env file
from pathlib import Path  # Python 3.6+ only
from dotenv import load_dotenv
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Coinbase Credentials
CB_CREDENTIALS = {
    'PASSPHRASE': os.environ['CB_PASSPHRASE'],
    'SECRET': os.environ['CB_SECRET'],
    'KEY': os.environ['CB_KEY'],
    'URL': os.environ['CB_URL']
}
