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
OFFSET_FILE = f"{STATE_DIR}/last_update_id.txt"
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
        # Create placeholder so GitHub tracks the directory
        repo.create_file(f"{path}/.gitkeep", f"Create {path} folder", "")
        print(f"ℹ️ Created {path} folder")

def read_repo_text(repo, path):
    try:
        contents = repo.get_contents(path)
        return contents.decoded_content.decode("utf-8"), contents.sha
    except UnknownObjectException:
        return None, None

def write_repo_text(repo, path, text, sha=None, message="Update file"):
    if sha:
        repo.update_file(path, message, text, sha)
    else:
        repo.create_file(path, message, text)

def read_repo_json(repo, path):
    text, sha = read_repo_text(repo, path)
    if text is None:
        return {}, None
    try:
        return json.loads(text), sha
    except json.JSONDecodeError:
        return {}, sha

def get_images_list(repo):
    items = repo.get_contents(IMAGE_DIR)
    names = [i.name for i in items if os.path.splitext(i.name)[1].lower() in VALID_EXTENSIONS]
    return sorted(names, key=natural_sort_key, reverse=True)

def get_next_index(repo):
    items = repo.get_contents(IMAGE_DIR)
    nums = []
    for i in items:
        name, ext = os.path.splitext(i.name)
        if ext.lower() in VALID_EXTENSIONS and name.startswith("image"):
            try:
                nums.append(int(name.replace("image", "")))
            except ValueError:
                pass
    return (max(nums) + 1) if nums else 1

def fetch_and_update():
    # Auth to GitHub
    auth = Auth.Token(GH_PAT)
    g = Github(auth=auth)
    repo = g.get_repo(REPO_NAME)

    # Ensure directories exist
    ensure_dir_exists(repo, IMAGE_DIR)
    ensure_dir_exists(repo, STATE_DIR)

    # Offset persistence in repo
    last_offset_text, last_offset_sha = read_repo_text(repo, OFFSET_FILE)
    last_offset = int(last_offset_text) if last_offset_text else None

    # Hash registry persistence
    hashes, hashes_sha = read_repo_json(repo, HASHES_FILE)

    # Telegram updates
    params = {}
    if last_offset is not None:
        params["offset"] = last_offset + 1

    updates = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
        params=params,
        timeout=30,
    ).json().get("result", [])

    if not updates:
        print("ℹ️ No new updates.")
    else:
        existing_names = [f.name for f in repo.get_contents(IMAGE_DIR)]
        next_index = get_next_index(repo)

        for update in updates:
            msg = update.get("message", {})
            if "photo" in msg:
                # Largest size
                photo = msg["photo"][-1]
                file_id = photo["file_id"]
                file_url = get_file_url(file_id)
                image_bytes = requests.get(file_url, timeout=60).content
                content_hash = sha256_bytes(image_bytes)

                # Skip if we've seen this content before
                if content_hash in hashes:
                    print(f"↩️ Duplicate content detected, skipping {hashes[content_hash]}")
                else:
                    filename = f"image{next_index:05d}.jpg"
                    path = f"{IMAGE_DIR}/{filename}"

                    # Avoid accidental name collision
                    if filename in existing_names:
                        next_index = get_next_index(repo)
                        filename = f"image{next_index:05d}.jpg"
                        path = f"{IMAGE_DIR}/{filename}"

                    try:
                        repo.create_file(path, f"Add {filename}", image_bytes)
                        hashes[content_hash] = filename
                        print(f"✅ Uploaded {filename}")
                        next_index += 1
                        # refresh existing names cache lightly
                        existing_names.append(filename)
                    except Exception as e:
                        print(f"⚠️ Failed to upload {filename}: {e}")

            # Advance offset to the latest processed update_id
            last_offset = update["update_id"]

        # Persist new offset and hashes
        write_repo_text(
            repo, OFFSET_FILE, str(last_offset),
            sha=last_offset_sha,
            message="Advance Telegram offset"
        )
        write_repo_text(
            repo, HASHES_FILE, json.dumps(hashes, indent=2),
            sha=hashes_sha,
            message="Update image hash registry"
        )

    # Build manifest with filenames only
    images = get_images_list(repo)
    manifest_content = "const manifest = [\n"
    for img in images:
        manifest_content += f'  "{img}",\n'
    manifest_content += "];\n"

    # Write manifest
    manifest_text, manifest_sha = read_repo_text(repo, MANIFEST_FILE)
    write_repo_text(
        repo, MANIFEST_FILE, manifest_content,
        sha=manifest_sha,
        message="Update manifest"
    )
    print(f"✅ {MANIFEST_FILE} updated with {len(images)} images.")

if __name__ == "__main__":
    fetch_and_update()