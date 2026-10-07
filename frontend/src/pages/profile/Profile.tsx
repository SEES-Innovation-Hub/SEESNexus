import { useState } from "react";
import Button from "../../components/Button";
import Card from "../../components/Card";
import { useAuth } from "../../hooks/useAuth";
import { useLogout } from "../../hooks/useLogout";
import { ProfileAvatar } from "./ProfileAvatar";
import { ProfileDetails } from "./ProfileDetails";
import { ProfileEditForm } from "./ProfileEditForm";

export function Profile() {
  const { user } = useAuth();
  const logout = useLogout();
  const [isEditing, setIsEditing] = useState(false);

  // ProtectedRoute never renders this without a user; this narrows the type.
  if (!user) return null;

  return (
    // Inside AppLayout: the sidebar provides the page frame, so this is just the card.
    <div className="mx-auto w-full max-w-md">
      <Card padding="lg" className="space-y-6">
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
              <Button onClick={() => setIsEditing(true)} className="flex-1">
                Edit profile
              </Button>
              <Button variant="secondary" onClick={logout} className="flex-1">
                Log out
              </Button>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
