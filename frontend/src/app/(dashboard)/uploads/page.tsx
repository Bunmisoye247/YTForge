"use client";

import { useState } from "react";
import { useSelectionStore } from "@/lib/stores/selection-store";
import { useRequestPublishApproval, useSeoMetadata, useSetSeoMetadata, useUpdateVideo, useVideos } from "@/lib/hooks/use-videos";
import { useToast } from "@/lib/stores/toast-store";
import { ProjectPicker } from "@/components/layout/ProjectPicker";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Input";
import { VideoStatus } from "@/types/enums";
import type { VideoRead } from "@/lib/api/schemas/videos";

function SeoEditor({ videoId }: { videoId: string }) {
  const { data: seo } = useSeoMetadata(videoId);
  const setSeo = useSetSeoMetadata(videoId);
  const toast = useToast();
  const [title, setTitle] = useState(seo?.title ?? "");
  const [description, setDescription] = useState(seo?.description ?? "");

  return (
    <div className="mt-3 flex flex-col gap-2 border-t border-[--color-border] pt-3 dark:border-[--color-border-dark]">
      <div className="text-xs font-medium text-[--color-text-muted] dark:text-[--color-text-muted-dark]">SEO metadata</div>
      <Input
        placeholder="SEO title"
        value={title || seo?.title || ""}
        onChange={(e) => setTitle(e.target.value)}
        maxLength={100}
      />
      <Textarea
        placeholder="SEO description"
        value={description || seo?.description || ""}
        onChange={(e) => setDescription(e.target.value)}
      />
      <div className="flex justify-end">
        <Button
          size="sm"
          isLoading={setSeo.isPending}
          onClick={() =>
            setSeo.mutate(
              { title: title || seo?.title || "", description: description || seo?.description || "" },
              {
                onSuccess: () => toast.success("SEO metadata saved"),
                onError: () => toast.error("Failed to save SEO metadata"),
              },
            )
          }
        >
          Save SEO
        </Button>
      </div>
    </div>
  );
}

function UploadCard({ video, projectId }: { video: VideoRead; projectId: string }) {
  const updateVideo = useUpdateVideo(projectId);
  const requestPublish = useRequestPublishApproval();
  const toast = useToast();
  const [title, setTitle] = useState(video.title);
  const [description, setDescription] = useState(video.description);
  const [showSeo, setShowSeo] = useState(false);

  return (
    <Card>
      <div className="mb-2 flex items-center justify-between">
        <StatusBadge status={video.status} />
      </div>
      {video.status === VideoStatus.DRAFT ? (
        <>
          <Input className="mb-2" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={100} />
          <Textarea value={description} onChange={(e) => setDescription(e.target.value)} />
          <div className="mt-2 flex justify-between">
            <Button
              size="sm"
              variant="secondary"
              isLoading={updateVideo.isPending}
              onClick={() =>
                updateVideo.mutate(
                  { videoId: video.id, data: { title, description } },
                  {
                    onSuccess: () => toast.success("Draft saved"),
                    onError: () => toast.error("Failed to save draft"),
                  },
                )
              }
            >
              Save draft
            </Button>
            <Button
              size="sm"
              isLoading={requestPublish.isPending}
              onClick={() =>
                requestPublish.mutate(video.id, {
                  onSuccess: () => toast.success("Publish approval requested"),
                  onError: () => toast.error("Failed to request approval"),
                })
              }
            >
              Request publish approval
            </Button>
          </div>
        </>
      ) : (
        <div>
          <div className="font-medium text-[--color-text] dark:text-[--color-text-dark]">{video.title}</div>
          <div className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">{video.description}</div>
        </div>
      )}

      <Button variant="ghost" size="sm" className="mt-3" onClick={() => setShowSeo((v) => !v)}>
        {showSeo ? "Hide SEO" : "Edit SEO"}
      </Button>
      {showSeo && <SeoEditor videoId={video.id} />}
    </Card>
  );
}

export default function UploadsPage() {
  const { projectId } = useSelectionStore();
  const { data: videoPage, isLoading } = useVideos(projectId ?? "");

  const uploadCandidates = (videoPage?.items ?? []).filter(
    (v) => v.status === VideoStatus.DRAFT || v.status === VideoStatus.SCHEDULED,
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[--color-text] dark:text-[--color-text-dark]">Uploads</h1>
        <ProjectPicker />
      </div>

      {!projectId ? (
        <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">Select a project.</p>
      ) : (
        <>
          <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">
            The actual YouTube upload is Phase 8 — this manages draft videos and requests the
            publish approval that a later phase will act on.
          </p>
          {isLoading ? (
            <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">Loading…</p>
          ) : uploadCandidates.length === 0 ? (
            <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">No draft or scheduled videos.</p>
          ) : (
            <div className="flex flex-col gap-4">
              {uploadCandidates.map((video) => (
                <UploadCard key={video.id} video={video} projectId={projectId} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
