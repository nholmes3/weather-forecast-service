import os


class Config:
    FLASK_RUN_PORT = 8000
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    TOMORROW_API_BASE_URL = os.environ.get('TOMORROW_API_BASE_URL', 'https://api.tomorrow.io/v4')
    TOMORROW_API_KEY = os.environ.get('TOMORROW_API_KEY')
