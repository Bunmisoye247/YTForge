import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";
import { titleCase } from "@/lib/utils/format";

type Tone = "neutral" | "info" | "success" | "warning" | "danger";

const toneClasses: Record<Tone, string> = {
  neutral:
    "bg-(--color-surface-2) text-(--color-text-muted) dark:bg-(--color-surface-2-dark) dark:text-(--color-text-muted-dark)",
  info: "bg-(--color-info)/12 text-(--color-info) dark:bg-(--color-info-dark)/15 dark:text-(--color-info-dark)",
  success:
    "bg-(--color-success)/12 text-(--color-success) dark:bg-(--color-success-dark)/15 dark:text-(--color-success-dark)",
  warning:
    "bg-(--color-warning)/12 text-(--color-warning) dark:bg-(--color-warning-dark)/15 dark:text-(--color-warning-dark)",
  danger:
    "bg-(--color-danger)/12 text-(--color-danger) dark:bg-(--color-danger-dark)/15 dark:text-(--color-danger-dark)",
};

export function Badge({
  tone = "neutral",
  pulse = false,
  className,
  children,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: Tone; pulse?: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold",
        toneClasses[tone],
        className,
      )}
      {...props}
    >
      <span className={cn("h-1.5 w-1.5 shrink-0 rounded-full bg-current", pulse && "animate-pulse")} />
      {children}
    </span>
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
  return (
    <Badge tone={statusTone(status)} pulse={status === "running"}>
      {titleCase(status)}
    </Badge>
  );
}
