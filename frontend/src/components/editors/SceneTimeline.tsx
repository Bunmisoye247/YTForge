"use client";

import { useScenes, useReorderScenes, useGenerateSceneImage } from "@/lib/hooks/use-storyboards";
import { useAssets, useAssetPresignedUrl } from "@/lib/hooks/use-assets";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/lib/stores/toast-store";
import { formatDuration } from "@/lib/utils/format";
import { AssetType, AssetStatus } from "@/types/enums";
import type { AssetRead } from "@/lib/api/schemas/assets";

function latestImageForScene(assets: AssetRead[] | undefined, sceneId: string): AssetRead | undefined {
  const matches = (assets ?? []).filter((a) => a.scene_id === sceneId && a.asset_type === AssetType.IMAGE);
  return matches.at(-1);
}

/** Reorders via move-up/move-down rather than full drag-and-drop — no extra
 * dependency, same end result (calls the backend's scenes/reorder
 * endpoint), and simpler to keep accessible. */
export function SceneTimeline({ storyboardId, projectId }: { storyboardId: string; projectId: string }) {
  const { data: scenes, isLoading } = useScenes(storyboardId);
  const { data: assetsPage } = useAssets(projectId, { limit: 200 });
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
      {scenes.map((scene, index) => {
        const image = latestImageForScene(assetsPage?.items, scene.id);
        const isGenerating = generateImage.isPending && generateImage.variables === scene.id;

        return (
          <Card key={scene.id} className="flex items-start gap-4">
            <SceneImageThumb asset={image} isGenerating={isGenerating} />

            <div className="flex-1">
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
                isLoading={isGenerating}
                onClick={() =>
                  generateImage.mutate(scene.id, {
                    onSuccess: () => toast.success("Image generated"),
                    onError: () => toast.error("Image generation failed"),
                  })
                }
              >
                {image ? "Regenerate image" : "Generate image"}
              </Button>
            </div>
          </Card>
        );
      })}
    </div>
  );
}

function SceneImageThumb({ asset, isGenerating }: { asset: AssetRead | undefined; isGenerating: boolean }) {
  const { data: presigned } = useAssetPresignedUrl(asset?.status === AssetStatus.READY ? asset.id : undefined);

  return (
    <div className="flex h-20 w-32 shrink-0 items-center justify-center overflow-hidden rounded-md border border-(--color-border) bg-(--color-surface-2) text-center dark:border-(--color-border-dark) dark:bg-(--color-surface-2-dark)">
      {isGenerating ? (
        <span className="px-2 text-xs text-(--color-text-muted) dark:text-(--color-text-muted-dark)">Generating…</span>
      ) : presigned?.url ? (
        // Presigned MinIO URLs are dynamic, signed, and expiring — not a
        // fixed remote host next/image's static allow-list config expects.
        // eslint-disable-next-line @next/next/no-img-element
        <img src={presigned.url} alt="" className="h-full w-full object-cover" />
      ) : asset?.status === AssetStatus.FAILED ? (
        <span className="px-2 text-xs text-(--color-danger) dark:text-(--color-danger-dark)">Generation failed</span>
      ) : asset?.status === AssetStatus.PENDING ? (
        <span className="px-2 text-xs text-(--color-text-muted) dark:text-(--color-text-muted-dark)">Pending…</span>
      ) : (
        <span className="px-2 text-xs text-(--color-text-muted) dark:text-(--color-text-muted-dark)">No image</span>
      )}
    </div>
  );
}
