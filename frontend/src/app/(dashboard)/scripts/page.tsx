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

function ScriptCard({ script, onTransition, isTransitioning }: {
  script: ScriptRead;
  onTransition: (status: ScriptStatus) => void;
  isTransitioning: boolean;
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
      <div className="mt-3 flex gap-2">
        {options.map((status) => (
          <Button key={status} size="sm" variant="secondary" isLoading={isTransitioning} onClick={() => onTransition(status)}>
            {status === ScriptStatus.DRAFT ? "Back to draft" : status}
          </Button>
        ))}
      </div>
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

  const isEmpty = !isLoading && (scripts?.items.length ?? 0) === 0;

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
          <Button className="ml-auto" onClick={() => setShowEditor((v) => !v)}>
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
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
