"use client";

import { useState } from "react";
import { useCreatePromptVersion } from "@/lib/hooks/use-prompts";
import { useToast } from "@/lib/stores/toast-store";
import { Button } from "@/components/ui/Button";
import { Input, Label, Textarea } from "@/components/ui/Input";

/** Prompt versions are never edited in place on the backend (see
 * CLAUDE.md conventions) — this form always creates the next version. */
export function PromptVersionEditor() {
  const [agent, setAgent] = useState("");
  const [name, setName] = useState("");
  const [content, setContent] = useState("");
  const create = useCreatePromptVersion();
  const toast = useToast();

  const handleSubmit = () => {
    create.mutate(
      { agent, name, content },
      {
        onSuccess: () => {
          toast.success("Prompt version created");
          setContent("");
        },
        onError: () => toast.error("Failed to create prompt version"),
      },
    );
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label htmlFor="prompt-agent">Agent</Label>
          <Input id="prompt-agent" value={agent} onChange={(e) => setAgent(e.target.value)} placeholder="writer" />
        </div>
        <div>
          <Label htmlFor="prompt-name">Name</Label>
          <Input id="prompt-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="video_script" />
        </div>
      </div>
      <div>
        <Label htmlFor="prompt-content">Content (Jinja2 template)</Label>
        <Textarea id="prompt-content" value={content} onChange={(e) => setContent(e.target.value)} rows={8} />
      </div>
      <div className="flex justify-end">
        <Button
          isLoading={create.isPending}
          disabled={!agent || !name || !content}
          onClick={handleSubmit}
        >
          Create version
        </Button>
      </div>
    </div>
  );
}
