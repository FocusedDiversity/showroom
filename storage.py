import os
import shutil
import tempfile
import zipfile
import mimetypes
from abc import ABC, abstractmethod
from flask import Response, send_from_directory
from config import STORAGE_BACKEND, UPLOAD_FOLDER, GCS_BUCKET


class Storage(ABC):
    @abstractmethod
    def save_file(self, slug, relative_path, data):
        """Save file data (bytes) to storage."""

    @abstractmethod
    def file_exists(self, slug, relative_path):
        """Check if a file exists."""

    @abstractmethod
    def read_file(self, slug, relative_path):
        """Read file content as text."""

    @abstractmethod
    def serve_file(self, slug, relative_path):
        """Return a Flask Response for the file."""

    @abstractmethod
    def delete_deck(self, slug):
        """Delete all files for a deck."""

    @abstractmethod
    def extract_zip(self, slug, zip_bytes):
        """Extract a zip archive into the deck's storage."""

    @abstractmethod
    def list_files(self, slug):
        """List all relative file paths for a deck."""


class LocalStorage(Storage):
    def __init__(self, base_dir):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def _deck_dir(self, slug):
        return os.path.join(self.base_dir, slug)

    def save_file(self, slug, relative_path, data):
        deck_dir = self._deck_dir(slug)
        full_path = os.path.join(deck_dir, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'wb') as f:
            f.write(data)

    def file_exists(self, slug, relative_path):
        return os.path.exists(os.path.join(self._deck_dir(slug), relative_path))

    def read_file(self, slug, relative_path):
        path = os.path.join(self._deck_dir(slug), relative_path)
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

    def serve_file(self, slug, relative_path):
        return send_from_directory(self._deck_dir(slug), relative_path)

    def delete_deck(self, slug):
        shutil.rmtree(self._deck_dir(slug), ignore_errors=True)

    def extract_zip(self, slug, zip_bytes):
        deck_dir = self._deck_dir(slug)
        os.makedirs(deck_dir, exist_ok=True)
        tmp = os.path.join(deck_dir, 'upload.zip')
        with open(tmp, 'wb') as f:
            f.write(zip_bytes)
        with zipfile.ZipFile(tmp, 'r') as zf:
            for member in zf.namelist():
                if member.startswith('/') or '..' in member:
                    os.remove(tmp)
                    raise ValueError(f'Unsafe path in zip: {member}')
            zf.extractall(deck_dir)
        os.remove(tmp)

    def list_files(self, slug):
        deck_dir = self._deck_dir(slug)
        result = []
        for root, dirs, files in os.walk(deck_dir):
            for fname in files:
                full = os.path.join(root, fname)
                result.append(os.path.relpath(full, deck_dir))
        return result


class GCSStorage(Storage):
    def __init__(self, bucket_name):
        from google.cloud import storage as gcs
        self.client = gcs.Client()
        self.bucket = self.client.bucket(bucket_name)

    def _prefix(self, slug, relative_path=''):
        if relative_path:
            return f'{slug}/{relative_path}'
        return f'{slug}/'

    def save_file(self, slug, relative_path, data):
        blob = self.bucket.blob(self._prefix(slug, relative_path))
        blob.upload_from_string(data)

    def file_exists(self, slug, relative_path):
        return self.bucket.blob(self._prefix(slug, relative_path)).exists()

    def read_file(self, slug, relative_path):
        blob = self.bucket.blob(self._prefix(slug, relative_path))
        return blob.download_as_text(encoding='utf-8')

    def serve_file(self, slug, relative_path):
        blob = self.bucket.blob(self._prefix(slug, relative_path))
        data = blob.download_as_bytes()
        content_type = mimetypes.guess_type(relative_path)[0] or 'application/octet-stream'
        return Response(data, mimetype=content_type)

    def delete_deck(self, slug):
        blobs = list(self.bucket.list_blobs(prefix=self._prefix(slug)))
        for blob in blobs:
            blob.delete()

    def extract_zip(self, slug, zip_bytes):
        tmp_dir = tempfile.mkdtemp()
        try:
            tmp_zip = os.path.join(tmp_dir, 'upload.zip')
            with open(tmp_zip, 'wb') as f:
                f.write(zip_bytes)
            with zipfile.ZipFile(tmp_zip, 'r') as zf:
                for member in zf.namelist():
                    if member.startswith('/') or '..' in member:
                        raise ValueError(f'Unsafe path in zip: {member}')
                zf.extractall(tmp_dir)
            os.remove(tmp_zip)
            # Upload extracted files to GCS
            for root, dirs, files in os.walk(tmp_dir):
                for fname in files:
                    full = os.path.join(root, fname)
                    rel = os.path.relpath(full, tmp_dir)
                    with open(full, 'rb') as fh:
                        self.save_file(slug, rel, fh.read())
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def list_files(self, slug):
        prefix = self._prefix(slug)
        blobs = self.bucket.list_blobs(prefix=prefix)
        return [blob.name[len(prefix):] for blob in blobs if blob.name != prefix]


def get_storage():
    if STORAGE_BACKEND == 'gcs':
        return GCSStorage(GCS_BUCKET)
    return LocalStorage(UPLOAD_FOLDER)
