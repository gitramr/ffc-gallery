import os
import re
import requests
from github import Auth, Github

# Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
GH_PAT = os.getenv("GH_PAT")

# Repo details
REPO_NAME = "gitkailas/infinite-gallery"
IMAGE_DIR = "images"
MANIFEST_FILE = "manifest.js"
OFFSET_FILE = "last_update_id.txt"
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def get_last_offset():
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE, "r") as f:
            return int(f.read().strip())
    return None

def save_last_offset(update_id):
    with open(OFFSET_FILE, "w") as f:
        f.write(str(update_id))

def get_file_url(file_id):
    file_info = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}"
    ).json()
    file_path = file_info["result"]["file_path"]
    return f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

def fetch_and_update():
    # Auth to GitHub
    auth = Auth.Token(GH_PAT)
    g = Github(auth=auth)
    repo = g.get_repo(REPO_NAME)

    # Handle Telegram updates
    last_offset = get_last_offset()
    params = {}
    if last_offset:
        params["offset"] = last_offset + 1

    updates = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates", params=params
    ).json()["result"]

    if not updates:
        print("ℹ️ No new updates.")
    else:
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

            save_last_offset(update["update_id"])

    # Build manifest from repo contents
    files = repo.get_contents(IMAGE_DIR)
    images = [f.name for f in files if os.path.splitext(f.name)[1].lower() in VALID_EXTENSIONS]
    images = sorted(images, key=natural_sort_key, reverse=True)

    manifest_content = "const manifest = [\n"
    for img in images:
        manifest_content += f'  "{img}",\n'   # ✅ only filename
    manifest_content += "];\n"

    try:
        contents = repo.get_contents(MANIFEST_FILE)
        repo.update_file(contents.path, "Update manifest", manifest_content, contents.sha)
        print(f"✅ {MANIFEST_FILE} updated with {len(images)} images.")
    except Exception:
        repo.create_file(MANIFEST_FILE, "Create manifest", manifest_content)
        print(f"✅ {MANIFEST_FILE} created with {len(images)} images.")

if __name__ == "__main__":
    fetch_and_update()