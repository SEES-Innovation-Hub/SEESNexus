import type { Project, ProjectMember } from "../../types/project";
import { isHttpUrl } from "../../utils/isHttpUrl";
import { CATEGORY_LABELS, STATUS_LABELS } from "../../utils/projectLabels";
import Badge from "../Badge";
import PrefetchLink from "../PrefetchLink";

const MAX_TECH_BADGES = 4;
const MAX_MEMBER_AVATARS = 4;

function MemberAvatar({ member }: { member: ProjectMember }) {
  const className =
    "-ml-2 size-7 rounded-full border border-sees-void object-cover first:ml-0";

  return member.profile_image_url ? (
    <img
      src={member.profile_image_url}
      alt={member.full_name}
      title={member.full_name}
      width={28}
      height={28}
      loading="lazy"
      decoding="async"
      className={className}
    />
  ) : (
    <span
      role="img"
      aria-label={member.full_name}
      title={member.full_name}
      className={`${className} flex items-center justify-center bg-sees-teal text-xs font-medium text-sees-mint`}
    >
      {member.full_name.charAt(0).toUpperCase()}
    </span>
  );
}

// py-3 with -my-3 grows the tap area to 44px without growing the card.
// relative z-10 lifts the links above the card-wide project link.
const linkClassName =
  "relative z-10 -mx-1.5 -my-3 px-1.5 py-3 text-sees-mustard underline hover:text-sees-mint";

// The width comes from the parent's grid column. The whole card opens the project: the title's
// link is stretched over the card with an ::after layer.
export default function ProjectCard({ project }: { project: Project }) {
  const extraTech = project.tech_stack.length - MAX_TECH_BADGES;

  return (
    <article className="relative h-full overflow-hidden rounded-2xl border border-sees-teal/40 bg-gradient-card shadow-sees-card transition-colors hover:border-sees-mint/50">
      {project.thumbnail_url ? (
        <img
          src={project.thumbnail_url}
          alt=""
          width={576}
          height={324}
          loading="lazy"
          decoding="async"
          className="aspect-video w-full object-cover"
        />
      ) : (
        // Without a thumbnail (every project until uploads exist) a phone gets a
        // slim banner instead of a tall empty box; wider screens keep the
        // picture's shape so cards in a row line up.
        <div
          aria-hidden="true"
          className="flex h-20 w-full items-center justify-center bg-sees-glass font-mono text-sm text-sees-mint/60 sm:aspect-video sm:h-auto"
        >
          {CATEGORY_LABELS[project.category]}
        </div>
      )}

      <div className="space-y-3 p-4">
        <div className="flex flex-wrap gap-2">
          <Badge tone="mint">{CATEGORY_LABELS[project.category]}</Badge>
          <Badge tone="mustard">{STATUS_LABELS[project.status]}</Badge>
        </div>

        <h3 className="text-lg font-semibold wrap-anywhere text-white">
          <PrefetchLink
            to={`/projects/${project.id}`}
            className="after:absolute after:inset-0 after:rounded-2xl focus-visible:outline-none focus-visible:after:outline-2 focus-visible:after:outline-sees-mint"
          >
            {project.title}
          </PrefetchLink>
        </h3>
        <p className="line-clamp-3 wrap-anywhere text-sm text-white/70">{project.description}</p>

        {project.tech_stack.length > 0 && (
          <ul className="flex flex-wrap gap-1.5 font-mono text-xs text-white/60">
            {project.tech_stack.slice(0, MAX_TECH_BADGES).map((tech) => (
              <li key={tech} className="max-w-full rounded bg-sees-void/60 px-1.5 py-0.5 wrap-anywhere">
                {tech}
              </li>
            ))}
            {extraTech > 0 && <li className="px-1 py-0.5">+{extraTech}</li>}
          </ul>
        )}

        <div className="flex items-center justify-between gap-2 text-sm">
          <div className="flex">
            {project.members.slice(0, MAX_MEMBER_AVATARS).map((member) => (
              <MemberAvatar key={member.id} member={member} />
            ))}
          </div>
          <div className="flex gap-3">
            {isHttpUrl(project.demo_url) && (
              <a href={project.demo_url} target="_blank" rel="noreferrer" className={linkClassName}>
                Demo
              </a>
            )}
            {isHttpUrl(project.github_url) && (
              <a href={project.github_url} target="_blank" rel="noreferrer" className={linkClassName}>
                GitHub
              </a>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}
