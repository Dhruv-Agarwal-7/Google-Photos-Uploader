import os
import time
import random
import typing
import requests
import mimetypes
from tqdm.auto import tqdm
from datetime import timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

# --- CONFIGURATION ---
MEDIA_DIR = '/content/drive/MyDrive/Videos'
SECRETS_PATH = '/content/drive/MyDrive/client_secrets.json'
UPLOADED_LOG_PATH = '/content/drive/MyDrive/uploaded_files.txt'
SHOW_ALL_OUTPUT = True  # Set to False to only see output of current file
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.appendonly']
UPLOAD_URL = 'https://photoslibrary.googleapis.com/v1/uploads'
SUPPORTED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.heif', '.avif', '.ico', '.tiff', '.raw',
    '.3gp', '.3g2', '.asf', '.avi', '.divx', '.m2t', '.m2ts', '.m4v', '.mkv', '.mmv', '.mod',
    '.mov', '.mp4', '.mpg', '.mts', '.tod', '.wmv'
}

def create_credentials(secrets_path: str, scopes: typing.List[str]) -> Credentials:
    path = os.path.splitext(secrets_path)[0]
    tokens_path = f'{path}-cached-token.json'
    credentials = None
    if os.path.exists(tokens_path):
        credentials = Credentials.from_authorized_user_file(tokens_path, scopes)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not os.path.exists(secrets_path):
                raise FileNotFoundError(f"client_secrets.json not found at {secrets_path}")
            flow = InstalledAppFlow.from_client_secrets_file(
                secrets_path, scopes, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            auth_url, _ = flow.authorization_url(prompt='consent')
            print("🔗 Visit this URL to authorize the app:\n" + auth_url)
            auth_code = input("🔐 Enter the authorization code: ")
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            with open(tokens_path, 'w') as token:
                token.write(credentials.to_json())
    return credentials

def create_photos_service(secrets_path: str) -> Resource:
    credentials = create_credentials(secrets_path, SCOPES)
    return build('photoslibrary', 'v1', credentials=credentials, static_discovery=False)

def load_uploaded_log(path: str) -> typing.Set[str]:
    if not os.path.exists(path):
        return set()
    with open(path, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def append_to_uploaded_log(path: str, file_path: str):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(file_path + '\n')

def format_eta(seconds_remaining):
    return str(timedelta(seconds=int(seconds_remaining)))

from IPython.display import clear_output

def upload_media_to_photos(service: Resource, file_path: str, credentials: Credentials, previous_file: str = None) -> bool:
    try:
        if credentials.expired and credentials.refresh_token:
            if SHOW_ALL_OUTPUT:
                print("🔁 Refreshing credentials...")
            credentials.refresh(Request())

        if SHOW_ALL_OUTPUT:
            if previous_file:
                print(f"✅ Previous upload: {previous_file}")
        else:
            clear_output(wait=True)
            if previous_file:
                print(f"✅ Previous upload: {previous_file}")
        print(f"📤 Starting upload: {file_path}")

        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False

        file_ext = os.path.splitext(file_path)[1].lower().strip()
        if file_ext not in SUPPORTED_EXTENSIONS:
            if SHOW_ALL_OUTPUT:
                print(f"⚠️ Unsupported file extension: {file_ext}")
            return False

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type or not (mime_type.startswith('image/') or mime_type.startswith('video/')):
            if SHOW_ALL_OUTPUT:
                print(f"⚠️ Unsupported MIME type: {mime_type}")
            return False

        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 ** 2)
        file_size_gb = file_size_mb / 1024

        if mime_type.startswith('image/') and file_size_mb > 200:
            print(f"⚠️ Skipping image: {file_path} exceeds 200 MB limit ({file_size_mb:.2f} MB)")
            return False

        if mime_type.startswith('video/') and file_size_gb > 20:
            print(f"⚠️ Skipping video: {file_path} exceeds 20 GB limit ({file_size_gb:.2f} GB)")
            return False

        if SHOW_ALL_OUTPUT:
            print(f"⬆️  Uploading file ({file_size_mb:.2f} MB)...")

        headers = {
            'Authorization': f'Bearer {credentials.token}',
            'Content-Type': 'application/octet-stream',
            'X-Goog-Upload-File-Name': os.path.basename(file_path),
            'X-Goog-Upload-Protocol': 'raw'
        }

        with open(file_path, 'rb') as f:
            progress = tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024,
                            desc=os.path.basename(file_path), leave=True)

            def callback(current):
                progress.update(current - progress.n)

            class FileReader:
                def __init__(self, f):
                    self.f = f
                    self.bytes_read = 0
                def read(self, size=-1):
                    chunk = self.f.read(size)
                    if chunk:
                        self.bytes_read += len(chunk)
                        callback(self.bytes_read)
                    return chunk
                def __len__(self):
                    return file_size

            monitored = FileReader(f)
            response = requests.post(UPLOAD_URL, headers=headers, data=monitored)
            progress.close()

        if response.status_code == 429:
            print(f"🚫 Skipping file due to 429 Too Many Requests: {file_path}")
            return False
        elif response.status_code != 200:
            print(f"❌ Upload failed: {response.text}")
            return False

        upload_token = response.text
        if not upload_token:
            print(f"❌ Upload token not received for: {file_path}")
            return False

        if SHOW_ALL_OUTPUT:
            print("🧠 Finalizing upload (batchCreate)...")
        request_body = {
            'newMediaItems': [{
                'simpleMediaItem': {
                    'fileName': os.path.basename(file_path),
                    'uploadToken': upload_token
                }
            }]
        }

        try:
            response = service.mediaItems().batchCreate(body=request_body).execute()
        except HttpError as e:
            if e.resp.status == 429:
                print(f"🚫 Skipping file : batchCreate quota exceeded: {file_path}")
                return False
            else:
                raise

        results = response.get('newMediaItemResults', [])
        status = results[0].get('status', {})
        code = status.get('code')
        message = status.get('message', '')

        if code == 0 or (code is None and message.lower() == 'success'):
            if SHOW_ALL_OUTPUT:
                print(f"✅ Successfully uploaded: {file_path}")
            append_to_uploaded_log(UPLOADED_LOG_PATH, file_path)
            return True
        else:
            print(f"❌ Failed to create media item: {file_path} [Code: {code}] {message}")
            return False

    except HttpError as e:
        print(f"❌ HttpError for {file_path}: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error for {file_path}: {str(e)}")
        return False

