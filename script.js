let manifest = [];
let cursor = 0;
const BATCH_SIZE = 10;

async function loadManifest() {
  const response = await fetch('manifest.json');
  manifest = await response.json();
  loadNextBatch();
}

function loadNextBatch() {
  const gallery = document.getElementById('gallery');
  const nextBatch = manifest.slice(cursor, cursor + BATCH_SIZE);
  nextBatch.forEach(img => {
    const imageElement = document.createElement('img');
    imageElement.src = `images/${img}`;
    imageElement.loading = "lazy";
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