import os
from decouple import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONGODB_KEY = config('MONGODB_KEY')
FRONTEND_URL = config('FRONTEND_URL')
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID')

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
