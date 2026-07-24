"use client";

import { useSelectionStore } from "@/lib/stores/selection-store";
import { useMyChannels } from "@/lib/hooks/use-channels";
import { useProjects } from "@/lib/hooks/use-projects";
import { useApprovals } from "@/lib/hooks/use-approvals";
import { PipelineTracker } from "@/components/pipeline/PipelineTracker";
import { Card } from "@/components/ui/Card";
import { ApprovalStatus } from "@/types/enums";

function KpiTile({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <div className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-[--color-text] dark:text-[--color-text-dark]">{value}</div>
    </Card>
  );
}

export default function OverviewPage() {
  const { channelId } = useSelectionStore();
  const { data: channels } = useMyChannels();
  const { data: projectPage } = useProjects(channelId ?? "", { limit: 1 });
  const { data: pendingApprovals } = useApprovals(ApprovalStatus.PENDING, { limit: 1 });

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold text-[--color-text] dark:text-[--color-text-dark]">Overview</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <KpiTile label="Channels" value={channels?.length ?? "—"} />
        <KpiTile label="Projects (current channel)" value={projectPage?.total ?? "—"} />
        <KpiTile label="Pending approvals" value={pendingApprovals?.total ?? "—"} />
      </div>

      <PipelineTracker />
    </div>
  );
}
