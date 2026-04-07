"""
Collage Manager — manages collage library and Recraft.ai integration.

Stores collage images via the existing storage abstraction under a
'_collages' slug prefix. Metadata tracked in the collages DB table.
"""

import base64
import os
import mimetypes
import json
import requests
from config import BASE_DIR

RECRAFT_API_KEY = os.environ.get('RECRAFT_API_KEY', '')
RECRAFT_API_URL = 'https://external.api.recraft.ai/v1/images/generations'
COLLAGE_SLUG = '_collages'
MAX_COLLAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def list_collages(db, tags=None):
    """List collages, optionally filtered by tags."""
    if tags:
        rows = db.execute(
            'SELECT * FROM collages WHERE tags && %s ORDER BY created_at DESC',
            (tags,)
        ).fetchall()
    else:
        rows = db.execute(
            'SELECT * FROM collages ORDER BY created_at DESC'
        ).fetchall()
    return rows


def get_collage(db, collage_id):
    """Get a single collage by ID."""
    return db.execute(
        'SELECT * FROM collages WHERE id = %s', (collage_id,)
    ).fetchone()


def upload_collage(db, storage, name, file_data, filename, tags=None):
    """Upload a collage image.

    Args:
        db: Database connection
        storage: Storage abstraction instance
        name: Display name for the collage
        file_data: Raw bytes of the image
        filename: Original filename (for extension)
        tags: Optional list of tag strings

    Returns:
        dict: The created collage row

    Raises:
        ValueError: If file is too large or wrong format
    """
    if not _allowed_file(filename):
        raise ValueError(f'File type not allowed. Use: {", ".join(ALLOWED_EXTENSIONS)}')

    if len(file_data) > MAX_COLLAGE_SIZE:
        raise ValueError(f'File too large. Max {MAX_COLLAGE_SIZE // (1024*1024)}MB.')

    ext = filename.rsplit('.', 1)[1].lower()

    # Insert into DB to get ID
    row = db.execute(
        """INSERT INTO collages (name, tags, storage_path, source)
           VALUES (%s, %s, %s, 'upload')
           RETURNING *""",
        (name, tags or [], f'placeholder')
    ).fetchone()
    db.commit()

    collage_id = row['id']
    storage_path = f'{collage_id}.{ext}'

    # Store the file
    storage.save_file(COLLAGE_SLUG, storage_path, file_data)

    # Update storage path
    db.execute(
        'UPDATE collages SET storage_path = %s WHERE id = %s',
        (storage_path, collage_id)
    )
    db.commit()

    return get_collage(db, collage_id)


def get_collage_data_uri(storage, collage):
    """Get a collage as a base64 data URI for embedding in HTML."""
    if not collage:
        return ''

    path = collage['storage_path']
    ext = path.rsplit('.', 1)[1].lower() if '.' in path else 'png'
    mime = mimetypes.guess_type(f'file.{ext}')[0] or 'image/png'

    try:
        # Read raw bytes from storage
        if hasattr(storage, '_deck_dir'):
            # LocalStorage
            full_path = os.path.join(storage._deck_dir(COLLAGE_SLUG), path)
            with open(full_path, 'rb') as f:
                data = f.read()
        else:
            # GCS — read_file returns text, need bytes
            blob = storage.bucket.blob(storage._prefix(COLLAGE_SLUG, path))
            data = blob.download_as_bytes()

        b64 = base64.b64encode(data).decode('ascii')
        return f'data:{mime};base64,{b64}'
    except Exception:
        return ''


def generate_collage_recraft(prompt, style_preset='digital_illustration'):
    """Generate collage images using Recraft.ai API.

    Args:
        prompt: Text description of the desired collage
        style_preset: Recraft style preset

    Returns:
        list[dict]: List of generated images with 'url' and 'b64' keys

    Raises:
        ValueError: If API key not configured
        RuntimeError: If API request fails
    """
    if not RECRAFT_API_KEY:
        raise ValueError('RECRAFT_API_KEY environment variable not set')

    headers = {
        'Authorization': f'Bearer {RECRAFT_API_KEY}',
        'Content-Type': 'application/json',
    }

    payload = {
        'prompt': prompt,
        'style': style_preset,
        'size': '1280x720',
        'n': 2,
    }

    try:
        resp = requests.post(RECRAFT_API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get('data', []):
            results.append({
                'url': item.get('url', ''),
                'b64': item.get('b64_json', ''),
            })
        return results

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f'Recraft.ai API error: {e}')


def save_generated_collage(db, storage, name, image_data, prompt, tags=None):
    """Save a generated collage image from Recraft.ai to the library.

    Args:
        db: Database connection
        storage: Storage abstraction
        name: Display name
        image_data: Raw image bytes
        prompt: The prompt used to generate it
        tags: Optional tag list

    Returns:
        dict: Created collage row
    """
    row = db.execute(
        """INSERT INTO collages (name, tags, storage_path, source, recraft_prompt)
           VALUES (%s, %s, %s, 'recraft', %s)
           RETURNING *""",
        (name, tags or [], 'placeholder', prompt)
    ).fetchone()
    db.commit()

    collage_id = row['id']
    storage_path = f'{collage_id}.png'

    storage.save_file(COLLAGE_SLUG, storage_path, image_data)

    db.execute(
        'UPDATE collages SET storage_path = %s WHERE id = %s',
        (storage_path, collage_id)
    )
    db.commit()

    return get_collage(db, collage_id)
