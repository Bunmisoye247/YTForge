"use client";

import type { ReactNode } from "react";
import { useProjects } from "@/lib/hooks/use-projects";
import { useScripts } from "@/lib/hooks/use-scripts";
import { useStoryboard } from "@/lib/hooks/use-storyboards";
import { useAssets } from "@/lib/hooks/use-assets";
import { useVideos } from "@/lib/hooks/use-videos";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { titleCase } from "@/lib/utils/format";
import { ProjectStatus, ScriptStatus, StoryboardStatus, VideoStatus, AssetStatus } from "@/types/enums";
import { IconCheck, IconIdeas, IconScripts, IconStoryboards, IconImages, IconVideos, IconUploads } from "@/components/ui/icons";

type StageState = "done" | "current" | "pending";
type Stage = { name: string; state: StageState; label: string; icon: (props: { className?: string }) => ReactNode };

const UPLOADED_STATUSES: readonly string[] = [VideoStatus.UPLOADED, VideoStatus.SCHEDULED, VideoStatus.PUBLISHED];

/** Derives each stage's real state from the project/scripts/storyboard/
 * assets/videos already fetched for this project — nothing here is
 * fabricated; a stage with no data simply reads "queued". */
function useStages(channelId: string, projectId: string): Stage[] | null {
  const { data: projectPage } = useProjects(channelId, { limit: 100 });
  const { data: scriptPage } = useScripts(projectId);
  const { data: storyboard } = useStoryboard(projectId);
  const { data: assetPage } = useAssets(projectId, { limit: 100 });
  const { data: videoPage } = useVideos(projectId, { limit: 20 });

  const project = projectPage?.items.find((p) => p.id === projectId);
  if (!project) return null;

  const scripts = scriptPage?.items ?? [];
  const approvedScript = scripts.find((s) => s.status === ScriptStatus.APPROVED);
  const latestScript = scripts[0];

  const assets = assetPage?.items ?? [];
  const readyAssetCount = assets.filter((a) => a.status === AssetStatus.READY).length;

  const videos = videoPage?.items ?? [];
  const uploadedVideo = videos.find((v) => UPLOADED_STATUSES.includes(v.status));
  const draftVideo = videos.find((v) => v.status === VideoStatus.DRAFT);

  const ideaDone = project.status !== ProjectStatus.IDEA;
  const scriptDone = Boolean(approvedScript);
  const scriptCurrent = !scriptDone && scripts.length > 0;
  const storyboardDone = storyboard?.status === StoryboardStatus.APPROVED;
  const storyboardCurrent = Boolean(storyboard) && !storyboardDone;
  const assetsDone = readyAssetCount > 0;
  const assetsCurrent = !assetsDone && assets.length > 0;
  const videoDone = Boolean(uploadedVideo);
  const videoCurrent = !videoDone && Boolean(draftVideo);

  return [
    {
      name: "Idea",
      icon: IconIdeas,
      state: ideaDone ? "done" : "current",
      label: ideaDone ? "approved" : "in progress",
    },
    {
      name: "Script",
      icon: IconScripts,
      state: scriptDone ? "done" : scriptCurrent ? "current" : "pending",
      label: scriptDone ? "approved" : latestScript ? titleCase(latestScript.status) : "queued",
    },
    {
      name: "Storyboard",
      icon: IconStoryboards,
      state: storyboardDone ? "done" : storyboardCurrent ? "current" : "pending",
      label: storyboardDone ? "approved" : storyboard ? titleCase(storyboard.status) : "queued",
    },
    {
      name: "Assets",
      icon: IconImages,
      state: assetsDone ? "done" : assetsCurrent ? "current" : "pending",
      label: assetsDone ? "ready" : assetsCurrent ? `${assets.length} registered` : "queued",
    },
    {
      name: "Video",
      icon: IconVideos,
      state: videoDone ? "done" : videoCurrent ? "current" : "pending",
      label: videoDone ? "ready" : videoCurrent ? "draft" : "queued",
    },
    {
      name: "Upload",
      icon: IconUploads,
      state: videoDone ? "done" : "pending",
      label: videoDone ? titleCase(uploadedVideo!.status) : "queued",
    },
  ];
}

export function PipelineRail({ channelId, projectId, projectTitle }: { channelId: string; projectId: string; projectTitle: string }) {
  const stages = useStages(channelId, projectId);

  if (!stages) return null;

  const doneCount = stages.filter((s) => s.state === "done").length;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{projectTitle} — pipeline</CardTitle>
        <span className="ml-auto font-mono text-xs text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
          stage {Math.min(doneCount + 1, stages.length)} / {stages.length}
        </span>
      </CardHeader>
      <div className="flex items-start">
        {stages.map((stage, i) => {
          const Icon = stage.icon;
          return (
            <div key={stage.name} className="relative flex min-w-0 flex-1 flex-col items-center">
              {i < stages.length - 1 && (
                <div
                  className={`absolute top-[15px] left-[calc(50%+17px)] h-0.5 w-[calc(100%-34px)] ${
                    stage.state === "done"
                      ? "bg-(--color-success) dark:bg-(--color-success-dark)"
                      : "bg-(--color-border) dark:bg-(--color-border-dark)"
                  }`}
                />
              )}
              <div
                className={`z-10 flex h-[30px] w-[30px] items-center justify-center rounded-full border-[1.5px] ${
                  stage.state === "done"
                    ? "border-(--color-success) bg-(--color-success)/12 text-(--color-success) dark:border-(--color-success-dark) dark:bg-(--color-success-dark)/15 dark:text-(--color-success-dark)"
                    : stage.state === "current"
                      ? "animate-pulse motion-reduce:animate-none border-(--color-accent) bg-(--color-accent)/12 text-(--color-accent) shadow-[0_0_0_4px_rgba(240,163,63,0.10)] dark:border-(--color-accent-dark) dark:bg-(--color-accent-dark)/15 dark:text-(--color-accent-dark)"
                      : "border-(--color-border) bg-(--color-surface-2) text-(--color-text-muted) dark:border-(--color-border-dark) dark:bg-(--color-surface-2-dark) dark:text-(--color-text-muted-dark)"
                }`}
              >
                {stage.state === "done" ? <IconCheck className="h-3.5 w-3.5" /> : <Icon className="h-3.5 w-3.5" />}
              </div>
              <div className="mt-2 text-[12.5px] font-semibold text-(--color-text) dark:text-(--color-text-dark)">
                {stage.name}
              </div>
              <div
                className={`font-mono text-[10.5px] ${
                  stage.state === "done"
                    ? "text-(--color-success) dark:text-(--color-success-dark)"
                    : stage.state === "current"
                      ? "text-(--color-accent) dark:text-(--color-accent-dark)"
                      : "text-(--color-text-muted) dark:text-(--color-text-muted-dark)"
                }`}
              >
                {stage.label}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
