import { useNavigate } from "react-router-dom";
import { errorMessage } from "../../api/client";
import Card from "../../components/Card";
import { useAuth } from "../../hooks/useAuth";
import { useCreateProject } from "../../hooks/useCreateProject";
import { useToast } from "../../hooks/useToast";
import { EMPTY_VALUES } from "./projectFormValues";
import { ProjectForm } from "./ProjectForm";

export function NewProject() {
  const { user } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const createProject = useCreateProject();

  // ProtectedRoute never renders this without a user; this narrows the type.
  if (!user) return null;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-sees-mint">New project</h1>
        <p className="mt-1 text-white/60">Share what you're building with the rest of SEES.</p>
      </div>
      <Card padding="lg">
        <ProjectForm
          initialValues={EMPTY_VALUES}
          submitLabel="Create project"
          isSubmitting={createProject.isPending}
          serverError={createProject.error && errorMessage(createProject.error, "Couldn't create the project. Try again.")}
          onSubmit={(payload) =>
            // The creator is listed as the first team member. Picking other
            // members needs a user search endpoint the backend doesn't have yet.
            createProject.mutate(
              { ...payload, member_ids: [user.id] },
              {
                onSuccess: (project) => {
                  showToast("Project created");
                  navigate(`/projects/${project.id}`);
                },
              },
            )
          }
          onCancel={() => navigate("/projects")}
        />
      </Card>
    </div>
  );
}
