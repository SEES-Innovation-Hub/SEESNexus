// Third-party, keyless image generation (pollinations.ai), called straight from
// the author's browser, with no backend endpoint involved. Notes from testing
// (2026-09-20):
//  - Speed varies from ~5s to ~45s for a new image; an already-generated one is
//    cached at their edge and returns in ~0.7s. So this only runs while an
//    author is creating a project, never on page load: visitors see the stored
//    thumbnail (uploaded via /upload/image), not this service.
//  - Requests whose origin is exactly "http://localhost:<port>" are rejected
//    (403, Turnstile). Any other origin works; in dev, open the app at
//    http://127.0.0.1:<port> instead.
//  - Anonymous use allows one queued request per IP and stamps a small
//    "pollinations.ai" watermark on the image.
const BASE_URL = "https://image.pollinations.ai/prompt";

// Keeps generated thumbnails visually consistent with the site's dark-teal brand.
const STYLE =
  "minimal flat vector illustration, dark teal background, mint accents, engineering theme, no text";

// 16:9 at 2x the project card's 288px width, so thumbnails stay sharp on phones.
const WIDTH = 576;
const HEIGHT = 324;

export async function generateImage(
  topic: string,
  signal: AbortSignal,
): Promise<File> {
  const prompt = encodeURIComponent(`${topic.trim()}, ${STYLE}`);
  // A fresh seed each call is what makes "generate again" give a new image.
  const seed = Math.floor(Math.random() * 1_000_000);
  const response = await fetch(
    `${BASE_URL}/${prompt}?width=${WIDTH}&height=${HEIGHT}&seed=${seed}&nologo=true&safe=true`,
    { signal },
  );
  if (!response.ok) {
    throw new Error(`Image generation failed (${response.status})`);
  }

  const blob = await response.blob();
  if (!blob.type.startsWith("image/")) {
    throw new Error("Image generation returned a non-image response");
  }
  return new File([blob], "generated.jpg", { type: blob.type });
}
