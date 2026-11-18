import { api, unwrap } from "./client";

// POST /upload/image (backend/app/api/v1/upload.py): multipart "file", up to
// 5 MB, JPEG/PNG/WebP/GIF (checked from the bytes). Returns the Cloudinary URL.
// 503 when the server has no Cloudinary keys.
export function uploadImage(file: File) {
  const body = new FormData();
  body.append("file", file);
  return unwrap<{ url: string }>(api.post("/upload/image", body));
}

export const MAX_UPLOAD_BYTES = 5 * 1024 * 1024;
export const UPLOAD_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"];
