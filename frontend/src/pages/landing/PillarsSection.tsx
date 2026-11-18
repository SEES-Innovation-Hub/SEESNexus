// Static marketing copy (from the project documentation's "Core Pillars"), not
// backend data, so there is nothing to fetch here.
const PILLARS = [
  {
    title: "Innovation Gallery",
    description:
      "See what other students are building, and share your own projects with the society.",
  },
  {
    title: "Hardware Lab",
    description:
      "Check what the lab has, request what you need, and see when it's due back.",
  },
  {
    title: "Community & Events",
    description:
      "Find hackathons, workshops and congresses, and register for them here.",
  },
];

export function PillarsSection() {
  return (
    <section
      aria-labelledby="pillars-heading"
      className="mx-auto w-full max-w-6xl px-6 py-16"
    >
      <h2 id="pillars-heading" className="text-3xl font-semibold text-sees-mint">
        What you can do here
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
