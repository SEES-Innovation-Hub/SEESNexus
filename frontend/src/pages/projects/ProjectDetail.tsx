import { ArrowLeft, CodeXml, ExternalLink, Pencil, Trash } from "lucide-react";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { errorMessage, isNotFoundError } from "../../api/client";
import Avatar from "../../components/Avatar";
import Badge from "../../components/Badge";
import Button from "../../components/Button";
import { buttonClassName } from "../../components/Button/buttonClassName";
import Card from "../../components/Card";
import ConfirmDialog from "../../components/ConfirmDialog";
import ErrorState from "../../components/ErrorState";
import PrefetchLink from "../../components/PrefetchLink";
import Skeleton from "../../components/Skeleton";
import { useAuth } from "../../hooks/useAuth";
import { useDeleteProject } from "../../hooks/useDeleteProject";
import { useProject } from "../../hooks/useProject";
import { useToast } from "../../hooks/useToast";
import { canEditProject } from "../../utils/canEditProject";
import { isHttpUrl } from "../../utils/isHttpUrl";
import { CATEGORY_LABELS, STATUS_LABELS } from "../../utils/projectLabels";
import { ProjectNotFound } from "./ProjectNotFound";

const backLinkClassName =
  "-my-3 inline-flex items-center gap-1 py-3 text-sm text-sees-mustard hover:text-sees-mint";

export function ProjectDetail() {
  const { id = "" } = useParams();
  const { user } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const { data: project, error, isPending, isFetching, refetch } = useProject(id);
  const deleteProject = useDeleteProject();
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  if (isPending) {
    return (
      <div aria-busy="true" aria-label="Loading project" className="mx-auto max-w-3xl space-y-4">
        <Skeleton className="aspect-[21/9] rounded-2xl" />
        <Skeleton className="h-9 w-2/3" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }
  if (!project) {
    return isNotFoundError(error) ? (
      <ProjectNotFound />
    ) : (
      <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />
    );
  }

  function handleDelete() {
    deleteProject.mutate(id, {
      onSuccess: () => {
        setConfirmingDelete(false);
        showToast("Project deleted");
        navigate("/projects");
      },
      onError: (deleteError) => {
        setConfirmingDelete(false);
        showToast(errorMessage(deleteError, "Couldn't delete the project. Try again."), "error");
      },
    });
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PrefetchLink to="/projects" className={backLinkClassName}>
        <ArrowLeft aria-hidden="true" className="size-4" />
        All projects
      </PrefetchLink>

      <Card as="article" padding="none" className="overflow-hidden">
        {project.thumbnail_url ? (
          <img
            src={project.thumbnail_url}
            alt=""
            width={1152}
            height={494}
            className="aspect-[21/9] w-full object-cover"
          />
        ) : (
          // Until thumbnails can be uploaded most projects have none, so the
          // stand-in is a slim banner rather than an empty full-size image box.
          <div
            aria-hidden="true"
            className="flex h-24 w-full items-center justify-center bg-sees-glass font-mono text-sees-mint/60 sm:h-32"
          >
            {CATEGORY_LABELS[project.category]}
          </div>
        )}

        <div className="space-y-6 p-5 sm:p-8">
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Badge tone="mint">{CATEGORY_LABELS[project.category]}</Badge>
              <Badge tone="mustard">{STATUS_LABELS[project.status]}</Badge>
            </div>
            <h1 className="text-2xl font-semibold wrap-anywhere text-white sm:text-3xl">{project.title}</h1>
            <p className="text-sm text-white/50">
              Added {new Date(project.created_at).toLocaleDateString(undefined, { dateStyle: "long" })}
            </p>
          </div>

          <p className="whitespace-pre-line wrap-anywhere text-white/80">{project.description}</p>

          {project.tech_stack.length > 0 && (
            <section aria-labelledby="tech-heading" className="space-y-2">
              <h2 id="tech-heading" className="text-sm font-medium text-sees-mint/80">
                Built with
              </h2>
              <ul className="flex flex-wrap gap-2 font-mono text-sm text-white/70">
                {project.tech_stack.map((tech) => (
                  <li key={tech} className="max-w-full rounded bg-sees-void/60 px-2 py-1 wrap-anywhere">
                    {tech}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {project.members.length > 0 && (
            <section aria-labelledby="team-heading" className="space-y-2">
              <h2 id="team-heading" className="text-sm font-medium text-sees-mint/80">
                Team
              </h2>
              <ul className="flex flex-wrap gap-4">
                {project.members.map((member) => (
                  <li key={member.id} className="flex items-center gap-2 text-sm text-white/80">
                    <Avatar name={member.full_name} imageUrl={member.profile_image_url} />
                    <span className="wrap-anywhere">{member.full_name}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {(isHttpUrl(project.demo_url) || isHttpUrl(project.github_url)) && (
            <div className="flex flex-wrap gap-3">
              {isHttpUrl(project.demo_url) && (
                <a href={project.demo_url} target="_blank" rel="noreferrer" className={buttonClassName("secondary")}>
                  <ExternalLink aria-hidden="true" className="size-4" />
                  Live demo
                </a>
              )}
              {isHttpUrl(project.github_url) && (
                <a href={project.github_url} target="_blank" rel="noreferrer" className={buttonClassName("secondary")}>
                  <CodeXml aria-hidden="true" className="size-4" />
                  Source code
                </a>
              )}
            </div>
          )}

          {canEditProject(project, user) && (
            <div className="flex flex-wrap gap-3 border-t border-sees-teal/40 pt-6">
              <PrefetchLink to={`/projects/${project.id}/edit`} className={buttonClassName()}>
                <Pencil aria-hidden="true" className="size-4" />
                Edit project
              </PrefetchLink>
              <Button variant="danger" onClick={() => setConfirmingDelete(true)}>
                <Trash aria-hidden="true" className="size-4" />
                Delete
              </Button>
            </div>
          )}
        </div>
      </Card>

      <ConfirmDialog
        open={confirmingDelete}
        title="Delete this project?"
        message={`"${project.title}" will be removed for everyone. This can't be undone.`}
        confirmLabel="Delete project"
        onConfirm={handleDelete}
        onCancel={() => setConfirmingDelete(false)}
        isPending={deleteProject.isPending}
      />
    </div>
  );
}
