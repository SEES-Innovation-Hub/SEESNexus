import axios from "axios";
import { ImagePlus, Link2, Trash } from "lucide-react";
import { useId, useState, type ChangeEvent } from "react";
import { errorMessage } from "../../api/client";
import { MAX_UPLOAD_BYTES, UPLOAD_TYPES, uploadImage } from "../../api/upload";
import { isHttpUrl } from "../../utils/isHttpUrl";
import { buttonClassName } from "../Button/buttonClassName";
import Button from "../Button";
import TextField from "../TextField";

interface ImageUploadFieldProps {
  id: string;
  label: string;
  // The image's URL, or "" for none.
  value: string;
  onChange: (url: string) => void;
  hint?: string;
  error?: string;
  // Lets the host form hold back Save while a picture uploads.
  onUploadingChange?: (isUploading: boolean) => void;
}

// Pick a picture, it uploads to Cloudinary straight away (POST /upload/image)
// and the field holds the URL it came back with. Shows a preview; Replace and
// Remove. "Use a link instead" takes a pasted https:// URL, which is also the
// fallback when the server has no Cloudinary keys.
export default function ImageUploadField({ id, label, value, onChange, hint, error, onUploadingChange }: ImageUploadFieldProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [usingLink, setUsingLink] = useState(false);
  const labelId = useId();

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const input = event.target;
    const file = input.files?.[0];
    input.value = ""; // so picking the same file again still fires
    if (!file) return;

    // Checked here first for a quick answer; the server checks the bytes again.
    if (!UPLOAD_TYPES.includes(file.type)) {
      setUploadError("Choose a JPEG, PNG, WebP or GIF image.");
      return;
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      setUploadError("That image is over 5 MB. Choose a smaller one.");
      return;
    }

    setUploadError(null);
    setIsUploading(true);
    onUploadingChange?.(true);
    try {
      const { url } = await uploadImage(file);
      onChange(url);
    } catch (failure) {
      const notConfigured = axios.isAxiosError(failure) && failure.response?.status === 503;
      if (notConfigured) setUsingLink(true);
      setUploadError(
        notConfigured
          ? "Image upload isn't set up on this server yet. Paste a link to the image instead."
          : errorMessage(failure, "Couldn't upload the image. Try again."),
      );
    } finally {
      setIsUploading(false);
      onUploadingChange?.(false);
    }
  }

  const message = uploadError ?? error;

  return (
    <div role="group" aria-labelledby={labelId} className="space-y-2">
      <p id={labelId} className="text-sm font-medium text-sees-mint/80">
        {label} <span className="font-normal text-white/40">(optional)</span>
      </p>

      {isHttpUrl(value) && (
        <img
          src={value}
          alt=""
          className="aspect-video w-full max-w-sm rounded-xl border border-sees-teal/60 object-cover"
        />
      )}

      <div className="flex flex-wrap gap-2">
        <label
          className={`${buttonClassName("secondary")} cursor-pointer focus-within:outline-2 focus-within:outline-sees-mint ${isUploading ? "pointer-events-none opacity-60" : ""}`}
        >
          <ImagePlus aria-hidden="true" className="size-4" />
          {isUploading ? "Uploading…" : value ? "Replace image" : "Upload image"}
          <input
            id={id}
            type="file"
            accept={UPLOAD_TYPES.join(",")}
            disabled={isUploading}
            onChange={handleFile}
            className="sr-only"
          />
        </label>
        {value && !isUploading && (
          <Button variant="ghost" onClick={() => onChange("")}>
            <Trash aria-hidden="true" className="size-4" />
            Remove
          </Button>
        )}
        {!usingLink && (
          <Button variant="ghost" onClick={() => setUsingLink(true)}>
            <Link2 aria-hidden="true" className="size-4" />
            Use a link instead
          </Button>
        )}
      </div>

      {usingLink && (
        <TextField
          id={`${id}-link`}
          label="Image link"
          type="url"
          required={false}
          value={value}
          onChange={onChange}
          placeholder="https://…"
        />
      )}

      {message ? (
        <p role="alert" className="text-sm wrap-anywhere text-red-400">
          {message}
        </p>
      ) : (
        hint && <p className="text-xs text-white/50">{hint}</p>
      )}
    </div>
  );
}
