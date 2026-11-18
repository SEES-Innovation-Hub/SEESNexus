import { UserPlus, X } from "lucide-react";
import { useState } from "react";
import Avatar from "../../components/Avatar";
import TextField from "../../components/TextField";
import { MIN_SEARCH_LENGTH, useUserSearch } from "../../hooks/useUserSearch";
import type { ProjectMember } from "../../types/project";

const MAX_TEAM = 20;

interface TeamPickerProps {
  value: ProjectMember[];
  onChange: (members: ProjectMember[]) => void;
  // The project's creator: always on the team, so no remove button.
  lockedId: string;
}

// The team: chips for who's on it, and a name search to add more.
export function TeamPicker({ value, onChange, lockedId }: TeamPickerProps) {
  const [query, setQuery] = useState("");
  const search = useUserSearch(query);
  const onTeam = new Set(value.map((member) => member.id));
  const results = (search.data ?? []).filter((member) => !onTeam.has(member.id));
  const typedEnough = query.trim().length >= MIN_SEARCH_LENGTH;
  const isFull = value.length >= MAX_TEAM;

  function add(member: ProjectMember) {
    if (isFull) return;
    onChange([...value, member]);
    setQuery("");
  }

  return (
    <fieldset className="space-y-3">
      <legend className="text-sm font-medium text-sees-mint/80">Team</legend>
      <ul aria-label="Team members" className="flex flex-wrap gap-2">
        {value.map((member) => (
          <li
            key={member.id}
            className="inline-flex min-h-11 items-center gap-2 rounded-full border border-sees-teal bg-sees-void/60 py-1 pr-1 pl-1.5 text-sm text-white"
          >
            <Avatar name={member.full_name} imageUrl={member.profile_image_url} size={28} />
            <span className="wrap-anywhere">{member.full_name}</span>
            {member.id === lockedId ? (
              <span className="pr-2 text-xs text-white/50">creator</span>
            ) : (
              <button
                type="button"
                onClick={() => onChange(value.filter((m) => m.id !== member.id))}
                aria-label={`Remove ${member.full_name} from the team`}
                className="-my-1.5 -mr-1 inline-flex size-11 shrink-0 items-center justify-center rounded-full text-white/50 hover:text-white"
              >
                <X aria-hidden="true" className="size-4" />
              </button>
            )}
          </li>
        ))}
      </ul>

      {isFull ? (
        <p className="text-xs text-white/50">That's the maximum of {MAX_TEAM} members.</p>
      ) : (
        <div className="space-y-2">
          <TextField
            id="team-search"
            label="Add a teammate"
            type="search"
            required={false}
            value={query}
            onChange={setQuery}
            maxLength={100}
            autoComplete="off"
            placeholder="Start typing a name"
          />
          {typedEnough && (
            <div aria-live="polite">
              {search.isPending ? (
                <p className="text-sm text-white/50">Searching…</p>
              ) : search.isError ? (
                <p className="text-sm text-red-400">Couldn't search right now. Try again.</p>
              ) : results.length === 0 ? (
                <p className="text-sm text-white/50">No other members match "{query.trim()}".</p>
              ) : (
                <ul aria-label="Matching members" className="divide-y divide-sees-teal/40 rounded-xl border border-sees-teal/60">
                  {results.map((member) => (
                    <li key={member.id}>
                      <button
                        type="button"
                        onClick={() => add(member)}
                        className="flex min-h-11 w-full items-center gap-3 px-3 py-2 text-left text-sm text-white hover:bg-sees-mint/5"
                      >
                        <Avatar name={member.full_name} imageUrl={member.profile_image_url} size={28} />
                        <span className="flex-1 wrap-anywhere">{member.full_name}</span>
                        <UserPlus aria-hidden="true" className="size-4 text-sees-mint" />
                        <span className="sr-only">Add to the team</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      )}
    </fieldset>
  );
}
