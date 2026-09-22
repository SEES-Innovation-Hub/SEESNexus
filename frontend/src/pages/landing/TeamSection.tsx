interface TeamMember {
  name: string;
  role: string;
  // Path under public/ (e.g. "/team/jane.jpg"); omit to show the placeholder icon.
  imageUrl?: string;
}

// PLACEHOLDER content — swap in the real names, roles and photos.
const TEAM: TeamMember[] = [
  { name: "John Doe", role: "Frontend Lead" },
  { name: "Doe John", role: "Backend Lead" },
  { name: "Jane Roe", role: "Design Lead" },
  { name: "Richard Roe", role: "Hardware Lead" },
];

function PlaceholderAvatar() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
      aria-hidden="true"
      className="w-1/3 text-sees-mint/40"
    >
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="9.5" r="3.2" />
      <path d="M5.8 18.4c1.4-2.5 3.6-3.8 6.2-3.8s4.8 1.3 6.2 3.8" />
    </svg>
  );
}

function TeamMemberCard({ member }: { member: TeamMember }) {
  return (
    <li className="overflow-hidden rounded-3xl border border-sees-teal/40 bg-gradient-card shadow-sees-card">
      {member.imageUrl ? (
        <img
          src={member.imageUrl}
          alt={member.name}
          width={400}
          height={400}
          loading="lazy"
          decoding="async"
          className="aspect-square w-full object-cover"
        />
      ) : (
        <div className="flex aspect-square w-full items-center justify-center">
          <PlaceholderAvatar />
        </div>
      )}
      <div className="bg-sees-void/40 px-4 py-5 text-center">
        <h3 className="text-lg font-semibold text-white">{member.name}</h3>
        <p className="mt-1 text-sm font-semibold uppercase tracking-wider text-sees-mint/60">
          {member.role}
        </p>
      </div>
    </li>
  );
}

export function TeamSection() {
  return (
    <section
      id="team"
      aria-labelledby="team-heading"
      className="mx-auto w-full max-w-6xl px-6 py-16"
    >
      <h2 id="team-heading" className="text-3xl font-semibold text-sees-mint">
        The people behind Sees Nexus
      </h2>
      <ul className="mt-8 grid grid-cols-2 gap-5 md:grid-cols-4">
        {TEAM.map((member) => (
          <TeamMemberCard key={member.name} member={member} />
        ))}
      </ul>
    </section>
  );
}
