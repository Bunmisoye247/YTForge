"use client";

import { useState } from "react";
import { useMyChannels, useCreateChannel } from "@/lib/hooks/use-channels";
import { useToast } from "@/lib/stores/toast-store";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { Input, Label } from "@/components/ui/Input";

export default function ChannelsPage() {
  const { data: channels, isLoading } = useMyChannels();
  const createChannel = useCreateChannel();
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");

  const handleCreate = () => {
    createChannel.mutate(
      { name },
      {
        onSuccess: () => {
          toast.success("Channel created");
          setName("");
          setOpen(false);
        },
        onError: () => toast.error("Failed to create channel"),
      },
    );
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[--color-text] dark:text-[--color-text-dark]">Channels</h1>
        <Button onClick={() => setOpen(true)}>New channel</Button>
      </div>

      {isLoading ? (
        <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">Loading…</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {channels?.map((channel) => (
            <Card key={channel.id}>
              <div className="font-medium text-[--color-text] dark:text-[--color-text-dark]">{channel.name}</div>
              {channel.youtube_channel_id && (
                <div className="mt-1 text-xs text-[--color-text-muted] dark:text-[--color-text-muted-dark]">
                  YouTube: {channel.youtube_channel_id}
                </div>
              )}
            </Card>
          ))}
          {channels?.length === 0 && (
            <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">No channels yet.</p>
          )}
        </div>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} title="New channel">
        <div className="flex flex-col gap-3">
          <div>
            <Label htmlFor="channel-name">Name</Label>
            <Input id="channel-name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="flex justify-end">
            <Button isLoading={createChannel.isPending} disabled={!name} onClick={handleCreate}>
              Create
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
