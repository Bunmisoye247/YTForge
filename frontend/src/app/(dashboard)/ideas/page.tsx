"use client";

import { useState } from "react";
import { useSelectionStore } from "@/lib/stores/selection-store";
import { useRecordTrend, useTrends } from "@/lib/hooks/use-trends";
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
  const { channelId } = useSelectionStore();
  const [offset, setOffset] = useState(0);
  const [open, setOpen] = useState(false);
  const [topic, setTopic] = useState("");
  const [source, setSource] = useState<TrendSource>(TrendSource.GOOGLE_TRENDS);

  const { data: page, isLoading } = useTrends(channelId ?? "", { limit: 20, offset });
  const recordTrend = useRecordTrend(channelId ?? "");
  const toast = useToast();

  if (!channelId) {
    return <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">Select a channel to see its ideas.</p>;
  }

  const handleCreate = () => {
    recordTrend.mutate(
      { topic, source },
      {
        onSuccess: () => {
          toast.success("Trend recorded");
          setTopic("");
          setOpen(false);
        },
        onError: () => toast.error("Failed to record trend"),
      },
    );
  };

  const columns: Column<TrendRead>[] = [
    { header: "Topic", cell: (t) => t.topic },
    { header: "Source", cell: (t) => t.source },
    { header: "Score", cell: (t) => t.score.toFixed(1) },
    {
      header: "Link",
      cell: (t) =>
        t.url ? (
          <a href={t.url} target="_blank" rel="noreferrer" className="text-(--color-accent) dark:text-(--color-accent-dark)">
            Open
          </a>
        ) : null,
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-(--color-text) dark:text-(--color-text-dark)">Ideas</h1>
          <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
            Manual trend entry — automated discovery lands with the TrendAgent (Phase 6).
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
          <div className="flex justify-end">
            <Button isLoading={recordTrend.isPending} disabled={!topic} onClick={handleCreate}>
              Record
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
