import { useState, type FormEvent } from "react";
import { errorMessage } from "../../api/client";
import TextField from "../../components/TextField";
import { useAuth } from "../../hooks/useAuth";
import type { User, UserUpdatePayload } from "../../types/auth";

interface ProfileEditFormProps {
  user: User;
  onDone: () => void;
}

export function ProfileEditForm({ user, onDone }: ProfileEditFormProps) {
  const { updateProfile } = useAuth();
  const [fullName, setFullName] = useState(user.full_name);
  const [department, setDepartment] = useState(user.department);
  const [level, setLevel] = useState(user.level ?? "");
  const [bio, setBio] = useState(user.bio ?? "");
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    // The backend stores these two as NOT NULL and rejects/breaks on blanks,
    // and the native `required` check lets whitespace-only values through.
    if (!fullName.trim() || !department.trim()) {
      setError("Name and department can't be blank.");
      return;
    }

    // Only changed fields are sent — PUT /auth/me applies exactly what it gets.
    const changes: UserUpdatePayload = {};
    if (fullName.trim() !== user.full_name) changes.full_name = fullName.trim();
    if (department.trim() !== user.department) changes.department = department.trim();
    if (level.trim() !== (user.level ?? "")) changes.level = level.trim();
    if (bio.trim() !== (user.bio ?? "")) changes.bio = bio.trim();

    if (Object.keys(changes).length === 0) {
      onDone();
      return;
    }

    setIsSaving(true);
    try {
      await updateProfile(changes);
      onDone();
    } catch (saveError) {
      setError(errorMessage(saveError, "Could not save your changes. Try again."));
      setIsSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <TextField id="full_name" label="Full name" value={fullName} onChange={setFullName} />
      <TextField id="department" label="Department" value={department} onChange={setDepartment} />
      <TextField id="level" label="Level" value={level} onChange={setLevel} required={false} />

      <div>
        <label htmlFor="bio" className="block text-sm font-medium text-sees-mint/80">
          Bio
        </label>
        <textarea
          id="bio"
          rows={4}
          value={bio}
          onChange={(event) => setBio(event.target.value)}
          className="mt-1 w-full rounded border border-sees-teal bg-sees-void/60 px-3 py-2.5 text-white placeholder:text-white/30 focus:border-sees-mint focus:outline-none focus:ring-1 focus:ring-sees-mint"
        />
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={isSaving}
          className="flex-1 rounded bg-sees-mint py-2.5 font-medium text-sees-forest transition-shadow hover:shadow-sees-glow disabled:opacity-50"
        >
          {isSaving ? "Saving…" : "Save"}
        </button>
        <button
          type="button"
          onClick={onDone}
          disabled={isSaving}
          className="flex-1 rounded border border-sees-teal py-2.5 font-medium text-sees-mint hover:border-sees-mint disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
