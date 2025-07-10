# 📷 Google Photos Uploader

Upload media files from your **Google Drive (using colab)** or **local directory** to your **Google Photos** account using the Photos Library API.

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
- Set the app type as **External** and add your Google email as a test user under Audience tab
- Create an OAuth2 **Desktop App** credential
- Download `client_secrets.json` and place it in the root directory

### 2. 🧾 Configuration
Edit the top of the script:
```python
MEDIA_DIR = '/content/drive/MyDrive/Videos'  # Path to your media directory
SECRETS_PATH = '/content/drive/MyDrive/client_secrets.json'
SHOW_ALL_OUTPUT = False  # Toggle full vs minimal logging
```

### 3. 🛠 Usage (Colab or Local Python)

**Google Colab** :
- Just open this notebook and execute all cells.
- All required packages are pre-installed.
  
<a href="https://colab.research.google.com/github/Dhruv-Agarwal-7/Google-Photos-Uploader/blob/master/Google_Photos_Uploader.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

**Local** (optional) :
```bash
pip install -r requirements.txt
python google_photos_uploader.py
```

---

## 📊 Output Summary
- Progress of current file shown (if `SHOW_ALL_OUTPUT = False`)
- ETA displayed based on average upload time
- Final summary of how many files succeeded

## 🔮 Future Scope
🗂️ Auto-create albums based on subfolders

📅 Sort and upload by creation date

🔄 Resume with hash-based deduplication

☁️ Google Drive-to-Photos syncing

---

## 🙌 Author
Built by Dhruv Agarwal with ❤️ for power users of Google Photos.
