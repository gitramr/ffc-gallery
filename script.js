let cursor = 0;
const BATCH_SIZE = 10;

function loadNextBatch() {
  const gallery = document.getElementById('gallery');
  const nextBatch = manifest.slice(cursor, cursor + BATCH_SIZE);
  console.log(`Loading images ${cursor} to ${cursor + BATCH_SIZE - 1}`);

  nextBatch.forEach(img => {
    const imageElement = document.createElement('img');
    const isFullPath = img.startsWith('images/') || img.startsWith('./images/');
    imageElement.src = isFullPath ? img : `images/${img}`;
    imageElement.loading = "lazy";
    imageElement.alt = img;
    imageElement.onerror = () => {
      console.error(`Failed to load image: ${imageElement.src}`);
      imageElement.style.display = "none";
    };
    gallery.appendChild(imageElement);
  });

  cursor += BATCH_SIZE;
}

const sentinel = document.getElementById('sentinel');
const observer = new IntersectionObserver(entries => {
  if (entries[0].isIntersecting) {
    loadNextBatch();
  }
});
observer.observe(sentinel);

document.addEventListener("DOMContentLoaded", () => {
  console.log("Document ready. Starting gallery.");
  if (!Array.isArray(manifest) || manifest.length === 0) {
    console.warn("Manifest is empty. No images to load.");
    return;
  }
  loadNextBatch();
});