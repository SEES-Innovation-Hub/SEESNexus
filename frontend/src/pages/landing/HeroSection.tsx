import { buttonClassName } from "../../components/Button/buttonClassName";
import PrefetchLink from "../../components/PrefetchLink";
import { useAuth } from "../../hooks/useAuth";

const primaryCta = buttonClassName("primary", "", "lg");
const secondaryCta = buttonClassName("secondary", "", "lg");

export function HeroSection() {
  const { user, isLoading } = useAuth();

  return (
    <section className="mx-auto flex w-full max-w-6xl flex-col items-start gap-6 px-6 py-20 md:py-32">
      <p className="font-mono text-sm uppercase tracking-widest text-sees-mustard">
        New Semester, New Heights
      </p>
      <h1 className="max-w-3xl text-4xl font-bold leading-tight text-sees-mint md:text-6xl">
        The digital home of SEES engineering.
      </h1>
      <p className="max-w-2xl text-lg text-white/70">
        Sees Nexus brings the projects, hardware and events of the Society of
        Electrical, Electronics and Computer Engineering Students at the
        University of Lagos into one place.
      </p>

      {/* Reserves the row while the session restores so the layout doesn't jump. */}
      <div className="flex min-h-12 flex-wrap gap-4">
        {!isLoading &&
          (user ? (
            <PrefetchLink to="/profile" className={primaryCta}>
              Go to your profile
            </PrefetchLink>
          ) : (
            <>
              <PrefetchLink to="/register" className={primaryCta}>
                Get started
              </PrefetchLink>
              <PrefetchLink to="/login" className={secondaryCta}>
                Log in
              </PrefetchLink>
            </>
          ))}
      </div>
    </section>
  );
}
