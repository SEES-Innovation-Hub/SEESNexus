import { useNavigate, useParams } from "react-router-dom";
import { errorMessage, isNotFoundError } from "../../api/client";
import { buttonClassName } from "../../components/Button/buttonClassName";
import Card from "../../components/Card";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import PrefetchLink from "../../components/PrefetchLink";
import Skeleton from "../../components/Skeleton";
import { useAuth } from "../../hooks/useAuth";
import { useProject } from "../../hooks/useProject";
import { useToast } from "../../hooks/useToast";
import { useUpdateProject } from "../../hooks/useUpdateProject";
import { canEditProject } from "../../utils/canEditProject";
import { toFormValues } from "./projectFormValues";
import { ProjectForm } from "./ProjectForm";
import { ProjectNotFound } from "./ProjectNotFound";

export function EditProject() {
  const { id = "" } = useParams();
  const { user } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const { data: project, error, isPlaceholderData, isFetching, refetch } = useProject(id);
  const updateProject = useUpdateProject();
  const detailPath = `/projects/${id}`;

  if (error && (!project || isPlaceholderData)) {
    return isNotFoundError(error) ? (
      <ProjectNotFound />
    ) : (
      <ErrorState onRetry={() => void refetch()} isRetrying={isFetching} />
    );
  }
  // The form copies its starting values once, so wait for the fresh record
  // rather than starting from a list's copy that might be older.
  if (!project || isPlaceholderData) {
    return <Skeleton className="mx-auto h-[32rem] max-w-2xl rounded-2xl" />;
  }

  if (!canEditProject(project, user)) {
    return (
      <EmptyState
        title="You can't edit this project"
        message="Only the person who created it, or an admin, can make changes."
        action={
          <PrefetchLink to={detailPath} className={buttonClassName("secondary")}>
            Back to the project
          </PrefetchLink>
        }
      />
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-sees-mint">Edit project</h1>
        <p className="mt-1 wrap-anywhere text-white/60">{project.title}</p>
      </div>
      <Card padding="lg">
        <ProjectForm
          initialValues={toFormValues(project)}
          submitLabel="Save changes"
          isSubmitting={updateProject.isPending}
          serverError={updateProject.error && errorMessage(updateProject.error, "Couldn't save the changes. Try again.")}
          onSubmit={(payload) =>
            // member_ids is left out, so the backend keeps the current team.
            updateProject.mutate(
              { id, payload },
              {
                onSuccess: () => {
                  showToast("Changes saved");
                  navigate(detailPath);
                },
              },
            )
          }
          onCancel={() => navigate(detailPath)}
        />
      </Card>
    </div>
  );
}
