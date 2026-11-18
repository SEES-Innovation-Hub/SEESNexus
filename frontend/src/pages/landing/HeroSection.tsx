import { buttonClassName } from "../../components/Button/buttonClassName";
import PrefetchLink from "../../components/PrefetchLink";

const primaryCta = buttonClassName("primary", "", "lg");
const secondaryCta = buttonClassName("secondary", "", "lg");

export function HeroSection() {
  return (
    <section className="mx-auto flex w-full max-w-6xl flex-col items-start gap-6 px-6 py-20 md:py-32">
      <p className="font-mono text-sm uppercase tracking-widest text-sees-mustard">
        New Semester, New Heights
      </p>
      <h1 className="max-w-3xl text-4xl font-bold leading-tight text-sees-mint md:text-6xl">
        Projects, hardware and events for SEES.
      </h1>
      <p className="max-w-2xl text-lg text-white/70">
        Share what you're building, borrow equipment from the lab, and sign up
        for events. Made for the Society of Electrical, Electronics and Computer
        Engineering Students at the University of Lagos.
      </p>

      <div className="flex flex-wrap gap-4">
        <PrefetchLink to="/register" className={primaryCta}>
          Get started
        </PrefetchLink>
        <PrefetchLink to="/login" className={secondaryCta}>
          Log in
        </PrefetchLink>
      </div>
    </section>
  );
}
