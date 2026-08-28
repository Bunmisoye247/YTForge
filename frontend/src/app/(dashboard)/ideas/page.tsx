"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSelectionStore } from "@/lib/stores/selection-store";
import { useRecordTrend, useTrends } from "@/lib/hooks/use-trends";
import { useCreateProject } from "@/lib/hooks/use-projects";
import { useStartPipeline } from "@/lib/hooks/use-pipeline-status";
import { useToast } from "@/lib/stores/toast-store";
import { Table, TablePagination, type Column } from "@/components/ui/Table";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { Input, Label } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { TrendSource } from "@/types/enums";
import type { TrendRead } from "@/lib/api/schemas/trends";

const SOURCES = Object.values(TrendSource);

export default function IdeasPage() {
  const { channelId, setProjectId } = useSelectionStore();
  const router = useRouter();
  const [offset, setOffset] = useState(0);
  const [open, setOpen] = useState(false);
  const [topic, setTopic] = useState("");
  const [source, setSource] = useState<TrendSource>(TrendSource.GOOGLE_TRENDS);
  const [url, setUrl] = useState("");
  const [score, setScore] = useState("");
  const [startingTrend, setStartingTrend] = useState<TrendRead | null>(null);
  const [projectTitle, setProjectTitle] = useState("");

  const { data: page, isLoading } = useTrends(channelId ?? "", { limit: 20, offset });
  const recordTrend = useRecordTrend(channelId ?? "");
  const createProject = useCreateProject(channelId ?? "");
  const startPipeline = useStartPipeline();
  const toast = useToast();

  if (!channelId) {
    return <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">Select a channel to see its ideas.</p>;
  }

  const handleCreate = () => {
    const parsedScore = Number(score);
    recordTrend.mutate(
      {
        topic,
        source,
        url: url.trim() ? url.trim() : null,
        score: score.trim() && !Number.isNaN(parsedScore) ? parsedScore : undefined,
      },
      {
        onSuccess: () => {
          toast.success("Trend recorded");
          setTopic("");
          setUrl("");
          setScore("");
          setOpen(false);
        },
        onError: () => toast.error("Failed to record trend"),
      },
    );
  };

  const handleStartProject = () => {
    if (!startingTrend) return;
    createProject.mutate(
      { title: projectTitle, trend_id: startingTrend.id },
      {
        onSuccess: (project) => {
          setProjectId(project.id);
          setStartingTrend(null);
          router.push("/scripts");
          startPipeline.mutate(
            { project_id: project.id, topic: projectTitle },
            {
              onSuccess: () => toast.success("Project started — generating script"),
              onError: () => toast.error("Project created, but script generation failed to start"),
            },
          );
        },
        onError: () => toast.error("Failed to start project"),
      },
    );
  };

  const rationaleOf = (t: TrendRead) => {
    const rationale = t.raw_payload?.rationale;
    return typeof rationale === "string" && rationale.length > 0 ? rationale : null;
  };

  const columns: Column<TrendRead>[] = [
    { header: "Topic", cell: (t) => t.topic },
    { header: "Source", cell: (t) => t.source },
    { header: "Score", cell: (t) => t.score.toFixed(1) },
    {
      header: "Why",
      cell: (t) => {
        const rationale = rationaleOf(t);
        return rationale ? (
          <span
            title={rationale}
            className="block max-w-xs truncate text-(--color-text-muted) dark:text-(--color-text-muted-dark)"
          >
            {rationale}
          </span>
        ) : (
          <span className="text-(--color-text-muted) dark:text-(--color-text-muted-dark)">—</span>
        );
      },
    },
    {
      header: "Link",
      cell: (t) =>
        t.url ? (
          <a href={t.url} target="_blank" rel="noreferrer" className="text-(--color-accent) dark:text-(--color-accent-dark)">
            Open
          </a>
        ) : null,
    },
    {
      header: "",
      cell: (t) => (
        <Button
          size="sm"
          variant="secondary"
          onClick={() => {
            setStartingTrend(t);
            setProjectTitle(t.topic);
          }}
        >
          Start project
        </Button>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-(--color-text) dark:text-(--color-text-dark)">Ideas</h1>
          <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
            Ranked by score, highest first. The trend discovery cron scores and records candidates here
            automatically every day — add one manually below to fast-track it into the ranking.
          </p>
        </div>
        <Button onClick={() => setOpen(true)}>Record trend</Button>
      </div>

      <Table columns={columns} rows={page?.items ?? []} rowKey={(t) => t.id} isLoading={isLoading} />
      <TablePagination page={page} onOffsetChange={setOffset} />

      <Dialog open={open} onClose={() => setOpen(false)} title="Record trend">
        <div className="flex flex-col gap-3">
          <div>
            <Label htmlFor="trend-topic">Topic</Label>
            <Input id="trend-topic" value={topic} onChange={(e) => setTopic(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="trend-source">Source</Label>
            <Select id="trend-source" value={source} onChange={(e) => setSource(e.target.value as TrendSource)}>
              {SOURCES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="trend-url">Link (optional)</Label>
            <Input id="trend-url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://…" />
          </div>
          <div>
            <Label htmlFor="trend-score">Score (optional, 0–100)</Label>
            <Input
              id="trend-score"
              type="number"
              min={0}
              max={100}
              step="0.1"
              value={score}
              onChange={(e) => setScore(e.target.value)}
              placeholder="0.0"
            />
          </div>
          <div className="flex justify-end">
            <Button isLoading={recordTrend.isPending} disabled={!topic} onClick={handleCreate}>
              Record
            </Button>
          </div>
        </div>
      </Dialog>

      <Dialog open={startingTrend !== null} onClose={() => setStartingTrend(null)} title="Start project from idea">
        <div className="flex flex-col gap-3">
          <div>
            <Label htmlFor="new-project-title">Project title</Label>
            <Input id="new-project-title" value={projectTitle} onChange={(e) => setProjectTitle(e.target.value)} />
          </div>
          <div className="flex justify-end">
            <Button
              isLoading={createProject.isPending || startPipeline.isPending}
              disabled={!projectTitle}
              onClick={handleStartProject}
            >
              Start project
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
