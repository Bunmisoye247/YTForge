"use client";

import { useScenes, useReorderScenes, useGenerateSceneImage } from "@/lib/hooks/use-storyboards";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/lib/stores/toast-store";
import { formatDuration } from "@/lib/utils/format";

/** Reorders via move-up/move-down rather than full drag-and-drop — no extra
 * dependency, same end result (calls the backend's scenes/reorder
 * endpoint), and simpler to keep accessible. */
export function SceneTimeline({ storyboardId, projectId }: { storyboardId: string; projectId: string }) {
  const { data: scenes, isLoading } = useScenes(storyboardId);
  const reorder = useReorderScenes(storyboardId);
  const generateImage = useGenerateSceneImage(projectId);
  const toast = useToast();

  if (isLoading) return <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">Loading…</p>;
  if (!scenes || scenes.length === 0) {
    return <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">No scenes yet.</p>;
  }

  const move = (index: number, direction: -1 | 1) => {
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= scenes.length) return;
    const ids = scenes.map((s) => s.id);
    [ids[index], ids[targetIndex]] = [ids[targetIndex]!, ids[index]!];
    reorder.mutate(ids);
  };

  return (
    <div className="flex flex-col gap-3">
      {scenes.map((scene, index) => (
        <Card key={scene.id} className="flex items-start justify-between gap-4">
          <div>
            <div className="mb-1 text-xs font-medium text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
              Scene {index + 1} · {formatDuration(scene.duration_seconds)}
            </div>
            <p className="text-sm text-(--color-text) dark:text-(--color-text-dark)">{scene.description}</p>
            {scene.voice_line && (
              <p className="mt-1 text-sm italic text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
                &ldquo;{scene.voice_line}&rdquo;
              </p>
            )}
          </div>
          <div className="flex shrink-0 flex-col gap-1">
            <Button variant="secondary" size="sm" disabled={index === 0} onClick={() => move(index, -1)}>
              Move up
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={index === scenes.length - 1}
              onClick={() => move(index, 1)}
            >
              Move down
            </Button>
            <Button
              size="sm"
              isLoading={generateImage.isPending && generateImage.variables === scene.id}
              onClick={() =>
                generateImage.mutate(scene.id, {
                  onSuccess: () => toast.success("Image generated"),
                  onError: () => toast.error("Image generation failed"),
                })
              }
            >
              Generate image
            </Button>
          </div>
        </Card>
      ))}
    </div>
  );
}
