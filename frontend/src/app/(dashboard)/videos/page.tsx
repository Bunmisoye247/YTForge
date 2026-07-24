"use client";

import { useState } from "react";
import { useSelectionStore } from "@/lib/stores/selection-store";
import { useAssets } from "@/lib/hooks/use-assets";
import { useCreateVideo, useVideos } from "@/lib/hooks/use-videos";
import { useToast } from "@/lib/stores/toast-store";
import { ProjectPicker } from "@/components/layout/ProjectPicker";
import { AssetGallery } from "@/components/editors/AssetGallery";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { Input, Label, Textarea } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { AssetType, AssetStatus } from "@/types/enums";
import Link from "next/link";

export default function VideosPage() {
  const { projectId } = useSelectionStore();
  const { data: videoPage, isLoading } = useVideos(projectId ?? "");
  const { data: assetPage } = useAssets(projectId ?? "", { limit: 50 });
  const createVideo = useCreateVideo(projectId ?? "");
  const toast = useToast();

  const [open, setOpen] = useState(false);
  const [renderAssetId, setRenderAssetId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const renderAssets = (assetPage?.items ?? []).filter(
    (a) => a.asset_type === AssetType.RENDER && a.status === AssetStatus.READY,
  );

  const handleCreate = () => {
    createVideo.mutate(
      { render_asset_id: renderAssetId, title, description },
      {
        onSuccess: () => {
          toast.success("Video created");
          setTitle("");
          setDescription("");
          setOpen(false);
        },
        onError: () => toast.error("Failed to create video"),
      },
    );
  };

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[--color-text] dark:text-[--color-text-dark]">Videos</h1>
        <ProjectPicker />
      </div>

      {!projectId ? (
        <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">Select a project.</p>
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Video entities</CardTitle>
              <Button size="sm" disabled={renderAssets.length === 0} onClick={() => setOpen(true)}>
                New video
              </Button>
            </CardHeader>
            {renderAssets.length === 0 && (
              <p className="mb-2 text-xs text-[--color-text-muted] dark:text-[--color-text-muted-dark]">
                No ready render assets yet — register one below before creating a video.
              </p>
            )}
            {isLoading ? (
              <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">Loading…</p>
            ) : (
              <div className="flex flex-col gap-2">
                {videoPage?.items.map((video) => (
                  <div key={video.id} className="flex items-center justify-between rounded-md border border-[--color-border] p-3 text-sm dark:border-[--color-border-dark]">
                    <div>
                      <div className="font-medium text-[--color-text] dark:text-[--color-text-dark]">{video.title}</div>
                      <div className="text-xs text-[--color-text-muted] dark:text-[--color-text-muted-dark]">{video.description}</div>
                    </div>
                    <div className="flex items-center gap-3">
                      <StatusBadge status={video.status} />
                      <Link href={`/uploads`} className="text-xs text-[--color-accent] dark:text-[--color-accent-dark]">
                        Manage in Uploads →
                      </Link>
                    </div>
                  </div>
                ))}
                {videoPage?.items.length === 0 && (
                  <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">No videos yet.</p>
                )}
              </div>
            )}
          </Card>

          <div>
            <h2 className="mb-3 text-sm font-semibold text-[--color-text-muted] dark:text-[--color-text-muted-dark]">
              Clips, audio, music &amp; render assets
            </h2>
            <AssetGallery
              projectId={projectId}
              types={[AssetType.CLIP, AssetType.AUDIO, AssetType.MUSIC, AssetType.RENDER]}
            />
          </div>
        </>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} title="New video">
        <div className="flex flex-col gap-3">
          <div>
            <Label htmlFor="render-asset">Render asset</Label>
            <Select id="render-asset" value={renderAssetId} onChange={(e) => setRenderAssetId(e.target.value)}>
              <option value="">Select…</option>
              {renderAssets.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.object_key}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="video-title">Title</Label>
            <Input id="video-title" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={100} />
          </div>
          <div>
            <Label htmlFor="video-description">Description</Label>
            <Textarea id="video-description" value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div className="flex justify-end">
            <Button
              isLoading={createVideo.isPending}
              disabled={!renderAssetId || !title || !description}
              onClick={handleCreate}
            >
              Create
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
