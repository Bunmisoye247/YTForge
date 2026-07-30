"use client";

import Link from "next/link";
import { useSelectionStore } from "@/lib/stores/selection-store";
import { useMyChannels } from "@/lib/hooks/use-channels";
import { useProjects } from "@/lib/hooks/use-projects";
import { useApprovals } from "@/lib/hooks/use-approvals";
import { PipelineTracker } from "@/components/pipeline/PipelineTracker";
import { PipelineRail } from "@/components/pipeline/PipelineRail";
import { Card, EmptyState } from "@/components/ui";
import { Button } from "@/components/ui/Button";
import { IconChannels, IconProjects, IconApprovals } from "@/components/ui/icons";
import { ApprovalStatus } from "@/types/enums";
import type { ReactNode } from "react";

function StatCard({
  icon,
  label,
  value,
  meta,
  metaTone = "muted",
}: {
  icon: ReactNode;
  label: string;
  value: string | number;
  meta?: string;
  metaTone?: "muted" | "good" | "warn";
}) {
  return (
    <Card>
      <div className="flex items-center gap-2 text-[13px] text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
        {icon}
        {label}
      </div>
      <div className="mt-1.5 font-display text-[32px] font-bold tracking-tight text-(--color-text) dark:text-(--color-text-dark)">
        {value}
      </div>
      {meta && (
        <div
          className={
            metaTone === "good"
              ? "mt-1 text-[12.5px] text-(--color-success) dark:text-(--color-success-dark)"
              : metaTone === "warn"
                ? "mt-1 text-[12.5px] text-(--color-accent) dark:text-(--color-accent-dark)"
                : "mt-1 text-[12.5px] text-(--color-text-muted) dark:text-(--color-text-muted-dark)"
          }
        >
          {meta}
        </div>
      )}
    </Card>
  );
}

export default function OverviewPage() {
  const { channelId, projectId } = useSelectionStore();
  const { data: channels } = useMyChannels();
  const { data: projectPage } = useProjects(channelId ?? "", { limit: 100 });
  const { data: pendingApprovals } = useApprovals(ApprovalStatus.PENDING, { limit: 1 });

  const currentChannel = channels?.find((c) => c.id === channelId);
  const currentProject = projectPage?.items.find((p) => p.id === projectId);
  const pendingCount = pendingApprovals?.total ?? 0;

  return (
    <div className="flex max-w-[1080px] flex-col gap-5">
      <div className="mb-1 flex items-end gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-(--color-text) dark:text-(--color-text-dark)">Production overview</h1>
          <p className="mt-0.5 text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
            {currentChannel ? `${currentChannel.name} · everything currently moving through the forge` : "Everything currently moving through the forge"}
          </p>
        </div>
        <Link href="/projects" className="ml-auto">
          <Button>+ New project</Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-3">
        <StatCard
          icon={<IconChannels className="h-[15px] w-[15px]" />}
          label="Channels"
          value={channels?.length ?? "—"}
          meta={channels?.length === 1 ? `${channels[0]!.name} active` : undefined}
        />
        <StatCard
          icon={<IconProjects className="h-[15px] w-[15px]" />}
          label="Projects in flight"
          value={projectPage?.total ?? "—"}
          meta={!channelId ? undefined : "in this channel"}
        />
        <StatCard
          icon={<IconApprovals className="h-[15px] w-[15px]" />}
          label="Pending approvals"
          value={pendingCount}
          meta={pendingCount > 0 ? `${pendingCount} awaiting review` : "Nothing blocking you"}
          metaTone={pendingCount > 0 ? "warn" : "good"}
        />
      </div>

      {channelId && projectId && currentProject ? (
        <PipelineRail channelId={channelId} projectId={projectId} projectTitle={currentProject.title} />
      ) : (
        <EmptyState
          icon={<IconProjects />}
          title="No project selected"
          description="Pick a project from the switcher up top to see its pipeline progress here."
        />
      )}

      <PipelineTracker projectId={projectId ?? undefined} />
    </div>
  );
}
