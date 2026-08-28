"use client";

import { useState } from "react";
import { useSelectionStore } from "@/lib/stores/selection-store";
import { useCreateScriptVersion, useFactChecks, useScripts, useUpdateScriptStatus } from "@/lib/hooks/use-scripts";
import { useToast } from "@/lib/stores/toast-store";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { IconScripts } from "@/components/ui/icons";
import { ScriptSectionsEditor } from "@/components/editors/ScriptSectionsEditor";
import { ScriptStatus } from "@/types/enums";
import type { ScriptRead } from "@/lib/api/schemas/scripts";

function FactCheckList({ scriptId }: { scriptId: string }) {
  const { data: factChecks } = useFactChecks(scriptId);
  if (!factChecks || factChecks.length === 0) return null;
  return (
    <div className="mt-2 flex flex-col gap-1">
      {factChecks.map((fc) => (
        <div key={fc.id} className="flex items-center gap-2 text-xs">
          <StatusBadge status={fc.verdict} />
          <span className="text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
            {fc.flags.length} flag(s) · {fc.model_used ?? "unknown model"}
          </span>
        </div>
      ))}
    </div>
  );
}

function ScriptSections({ sections }: { sections: Record<string, unknown> }) {
  const entries = Object.entries(sections);
  if (entries.length === 0) {
    return (
      <p className="mt-3 text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">Empty draft — no sections yet.</p>
    );
  }
  return (
    <div className="mt-3 flex flex-col gap-3">
      {entries.map(([key, value]) => (
        <div key={key}>
          <div className="text-xs font-semibold tracking-wide text-(--color-text-muted) uppercase dark:text-(--color-text-muted-dark)">
            {key}
          </div>
          <div className="mt-1 text-sm whitespace-pre-wrap text-(--color-text) dark:text-(--color-text-dark)">
            {typeof value === "string" ? value : JSON.stringify(value, null, 2)}
          </div>
        </div>
      ))}
    </div>
  );
}

function ScriptCard({
  script,
  onTransition,
  isTransitioning,
  isEditing,
  onStartEdit,
  onCancelEdit,
  onSaveEdit,
  isSavingEdit,
}: {
  script: ScriptRead;
  onTransition: (status: ScriptStatus) => void;
  isTransitioning: boolean;
  isEditing: boolean;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onSaveEdit: (sections: Record<string, string>) => void;
  isSavingEdit: boolean;
}) {
  const next: Partial<Record<ScriptStatus, ScriptStatus[]>> = {
    [ScriptStatus.DRAFT]: [ScriptStatus.IN_REVIEW],
    [ScriptStatus.IN_REVIEW]: [ScriptStatus.APPROVED, ScriptStatus.REJECTED, ScriptStatus.DRAFT],
    [ScriptStatus.REJECTED]: [ScriptStatus.DRAFT],
  };
  const options = next[script.status] ?? [];

  return (
    <Card>
      <div className="mb-2 flex items-center justify-between">
        <span className="font-medium text-(--color-text) dark:text-(--color-text-dark)">Version {script.version}</span>
        <StatusBadge status={script.status} />
      </div>
      <FactCheckList scriptId={script.id} />

      {isEditing ? (
        <div className="mt-3">
          <ScriptSectionsEditor initialSections={script.sections} isSaving={isSavingEdit} onSave={onSaveEdit} />
          <div className="mt-2 flex justify-end">
            <Button variant="ghost" size="sm" onClick={onCancelEdit}>
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <>
          <ScriptSections sections={script.sections} />
          <div className="mt-3 flex gap-2">
            <Button size="sm" variant="secondary" onClick={onStartEdit}>
              Edit
            </Button>
            {options.map((status) => (
              <Button key={status} size="sm" variant="secondary" isLoading={isTransitioning} onClick={() => onTransition(status)}>
                {status === ScriptStatus.DRAFT ? "Back to draft" : status}
              </Button>
            ))}
          </div>
        </>
      )}
    </Card>
  );
}

export default function ScriptsPage() {
  const { projectId } = useSelectionStore();
  const { data: scripts, isLoading } = useScripts(projectId ?? "");
  const createVersion = useCreateScriptVersion(projectId ?? "");
  const updateStatus = useUpdateScriptStatus(projectId ?? "");
  const toast = useToast();
  const [showEditor, setShowEditor] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const isEmpty = !isLoading && (scripts?.items.length ?? 0) === 0;

  const handleSaveEdit = (sections: Record<string, string>) => {
    createVersion.mutate(
      { sections },
      {
        onSuccess: () => {
          toast.success("New version created from your edits");
          setEditingId(null);
        },
        onError: () => toast.error("Failed to save edits"),
      },
    );
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-end gap-4">
        <div>
          <h1 className="text-xl font-semibold text-(--color-text) dark:text-(--color-text-dark)">Scripts</h1>
          {projectId && (
            <p className="mt-0.5 text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
              Version history and drafts
            </p>
          )}
        </div>
        {projectId && !isEmpty && (
          <Button
            className="ml-auto"
            onClick={() => {
              setEditingId(null);
              setShowEditor((v) => !v);
            }}
          >
            {showEditor ? "Cancel" : "+ Write new version"}
          </Button>
        )}
      </div>

      {!projectId ? (
        <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">Select a project.</p>
      ) : (
        <>
          {showEditor && (
            <Card>
              <ScriptSectionsEditor
                initialSections={{}}
                isSaving={createVersion.isPending}
                onSave={(sections) =>
                  createVersion.mutate(
                    { sections },
                    {
                      onSuccess: () => {
                        toast.success("Script version created");
                        setShowEditor(false);
                      },
                      onError: () => toast.error("Failed to create script version"),
                    },
                  )
                }
              />
            </Card>
          )}

          {isLoading ? (
            <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">Loading…</p>
          ) : isEmpty ? (
            <EmptyState
              icon={<IconScripts />}
              title="No drafts yet"
              description="Generate a first draft from your approved idea, or write one from scratch. Every version is kept, so you can compare and roll back."
              action={
                !showEditor && <Button onClick={() => setShowEditor(true)}>Write first draft</Button>
              }
            />
          ) : (
            <div className="flex flex-col gap-3">
              {scripts?.items.map((script) => (
                <ScriptCard
                  key={script.id}
                  script={script}
                  isTransitioning={updateStatus.isPending}
                  onTransition={(status) =>
                    updateStatus.mutate(
                      { scriptId: script.id, data: { status } },
                      { onError: () => toast.error("Status transition failed") },
                    )
                  }
                  isEditing={editingId === script.id}
                  onStartEdit={() => {
                    setShowEditor(false);
                    setEditingId(script.id);
                  }}
                  onCancelEdit={() => setEditingId(null)}
                  onSaveEdit={handleSaveEdit}
                  isSavingEdit={createVersion.isPending}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
