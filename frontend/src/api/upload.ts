import { api, unwrap } from "./client";

// ASSUMED contract — /upload/image (Zafrullah's Cloudinary endpoint) isn't
// built yet. Assumes a multipart "file" field and a `{url}` payload in the
// envelope. Confirm against the real endpoint; this is the only place to change.
export function uploadImage(file: File) {
  const body = new FormData();
  body.append("file", file);
  return unwrap<{ url: string }>(api.post("/upload/image", body));
}