def main():
    try:
        credentials = create_credentials(SECRETS_PATH, SCOPES)
        service = create_photos_service(SECRETS_PATH)
    except Exception as e:
        print(f"❌ Initialization error: {str(e)}")
        return

    if not os.path.exists(MEDIA_DIR):
        print(f"❌ Directory not found: {MEDIA_DIR}")
        return

    uploaded_log = load_uploaded_log(UPLOADED_LOG_PATH)

    media_files = []
    for root, _, files in os.walk(MEDIA_DIR):
        for f in files:
            full_path = os.path.join(root, f)
            if full_path not in uploaded_log:
                media_files.append(full_path)

    if not media_files:
        print(f"📭 No new media files found in {MEDIA_DIR}")
        return

    media_files.sort()
    print(f"📁 Found {len(media_files)} media files to upload. Beginning upload...\n")

    success_count = 0
    prev_file = None
    total_files = len(media_files)
    start_time = time.time()

    for idx, file_path in enumerate(media_files):
        time.sleep(2)
        elapsed = time.time() - start_time
        if idx > 0:
            avg_time = elapsed / idx
            remaining = total_files - idx
            eta = format_eta(avg_time * remaining)
            print(f"⏳ ETA: {eta} remaining ({remaining} files left)")

        success = upload_media_to_photos(service, file_path, credentials, prev_file)
        if success:
            success_count += 1
            prev_file = file_path

    print(f"\n📊 Upload Summary: {success_count}/{len(media_files)} uploaded successfully ({(success_count / len(media_files)) * 100:.2f}%)")

if __name__ == '__main__':
    main()
