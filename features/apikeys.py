import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

GEMINIAI_API_KEY = os.getenv('GEMINIAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ID = os.getenv('SEARCH_ID')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
DATABASE_API = os.getenv('DATABASE_API', '')
