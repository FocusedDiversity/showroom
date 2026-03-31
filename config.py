import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://showroom:showroom@localhost:5432/showroom')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
STORAGE_BACKEND = os.environ.get('STORAGE_BACKEND', 'local')
GCS_BUCKET = os.environ.get('GCS_BUCKET', '')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload
