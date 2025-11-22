import os
import re
import subprocess
from pathlib import Path

IMAGE_DIR = "images"
MANIFEST_FILE = "manifest.js"
SCRIPT_FILE = "generate_manifest.py"
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

def get_existing_numbers(ext):
    """Return a sorted list of used numbers for a given extension."""
    files = os.listdir(IMAGE_DIR)
    numbers = []
    for f in files:
        name, e = os.path.splitext(f)
        if e.lower() == ext and name.startswith("image"):
            try:
                num = int(name.replace("image", ""))
                numbers.append(num)
            except ValueError:
                pass
    return sorted(numbers)

def get_next_available_number(ext):
    """Find the lowest missing number, else next highest."""
    numbers = get_existing_numbers(ext)
    if not numbers:
        return 1
    # find first gap
    for i in range(1, max(numbers) + 1):
        if i not in numbers:
            return i
    return max(numbers) + 1

def rename_untracked_images():
    """Rename any non‑conforming files to the next available slot."""
    files = os.listdir(IMAGE_DIR)
    renamed = []
    for f in files:
        name, ext = os.path.splitext(f)
        ext = ext.lower()
        if ext not in VALID_EXTENSIONS:
            continue
        if not name.startswith("image"):
            # Needs renaming
            next_num = get_next_available_number(ext)
            new_name = f"image{next_num:05d}{ext}"
            old_path = Path(IMAGE_DIR) / f
            new_path = Path(IMAGE_DIR) / new_name
            os.rename(old_path, new_path)
            renamed.append((f, new_name))
    if renamed:
        print("🔄 Renamed files:")
        for old, new in renamed:
            print(f"  {old} → {new}")
    return renamed

def get_image_list():
    files = os.listdir(IMAGE_DIR)
    images = [f for f in files if os.path.splitext(f)[1].lower() in VALID_EXTENSIONS]
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
        subprocess.run(["git", "add", MANIFEST_FILE, SCRIPT_FILE, IMAGE_DIR], check=True)
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
        rename_untracked_images()
        images = get_image_list()
        write_manifest(images)
        git_commit_and_push()
    except Exception as e:
        print(f"❌ Error: {e}")