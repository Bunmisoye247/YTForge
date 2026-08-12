"use client";

import { useState, type ReactNode } from "react";
import { useGenerateProjectImage } from "@/lib/hooks/use-assets";
import { useToast } from "@/lib/stores/toast-store";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Input";
import { IconSparkle, IconImages, IconIdeas, IconVideos, IconChannels, IconAnalytics, IconSettings } from "@/components/ui/icons";
import { cn } from "@/lib/utils/cn";

type Preset = {
  label: string;
  prompt: string;
  icon: ReactNode;
  swatch: string;
};

// Real, functional starting points for this app's actual domain (YouTube
// content assets) — clicking one fills the prompt with editable text, not
// a static example photo (no fabricated "here's what you'll get" images).
const PRESETS: Preset[] = [
  {
    label: "Thumbnail",
    prompt: "Bold, high-contrast YouTube thumbnail, dramatic lighting, clear focal subject, room for title text",
    icon: <IconImages className="h-4 w-4" />,
    swatch: "bg-(--color-accent)/20 text-(--color-accent) dark:bg-(--color-accent-dark)/20 dark:text-(--color-accent-dark)",
  },
  {
    label: "Talking head",
    prompt: "Presenter speaking to camera in a well-lit home studio, friendly expression, shallow depth of field",
    icon: <IconChannels className="h-4 w-4" />,
    swatch: "bg-(--color-info)/20 text-(--color-info) dark:bg-(--color-info)/20 dark:text-(--color-info-dark)",
  },
  {
    label: "Product shot",
    prompt: "Clean product photography on a neutral background, soft studio lighting, subtle reflection",
    icon: <IconVideos className="h-4 w-4" />,
    swatch: "bg-(--color-success)/20 text-(--color-success) dark:bg-(--color-success)/20 dark:text-(--color-success-dark)",
  },
  {
    label: "B-roll",
    prompt: "Cinematic wide establishing shot, natural light, shallow depth of field, documentary style",
    icon: <IconAnalytics className="h-4 w-4" />,
    swatch: "bg-(--color-warning)/20 text-(--color-warning) dark:bg-(--color-warning)/20 dark:text-(--color-warning-dark)",
  },
  {
    label: "Diagram",
    prompt: "Clean, minimal explainer diagram, flat design, labeled arrows, high contrast on white background",
    icon: <IconIdeas className="h-4 w-4" />,
    swatch: "bg-(--color-info)/20 text-(--color-info) dark:bg-(--color-info)/20 dark:text-(--color-info-dark)",
  },
  {
    label: "Character",
    prompt: "Stylized character illustration, expressive pose, vibrant flat colors, simple background",
    icon: <IconSettings className="h-4 w-4" />,
    swatch: "bg-(--color-danger)/20 text-(--color-danger) dark:bg-(--color-danger)/20 dark:text-(--color-danger-dark)",
  },
];

export function CreateImagePanel({ projectId }: { projectId: string }) {
  const [prompt, setPrompt] = useState("");
  const generate = useGenerateProjectImage(projectId);
  const toast = useToast();

  const handleGenerate = () => {
    if (!prompt.trim()) return;
    generate.mutate(
      { prompt: prompt.trim() },
      {
        onSuccess: () => toast.success("Image generated"),
        onError: () => toast.error("Image generation failed"),
      },
    );
  };

  return (
    <Card className="flex flex-col items-center gap-6 py-10 text-center">
      <div className="flex flex-col items-center gap-3">
        <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-(--color-accent)/15 text-(--color-accent) dark:bg-(--color-accent-dark)/15 dark:text-(--color-accent-dark)">
          <IconSparkle className="h-5 w-5" />
        </span>
        <h2 className="font-display text-2xl font-semibold text-(--color-text) dark:text-(--color-text-dark)">
          Create images
        </h2>
        <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
          Describe what you need, or start from a preset below.
        </p>
      </div>

      <div className="w-full max-w-xl rounded-2xl border border-(--color-border) bg-(--color-bg) p-3 dark:border-(--color-border-dark) dark:bg-(--color-bg-dark)">
        <Textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe your image"
          rows={3}
          className="min-h-0 resize-none border-none bg-transparent p-1 focus:outline-none"
        />
        <div className="flex items-center justify-end border-t border-(--color-border) pt-2 dark:border-(--color-border-dark)">
          <Button size="sm" isLoading={generate.isPending} disabled={!prompt.trim()} onClick={handleGenerate}>
            Generate
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap justify-center gap-4">
        {PRESETS.map((preset) => (
          <button
            key={preset.label}
            type="button"
            onClick={() => setPrompt(preset.prompt)}
            className="flex w-20 flex-col items-center gap-1.5 text-center"
          >
            <span className={cn("flex h-14 w-14 items-center justify-center rounded-full", preset.swatch)}>
              {preset.icon}
            </span>
            <span className="text-xs font-medium text-(--color-text) dark:text-(--color-text-dark)">
              {preset.label}
            </span>
          </button>
        ))}
      </div>
    </Card>
  );
}
