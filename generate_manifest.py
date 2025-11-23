import os
import re
from github import Auth, Github

IMAGE_DIR = "images"
MANIFEST_FILE = "manifest.js"
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

GH_PAT = os.getenv("GH_PAT")
REPO_NAME = "gitkailas/infinite-gallery"

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

def get_image_list(repo):
    files = repo.get_contents(IMAGE_DIR)
    images = [f.name for f in files if os.path.splitext(f.name)[1].lower() in VALID_EXTENSIONS]
    return sorted(images, key=natural_sort_key, reverse=True)

def build_manifest(images):
    content = "const manifest = [\n"
    for img in images:
        content += f'  "{IMAGE_DIR}/{img}",\n'
    content += "];\n"
    return content

def update_manifest():
    auth = Auth.Token(GH_PAT)
    g = Github(auth=auth)
    repo = g.get_repo(REPO_NAME)

    images = get_image_list(repo)
    manifest_content = build_manifest(images)

    try:
        contents = repo.get_contents(MANIFEST_FILE)
        repo.update_file(contents.path, "Update manifest", manifest_content, contents.sha)
        print(f"✅ {MANIFEST_FILE} updated with {len(images)} images.")
    except Exception:
        repo.create_file(MANIFEST_FILE, "Create manifest", manifest_content)
        print(f"✅ {MANIFEST_FILE} created with {len(images)} images.")

if __name__ == "__main__":
    update_manifest()