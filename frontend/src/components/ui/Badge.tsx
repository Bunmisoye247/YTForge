import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";
import { titleCase } from "@/lib/utils/format";

type Tone = "neutral" | "info" | "success" | "warning" | "danger";

const toneClasses: Record<Tone, string> = {
  neutral:
    "bg-[--color-surface] text-[--color-text-muted] dark:bg-[--color-surface-dark] dark:text-[--color-text-muted-dark]",
  info: "bg-sky-100 text-sky-700 dark:bg-sky-950 dark:text-sky-300",
  success: "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300",
  warning: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  danger: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300",
};

export function Badge({
  tone = "neutral",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        toneClasses[tone],
        className,
      )}
      {...props}
    />
  );
}

// Several enum families (ProjectStatus, ScriptStatus, StoryboardStatus,
// AssetStatus, VideoStatus, ApprovalStatus, JobStatus, FactCheckVerdict,
// VoiceProfileStatus, ModelAvailability) share string values like "draft",
// "approved", "pending", "failed" — this is a single flat map keyed by the
// literal value, not by family, so each value appears exactly once here
// with one tone that reads sensibly across every family that uses it.
const TONE_BY_VALUE: Record<string, Tone> = {
  idea: "neutral",
  in_progress: "info",
  in_review: "warning",
  completed: "success",
  archived: "neutral",
  draft: "neutral",
  approved: "success",
  rejected: "danger",
  ready: "info",
  pending: "warning",
  failed: "danger",
  orphaned: "neutral",
  uploaded: "info",
  scheduled: "info",
  published: "success",
  running: "info",
  terminated: "neutral",
  timed_out: "danger",
  cancelled: "neutral",
  passed: "success",
  flagged: "danger",
  pending_approval: "warning",
  revoked: "danger",
  available: "success",
  unavailable: "neutral",
};

function statusTone(value: string): Tone {
  return TONE_BY_VALUE[value] ?? "neutral";
}

export function StatusBadge({ status }: { status: string }) {
  return <Badge tone={statusTone(status)}>{titleCase(status)}</Badge>;
}
