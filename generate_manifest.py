import os
import re
import subprocess

IMAGE_DIR = "images"
MANIFEST_FILE = "manifest.js"
SCRIPT_FILE = "generate_manifest.py"
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

def get_image_list():
    if not os.path.isdir(IMAGE_DIR):
        raise FileNotFoundError(f"❌ Folder '{IMAGE_DIR}' not found.")
    files = os.listdir(IMAGE_DIR)
    images = [f for f in files if os.path.splitext(f)[1].lower() in VALID_EXTENSIONS]
    missing = [f for f in files if os.path.splitext(f)[1].lower() not in VALID_EXTENSIONS]
    if missing:
        print(f"⚠️ Skipped non-image files: {missing}")
    return sorted(images, key=natural_sort_key)

def write_manifest(images):
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        f.write("const manifest = [\n")
        for img in images:
            f.write(f'  "{img}",\n')
        f.write("];\n")
    print(f"✅ {MANIFEST_FILE} updated with {len(images)} images.")

def git_commit_and_push():
    try:
        # Stage manifest, script, and all images
        subprocess.run(["git", "add", MANIFEST_FILE, SCRIPT_FILE], check=True)
        subprocess.run(["git", "add", IMAGE_DIR], check=True)

        # Check if there's anything to commit
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if result.stdout.strip() == "":
            print("ℹ️ No changes to commit.")
            return

        subprocess.run(["git", "commit", "-m", "Auto-update manifest and assets"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("🚀 Changes committed and pushed to GitHub.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")

if __name__ == "__main__":
    try:
        images = get_image_list()
        write_manifest(images)
        git_commit_and_push()
    except Exception as e:
        print(f"❌ Error: {e}")