let manifest = [];
let cursor = 0;
const BATCH_SIZE = 10;

async function loadManifest() {
  try {
    const response = await fetch('manifest.json');
    if (!response.ok) throw new Error(`Failed to fetch manifest: ${response.status}`);
    manifest = await response.json();
    console.log("Manifest loaded:", manifest);
    if (manifest.length === 0) {
      console.warn("Manifest is empty. No images to load.");
      return;
    }
    loadNextBatch();
  } catch (error) {
    console.error("Error loading manifest:", error);
  }
}

function loadNextBatch() {
  const gallery = document.getElementById('gallery');
  const nextBatch = manifest.slice(cursor, cursor + BATCH_SIZE);
  console.log(`Loading images ${cursor} to ${cursor + BATCH_SIZE - 1}`);

  nextBatch.forEach(img => {
    const imageElement = document.createElement('img');
    imageElement.src = `images/${img}`;
    imageElement.loading = "lazy";
    imageElement.alt = img;
    imageElement.onerror = () => {
      console.error(`Failed to load image: ${imageElement.src}`);
      imageElement.style.display = "none"; // hide broken image
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

loadManifest();