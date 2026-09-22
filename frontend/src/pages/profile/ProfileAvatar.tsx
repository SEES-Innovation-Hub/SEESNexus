import { useState, type ChangeEvent } from "react";
import { uploadImage } from "../../api/upload";
import { errorMessage } from "../../api/client";
import { useAuth } from "../../hooks/useAuth";

interface ProfileAvatarProps {
  imageUrl: string | null;
  name: string;
}

export function ProfileAvatar({ imageUrl, name }: ProfileAvatarProps) {
  const { updateProfile } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const input = event.target;
    const file = input.files?.[0];
    if (!file) return;

    setError(null);
    setIsUploading(true);
    try {
      const { url } = await uploadImage(file);
      await updateProfile({ profile_image_url: url });
    } catch (uploadError) {
      setError(errorMessage(uploadError, "Could not upload the image. Try again."));
    } finally {
      setIsUploading(false);
      // Lets the same file be picked again after a failed attempt.
      input.value = "";
    }
  }

  return (
    <div className="flex flex-col items-center gap-2">
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={`${name}'s profile`}
          width={96}
          height={96}
          decoding="async"
          className="size-24 rounded-full border border-sees-teal object-cover"
        />
      ) : (
        <div
          aria-hidden="true"
          className="flex size-24 items-center justify-center rounded-full border border-sees-teal bg-sees-glass text-3xl font-semibold text-sees-mint"
        >
          {name.charAt(0).toUpperCase()}
        </div>
      )}

      <label className="inline-flex min-h-11 cursor-pointer items-center text-sm text-sees-mustard underline focus-within:ring-1 focus-within:ring-sees-mint hover:text-sees-mint">
        {isUploading ? "Uploading…" : "Change photo"}
        <input
          type="file"
          accept="image/*"
          disabled={isUploading}
          onChange={handleFileChange}
          className="sr-only"
        />
      </label>

      {error && <p className="text-center text-sm text-red-400">{error}</p>}
    </div>
  );
}
