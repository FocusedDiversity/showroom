import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'showroom.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload
