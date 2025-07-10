# 📷 Google Photos Uploader

Upload media files from your Google Drive to your Google Photos account using the Photos Library API.

---

## 🚀 Features

- ✅ Supports **images and videos** with many common formats
- 📂 Recursively scans nested folders
- 📌 Skips already uploaded files (based on log)
- 🔁 Skips oversized files (Photos > 200MB, Videos > 20GB)
- 📈 Shows per-file upload progress and ETA
- 🔐 OAuth2 authentication with persistent token cache
- ⚠️ Gracefully skips 429 rate-limiting errors

---

## 📦 Setup Instructions

### 1. 🔐 Create Google API Credentials

- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Enable **Photos Library API**
- Add `./auth/photoslibrary` scope under Data Access
- Add your email id as a test user and make sure the app is external
- Create an OAuth2 **Desktop App** credential
- Download `client_secrets.json` and place it in the root directory of your drive

### 2. 🛠 Environment (Colab or Local Python)

**Google Colab**:
- Just upload the script and run it. All required packages are pre-installed.

## 🧾 Configuration
Edit the top of the script:
```
MEDIA_DIR = '/content/drive/MyDrive/Videos'  # Path to your media directory
SECRETS_PATH = '/content/drive/MyDrive/client_secrets.json'
SHOW_ALL_OUTPUT = False  # Toggle full vs minimal logging
```

## 🔮 Future Scope
🗂️ Auto-create albums based on subfolders

📅 Sort and upload by creation date

🔄 Resume with hash-based deduplication

☁️ Google Drive-to-Photos syncing
