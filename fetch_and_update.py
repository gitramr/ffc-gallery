import os
import re
import json
import hashlib
import requests
from github import Auth, Github
from github.GithubException import UnknownObjectException

# Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
GH_PAT = os.getenv("GH_PAT")

# Repo details
REPO_NAME = "gitkailas/infinite-gallery"
IMAGE_DIR = "images"
MANIFEST_FILE = "manifest.js"
STATE_DIR = ".state"
HASHES_FILE = f"{STATE_DIR}/image_hashes.json"
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def natural_sort_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def get_file_url(file_id):
    file_info = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile",
        params={"file_id": file_id},
        timeout=30,
    ).json()
    file_path = file_info["result"]["file_path"]
    return f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"

def ensure_dir_exists(repo, path):
    try:
        repo.get_contents(path)
    except UnknownObjectException:
        repo.create_file(f"{path}/.gitkeep", f"Create {path} folder", "")
        print(f"ℹ️ Created {path} folder")

def read_repo_json(repo, path):
    try:
        contents = repo.get_contents(path)
        return json.loads(contents.decoded_content.decode("utf-8")), contents.sha
    except Exception:
        return {}, None

def write_repo_text(repo, path, text, sha=None, message="Update file"):
    if sha:
        repo.update_file(path, message, text, sha)
    else:
        repo.create_file(path, message, text)

def get_images_list(repo):
    items = repo.get_contents(IMAGE_DIR)
    names = [i.name for i in items if os.path.splitext(i.name)[1].lower() in VALID_EXTENSIONS]
    return sorted(names, key=natural_sort_key, reverse=True)

def fetch_and_update():
    # Auth to GitHub
    auth = Auth.Token(GH_PAT)
    g = Github(auth=auth)
    repo = g.get_repo(REPO_NAME)

    ensure_dir_exists(repo, IMAGE_DIR)
    ensure_dir_exists(repo, STATE_DIR)

    # Load hash registry
    hashes, hashes_sha = read_repo_json(repo, HASHES_FILE)

    # 1. Fetch all messages from Telegram channel
    updates = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
        timeout=30,
    ).json().get("result", [])

    # Collect current Telegram images
    telegram_hashes = {}
    for update in updates:
        msg = update.get("message", {})
        if "photo" in msg:
            photo = msg["photo"][-1]
            file_id = photo["file_id"]
            file_url = get_file_url(file_id)
            image_bytes = requests.get(file_url, timeout=60).content
            content_hash = sha256_bytes(image_bytes)
            telegram_hashes[content_hash] = image_bytes

    # 2. Delete repo images not in Telegram
    repo_files = repo.get_contents(IMAGE_DIR)
    for f in repo_files:
        if f.name.endswith(tuple(VALID_EXTENSIONS)):
            # If hash not in telegram_hashes, delete
            file_bytes = f.decoded_content
            file_hash = sha256_bytes(file_bytes)
            if file_hash not in telegram_hashes:
                repo.delete_file(f.path, f"Remove {f.name}", f.sha)
                print(f"🗑️ Deleted {f.name} (not in Telegram)")

    # 3. Add new Telegram images not in repo
    existing_files = [f.name for f in repo.get_contents(IMAGE_DIR)]
    next_index = len(existing_files) + 1
    for h, img_bytes in telegram_hashes.items():
        if h not in hashes:
            filename = f"image{next_index:05d}.jpg"
            path = f"{IMAGE_DIR}/{filename}"
            repo.create_file(path, f"Add {filename}", img_bytes)
            hashes[h] = filename
            print(f"✅ Uploaded {filename}")
            next_index += 1

    # 4. Persist hash registry
    write_repo_text(
        repo, HASHES_FILE, json.dumps(hashes, indent=2),
        sha=hashes_sha,
        message="Update image hash registry"
    )

    # 5. Build manifest
    images = get_images_list(repo)
    manifest_content = "const manifest = [\n"
    for img in images:
        manifest_content += f'  "{img}",\n'
    manifest_content += "];\n"

    manifest_text = None
    manifest_sha = None
    try:
        contents = repo.get_contents(MANIFEST_FILE)
        manifest_text = contents.decoded_content.decode("utf-8")
        manifest_sha = contents.sha
    except Exception:
        pass

    write_repo_text(
        repo, MANIFEST_FILE, manifest_content,
        sha=manifest_sha,
        message="Update manifest"
    )
    print(f"✅ {MANIFEST_FILE} updated with {len(images)} images.")

if __name__ == "__main__":
    fetch_and_update()