"use client";

import { useState } from "react";
import { useSelectionStore } from "@/lib/stores/selection-store";
import { useScripts } from "@/lib/hooks/use-scripts";
import { useAddScene, useCreateStoryboard, useScenes, useStoryboard, useUpdateStoryboardStatus } from "@/lib/hooks/use-storyboards";
import { useToast } from "@/lib/stores/toast-store";
import { ProjectPicker } from "@/components/layout/ProjectPicker";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { Input, Label, Textarea } from "@/components/ui/Input";
import { SceneTimeline } from "@/components/editors/SceneTimeline";
import { StoryboardStatus } from "@/types/enums";

const NEXT_STATUSES: Record<string, StoryboardStatus[]> = {
  [StoryboardStatus.DRAFT]: [StoryboardStatus.READY],
  [StoryboardStatus.READY]: [StoryboardStatus.APPROVED, StoryboardStatus.DRAFT],
  [StoryboardStatus.APPROVED]: [],
};

export default function StoryboardsPage() {
  const { projectId } = useSelectionStore();
  const { data: storyboard, isLoading } = useStoryboard(projectId ?? "");
  const { data: scripts } = useScripts(projectId ?? "");
  const createStoryboard = useCreateStoryboard(projectId ?? "");
  const updateStatus = useUpdateStoryboardStatus(projectId ?? "");
  const { data: scenes } = useScenes(storyboard?.id);
  const addScene = useAddScene(storyboard?.id ?? "");
  const toast = useToast();

  const [sceneDialogOpen, setSceneDialogOpen] = useState(false);
  const [description, setDescription] = useState("");
  const [duration, setDuration] = useState("8");

  if (!projectId) {
    return (
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[--color-text] dark:text-[--color-text-dark]">Storyboards</h1>
        <ProjectPicker />
      </div>
    );
  }

  const approvedScript = scripts?.items.find((s) => s.status === "approved");

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[--color-text] dark:text-[--color-text-dark]">Storyboards</h1>
        <ProjectPicker />
      </div>

      {isLoading ? (
        <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">Loading…</p>
      ) : !storyboard ? (
        <Card>
          <p className="mb-3 text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">
            {approvedScript
              ? "No storyboard yet for this project."
              : "This project needs an approved script before a storyboard can be created."}
          </p>
          {approvedScript && (
            <Button
              isLoading={createStoryboard.isPending}
              onClick={() =>
                createStoryboard.mutate(approvedScript.id, {
                  onError: () => toast.error("Failed to create storyboard"),
                })
              }
            >
              Create storyboard
            </Button>
          )}
        </Card>
      ) : (
        <>
          <Card>
            <div className="flex items-center justify-between">
              <StatusBadge status={storyboard.status} />
              <div className="flex gap-2">
                {(NEXT_STATUSES[storyboard.status] ?? []).map((status) => (
                  <Button
                    key={status}
                    size="sm"
                    variant="secondary"
                    isLoading={updateStatus.isPending}
                    onClick={() =>
                      updateStatus.mutate(
                        { storyboardId: storyboard.id, data: { status } },
                        { onError: () => toast.error("Status transition failed") },
                      )
                    }
                  >
                    {status}
                  </Button>
                ))}
                <Button size="sm" onClick={() => setSceneDialogOpen(true)}>
                  Add scene
                </Button>
              </div>
            </div>
          </Card>

          <SceneTimeline storyboardId={storyboard.id} />

          <Dialog open={sceneDialogOpen} onClose={() => setSceneDialogOpen(false)} title="Add scene">
            <div className="flex flex-col gap-3">
              <div>
                <Label htmlFor="scene-description">Description</Label>
                <Textarea id="scene-description" value={description} onChange={(e) => setDescription(e.target.value)} />
              </div>
              <div>
                <Label htmlFor="scene-duration">Duration (seconds)</Label>
                <Input
                  id="scene-duration"
                  type="number"
                  min={1}
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                />
              </div>
              <div className="flex justify-end">
                <Button
                  disabled={!description}
                  isLoading={addScene.isPending}
                  onClick={() => {
                    const nextIndex = scenes?.length ?? 0;
                    addScene.mutate(
                      { sequence_index: nextIndex, description, duration_seconds: duration },
                      {
                        onSuccess: () => {
                          toast.success("Scene added");
                          setDescription("");
                          setSceneDialogOpen(false);
                        },
                        onError: () => toast.error("Failed to add scene"),
                      },
                    );
                  }}
                >
                  Add
                </Button>
              </div>
            </div>
          </Dialog>
        </>
      )}
    </div>
  );
}
