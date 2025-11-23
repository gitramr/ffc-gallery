import os
import requests
from github import Auth, Github

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
GH_PAT = os.getenv("GH_PAT")   # use your PAT here
REPO_NAME = "gitkailas/infinite-gallery"
IMAGE_DIR = "images"

def get_file_url(file_id):
    file_info = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}"
    ).json()
    file_path = file_info["result"]["file_path"]
    return f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"

def fetch_images():
    updates = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    ).json()["result"]

    auth = Auth.Token(GH_PAT)
    g = Github(auth=auth)
    repo = g.get_repo(REPO_NAME)

    existing_files = [f.name for f in repo.get_contents(IMAGE_DIR)]
    next_index = len(existing_files) + 1

    for update in updates:
        msg = update.get("message", {})
        if "photo" in msg:
            photo = msg["photo"][-1]
            file_id = photo["file_id"]
            file_url = get_file_url(file_id)
            image_bytes = requests.get(file_url).content

            filename = f"image{next_index:05d}.jpg"
            path = f"{IMAGE_DIR}/{filename}"

            if filename not in existing_files:
                try:
                    repo.create_file(path, f"Add {filename}", image_bytes)
                    print(f"✅ Uploaded {filename}")
                    next_index += 1
                except Exception as e:
                    print(f"⚠️ Failed to upload {filename}: {e}")

if __name__ == "__main__":
    fetch_images()