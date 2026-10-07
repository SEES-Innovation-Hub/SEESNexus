import { useState, type ReactNode } from "react";
import Badge from "../../components/Badge";
import Button from "../../components/Button";
import { buttonClassName } from "../../components/Button/buttonClassName";
import Card from "../../components/Card";
import ConfirmDialog from "../../components/ConfirmDialog";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import Modal from "../../components/Modal";
import Pagination from "../../components/Pagination";
import Select from "../../components/Select";
import Skeleton from "../../components/Skeleton";
import Spinner from "../../components/Spinner";
import TextArea from "../../components/TextArea";
import TextField from "../../components/TextField";
import { useToast } from "../../hooks/useToast";

// TEMPORARY dev-only sandbox (route compiled out of production builds): every
// shared component in its states, to check looks and behaviour in one place.
// Not real app data: nothing here calls the API.

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-4">
      <h2 className="font-mono text-sm text-sees-mustard">{title}</h2>
      {children}
    </section>
  );
}

export function ComponentsPreview() {
  const { showToast } = useToast();
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmPending, setConfirmPending] = useState(false);
  const [page, setPage] = useState(1);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<"IOT" | "WEB" | "">("");

  function fakeConfirm() {
    setConfirmPending(true);
    window.setTimeout(() => {
      setConfirmPending(false);
      setConfirmOpen(false);
      showToast("Deleted (preview only, nothing was sent)");
    }, 1500);
  }

  return (
    <main className="mx-auto max-w-4xl space-y-12 px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-semibold text-sees-mint">Shared components</h1>

      <Section title="Button">
        <div className="flex flex-wrap gap-3">
          <Button>Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Danger</Button>
          <Button isLoading>Saving</Button>
          <Button disabled>Disabled</Button>
          <a href="#links" className={buttonClassName("secondary")}>
            A link styled as a button
          </a>
        </div>
      </Section>

      <Section title="Badge · Spinner · Skeleton">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="mint">Web</Badge>
          <Badge tone="mustard">In progress</Badge>
          <Badge tone="red">Rejected</Badge>
          <Badge>Returned</Badge>
          <Spinner className="ml-4 size-5 text-sees-mint" />
        </div>
        <div className="space-y-2">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      </Section>

      <Section title="Card">
        <div className="grid gap-4 sm:grid-cols-2">
          <Card as="article">
            <h3 className="text-lg font-semibold">Default padding</h3>
            <p className="text-sm text-white/70">A glass panel, as used by Login and project cards.</p>
          </Card>
          <Card as="article" padding="lg">
            <h3 className="text-lg font-semibold">Large padding</h3>
            <p className="text-sm wrap-anywhere text-white/70">
              Averyveryverylongunbrokenwordthatmustwrapinsidethecardonasmallphonescreen
            </p>
          </Card>
        </div>
      </Section>

      <Section title="Form fields">
        <Card className="max-w-md space-y-4">
          <TextField id="pv-title" label="Title" value={title} onChange={setTitle} hint="Shown on the project card." />
          <TextField
            id="pv-error"
            label="Email"
            value="not-an-email"
            onChange={() => undefined}
            error="Enter a valid email address."
          />
          <TextArea id="pv-desc" label="Description" value={description} onChange={setDescription} />
          <Select
            id="pv-cat"
            label="Category"
            value={category}
            onChange={setCategory}
            placeholder="All categories"
            required={false}
            options={[
              { value: "IOT", label: "IoT" },
              { value: "WEB", label: "Web" },
            ]}
          />
        </Card>
      </Section>

      <Section title="EmptyState · ErrorState">
        <EmptyState
          title="No projects yet"
          message="Projects you create will appear here."
          action={<Button>Create a project</Button>}
        />
        <ErrorState onRetry={() => showToast("Retry clicked")} />
      </Section>

      <Section title="Pagination">
        <Pagination page={page} totalPages={5} onPageChange={setPage} />
      </Section>

      <Section title="Modal · ConfirmDialog · Toast">
        <div className="flex flex-wrap gap-3">
          <Button variant="secondary" onClick={() => setModalOpen(true)}>
            Open modal
          </Button>
          <Button variant="danger" onClick={() => setConfirmOpen(true)}>
            Delete something
          </Button>
          <Button variant="secondary" onClick={() => showToast("Project saved")}>
            Success toast
          </Button>
          <Button variant="secondary" onClick={() => showToast("Couldn't save. Try again.", "error")}>
            Error toast
          </Button>
        </div>
      </Section>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="A modal"
        footer={<Button onClick={() => setModalOpen(false)}>Done</Button>}
      >
        <p className="text-sm text-white/70">
          Esc, the × button or clicking outside closes it. Tab stays inside. The page behind doesn't scroll.
        </p>
      </Modal>

      <ConfirmDialog
        open={confirmOpen}
        title="Delete this project?"
        message="This can't be undone."
        confirmLabel="Delete"
        onConfirm={fakeConfirm}
        onCancel={() => setConfirmOpen(false)}
        isPending={confirmPending}
      />
    </main>
  );
}
