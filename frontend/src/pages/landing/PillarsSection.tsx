// Static marketing copy (from the project documentation's "Core Pillars"), not
// backend data — there is nothing to fetch here.
const PILLARS = [
  {
    title: "Innovation Gallery",
    description:
      "A showcase for student work, so projects become discoverable, memorable and shareable.",
  },
  {
    title: "Hardware Lab",
    description:
      "See what equipment exists, who borrowed it and when it's due — less loss, faster checkout.",
  },
  {
    title: "Community & Events",
    description:
      "Discover and register for hackathons, workshops and congresses in one place.",
  },
];

export function PillarsSection() {
  return (
    <section
      aria-labelledby="pillars-heading"
      className="mx-auto w-full max-w-6xl px-6 py-16"
    >
      <h2 id="pillars-heading" className="text-3xl font-semibold text-sees-mint">
        One platform, three pillars
      </h2>
      <ul className="mt-8 grid gap-5 md:grid-cols-3">
        {PILLARS.map((pillar) => (
          <li
            key={pillar.title}
            className="rounded-2xl border border-sees-teal/40 bg-gradient-card p-6 shadow-sees-card"
          >
            <h3 className="text-lg font-semibold text-white">{pillar.title}</h3>
            <p className="mt-2 text-sm text-white/70">{pillar.description}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
