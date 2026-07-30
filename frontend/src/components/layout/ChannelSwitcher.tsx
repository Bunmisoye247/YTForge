"use client";

import { useEffect } from "react";
import { useMyChannels } from "@/lib/hooks/use-channels";
import { useSelectionStore } from "@/lib/stores/selection-store";
import { Select } from "@/components/ui/Select";
import { SwitcherShell } from "@/components/layout/SwitcherShell";

export function ChannelSwitcher() {
  const { data: channels, isLoading } = useMyChannels();
  const { channelId, setChannelId } = useSelectionStore();

  useEffect(() => {
    if (!channelId && channels && channels.length > 0) {
      setChannelId(channels[0]!.id);
    }
  }, [channelId, channels, setChannelId]);

  if (isLoading) return null;
  if (!channels || channels.length === 0) {
    return (
      <SwitcherShell label="Channel">
        <span className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">No channels yet</span>
      </SwitcherShell>
    );
  }

  return (
    <SwitcherShell label="Channel">
      <Select
        bare
        value={channelId ?? ""}
        onChange={(e) => setChannelId(e.target.value || null)}
        aria-label="Select channel"
      >
        {channels.map((channel) => (
          <option key={channel.id} value={channel.id}>
            {channel.name}
          </option>
        ))}
      </Select>
    </SwitcherShell>
  );
}
