import { ChevronsUpDown, LogOut, UserRound } from "lucide-react";
import { useId, useRef } from "react";
import { Link } from "react-router-dom";
import Avatar from "../../components/Avatar";
import { useAuth } from "../../hooks/useAuth";

const itemClassName =
  "flex min-h-11 w-full items-center gap-3 rounded-lg px-3 text-sm text-white/80 hover:bg-sees-mint/10 hover:text-white";

// The signed-in person at the bottom of the sidebar; clicking opens a small menu.
// The menu uses the browser's popover feature: it closes on Esc or a click
// anywhere else and sits above everything, with no JavaScript of our own.
// It is pinned to the bottom-left corner, where the sidebar always is.
export function UserMenu({ collapsed, onNavigate }: { collapsed: boolean; onNavigate?: () => void }) {
  const { user, logout } = useAuth();
  const menuId = useId();
  const menuRef = useRef<HTMLDivElement>(null);

  if (!user) return null;

  return (
    <div className="border-t border-sees-teal/40 p-3">
      <button
        type="button"
        popoverTarget={menuId}
        aria-label={collapsed ? `Account menu for ${user.full_name}` : undefined}
        className={`flex min-h-12 w-full items-center gap-3 rounded-lg p-2 text-left hover:bg-sees-mint/5 ${collapsed ? "justify-center" : ""}`}
      >
        <Avatar name={user.full_name} imageUrl={user.profile_image_url} />
        {!collapsed && (
          <>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-medium text-white">{user.full_name}</span>
              <span className="block truncate text-xs text-white/50">{user.email}</span>
            </span>
            <ChevronsUpDown aria-hidden="true" className="size-4 shrink-0 text-white/40" />
          </>
        )}
      </button>

      <div
        ref={menuRef}
        id={menuId}
        popover="auto"
        className="inset-auto bottom-20 left-3 m-0 w-60 rounded-xl border border-sees-teal/60 bg-sees-forest p-1 text-white shadow-sees-card"
      >
        <p className="px-3 pt-2 pb-1 text-xs wrap-anywhere text-white/50">{user.email}</p>
        <Link
          to="/profile"
          onClick={() => {
            menuRef.current?.hidePopover();
            onNavigate?.();
          }}
          className={itemClassName}
        >
          <UserRound aria-hidden="true" className="size-4" />
          Profile
        </Link>
        <button
          type="button"
          onClick={() => {
            menuRef.current?.hidePopover();
            logout();
          }}
          className={itemClassName}
        >
          <LogOut aria-hidden="true" className="size-4" />
          Log out
        </button>
      </div>
    </div>
  );
}
