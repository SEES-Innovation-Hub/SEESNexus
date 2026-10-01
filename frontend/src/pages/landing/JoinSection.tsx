import PrefetchLink from "../../components/PrefetchLink";
import { useAuth } from "../../hooks/useAuth";

// A pitch to sign up means nothing to someone who already has an account.
export function JoinSection() {
  const { user, isLoading } = useAuth();
  if (isLoading || user) return null;

  return (
    <section
      aria-labelledby="join-heading"
      className="mx-auto w-full max-w-6xl px-6 py-16"
    >
      <div className="rounded-3xl border border-sees-teal/40 bg-gradient-card p-10 text-center shadow-sees-card md:p-16">
        <h2 id="join-heading" className="text-3xl font-semibold text-sees-mint">
          Join SEES Nexus
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-white/70">
          Create an account to be part of the community's projects, hardware lab
          and events.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-4">
          <PrefetchLink
            to="/register"
            className="rounded bg-sees-mint px-6 py-3 font-medium text-sees-forest transition-shadow hover:shadow-sees-glow"
          >
            Create an account
          </PrefetchLink>
          <PrefetchLink
            to="/login"
            className="rounded border border-sees-teal px-6 py-3 font-medium text-sees-mint hover:border-sees-mint"
          >
            Log in
          </PrefetchLink>
        </div>
      </div>
    </section>
  );
}
