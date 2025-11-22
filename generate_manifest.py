import os
import re

IMAGE_DIR = "images"
MANIFEST_FILE = "manifest.js"
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

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

if __name__ == "__main__":
    if not os.path.isdir(IMAGE_DIR):
        print(f"❌ Folder '{IMAGE_DIR}' not found.")
    else:
        images = get_image_list()
        write_manifest(images)