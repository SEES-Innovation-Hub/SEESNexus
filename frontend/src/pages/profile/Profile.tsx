import { useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import { ProfileAvatar } from "./ProfileAvatar";
import { ProfileDetails } from "./ProfileDetails";
import { ProfileEditForm } from "./ProfileEditForm";

export function Profile() {
  const { user, logout } = useAuth();
  const [isEditing, setIsEditing] = useState(false);

  // ProtectedRoute never renders this without a user; this narrows the type.
  if (!user) return null;

  return (
    // Inside AppLayout: the sidebar provides the page frame, so this is just the card.
    <div className="mx-auto w-full max-w-md">
      <div className="space-y-6 rounded-2xl border border-sees-teal/40 bg-gradient-card p-6 shadow-sees-card sm:p-8">
        <div className="flex flex-col items-center gap-3 text-center">
          <ProfileAvatar imageUrl={user.profile_image_url} name={user.full_name} />
          <h1 className="text-2xl font-semibold wrap-anywhere text-sees-mint">{user.full_name}</h1>
        </div>

        {isEditing ? (
          <ProfileEditForm user={user} onDone={() => setIsEditing(false)} />
        ) : (
          <>
            <ProfileDetails user={user} />
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="flex-1 rounded bg-sees-mint py-2.5 font-medium text-sees-forest transition-shadow hover:shadow-sees-glow"
              >
                Edit profile
              </button>
              <button
                type="button"
                onClick={logout}
                className="flex-1 rounded border border-sees-teal py-2.5 font-medium text-sees-mint hover:border-sees-mint"
              >
                Log out
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
