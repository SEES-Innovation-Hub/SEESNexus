import { Link } from "react-router-dom";
import PrefetchLink from "../../components/PrefetchLink";
import { useAuth } from "../../hooks/useAuth";

// min-h-11 = 44px, the touch-target size recommended for phones.
const navLinkClassName =
  "inline-flex min-h-11 items-center px-3 text-sees-mint hover:text-white";

export function LandingNav() {
  const { user, isLoading } = useAuth();

  return (
    <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
      <Link
        to="/"
        className="inline-flex min-h-11 items-center text-lg font-semibold text-sees-mint"
      >
        SEES Nexus
      </Link>

      <nav aria-label="Account" className="flex items-center gap-2 text-sm">
        {!isLoading &&
          (user ? (
            <PrefetchLink to="/profile" className={navLinkClassName}>
              Profile
            </PrefetchLink>
          ) : (
            <>
              <PrefetchLink to="/login" className={navLinkClassName}>
                Log in
              </PrefetchLink>
              <PrefetchLink
                to="/register"
                className="inline-flex min-h-11 items-center rounded bg-sees-mint px-4 font-medium text-sees-forest transition-shadow hover:shadow-sees-glow"
              >
                Register
              </PrefetchLink>
            </>
          ))}
      </nav>
    </header>
  );
}
