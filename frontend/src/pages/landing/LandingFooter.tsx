import PrefetchLink from "../../components/PrefetchLink";
import { useAuth } from "../../hooks/useAuth";

// min-h-11 = 44px, the touch-target size recommended for phones.
const linkClassName =
  "inline-flex min-h-11 min-w-11 items-center text-white/70 hover:text-sees-mint";

export function LandingFooter() {
  const { user, isLoading } = useAuth();

  return (
    <footer className="border-t border-sees-teal/40">
      <div className="mx-auto grid w-full max-w-6xl gap-10 px-6 py-12 md:grid-cols-3">
        <div>
          <p className="text-lg font-semibold text-sees-mint">SEES Nexus</p>
          <p className="mt-2 text-sm text-white/60">
            The Society of Electrical, Electronics and Computer Engineering
            Students, University of Lagos.
          </p>
        </div>

        <nav aria-label="Explore" className="text-sm">
          <p className="font-medium text-sees-mint/80">Explore</p>
          <ul className="mt-1">
            <li>
              <a href="#projects" className={linkClassName}>
                Innovation Gallery
              </a>
            </li>
            <li>
              <a href="#team" className={linkClassName}>
                The team
              </a>
            </li>
          </ul>
        </nav>

        <nav aria-label="Account" className="text-sm">
          <p className="font-medium text-sees-mint/80">Account</p>
          <ul className="mt-1">
            {!isLoading &&
              (user ? (
                <li>
                  <PrefetchLink to="/profile" className={linkClassName}>
                    Profile
                  </PrefetchLink>
                </li>
              ) : (
                <>
                  <li>
                    <PrefetchLink to="/login" className={linkClassName}>
                      Log in
                    </PrefetchLink>
                  </li>
                  <li>
                    <PrefetchLink to="/register" className={linkClassName}>
                      Register
                    </PrefetchLink>
                  </li>
                </>
              ))}
          </ul>
        </nav>
      </div>

      <p className="border-t border-sees-teal/40 px-6 py-5 text-center text-sm text-white/50">
        © {new Date().getFullYear()} SEES Nexus · New Semester, New Heights
      </p>
    </footer>
  );
}
