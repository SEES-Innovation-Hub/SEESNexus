interface TeamMember {
  name: string;
  role: string;
  // Path under public/ (e.g. "/team/jane.jpg"); omit to show the placeholder icon.
  imageUrl?: string;
}

// Photos are 640x640 WebP in public/team/, cropped square on the face, with
// the camera's metadata (time, device, location) stripped.
const TEAM: TeamMember[] = [
  { name: "Ifeoluwa Adeyemo", role: "Frontend Engineer", imageUrl: "/team/ifeoluwa.webp" },
  { name: "Olaitan Ismail", role: "Backend Engineer", imageUrl: "/team/olaitan-ismail.webp" },
  {
    name: "Fakorode Henry",
    role: "Technical Development Lead & Backend Engineer",
    imageUrl: "/team/fakorode-henry.webp",
  },
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
    <li className="flex flex-col overflow-hidden rounded-3xl border border-sees-teal/40 bg-gradient-card shadow-sees-card">
      {member.imageUrl ? (
        <img
          src={member.imageUrl}
          alt={member.name}
          width={640}
          height={640}
          loading="lazy"
          decoding="async"
          className="aspect-square w-full object-cover"
        />
      ) : (
        <div className="flex aspect-square w-full items-center justify-center">
          <PlaceholderAvatar />
        </div>
      )}
      <div className="flex-1 bg-sees-void/40 px-4 py-5 text-center">
        <h3 className="text-lg font-semibold wrap-anywhere text-white">{member.name}</h3>
        <p className="mt-1 text-sm font-semibold uppercase tracking-wider text-balance text-sees-mint/60">
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
      <ul className="mx-auto mt-8 grid max-w-xs gap-5 sm:max-w-none sm:grid-cols-3">
        {TEAM.map((member) => (
          <TeamMemberCard key={member.name} member={member} />
        ))}
      </ul>
    </section>
  );
}
