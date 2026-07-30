"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { FieldError, Input, Label, Textarea } from "@/components/ui/Input";

type Section = { key: string; value: string };

function sectionsToList(sections: Record<string, unknown>): Section[] {
  return Object.entries(sections).map(([key, value]) => ({
    key,
    value: typeof value === "string" ? value : JSON.stringify(value, null, 2),
  }));
}

function listToSections(list: Section[]): Record<string, string> {
  return Object.fromEntries(list.filter((s) => s.key.trim() !== "").map((s) => [s.key, s.value]));
}

type Props = {
  initialSections: Record<string, unknown>;
  onSave: (sections: Record<string, string>) => void;
  isSaving?: boolean;
};

/** `Script.sections` is a free-form JSON object on the backend (hook, body,
 * cta, …) — this edits it as a list of named text blocks rather than a raw
 * JSON textarea, since that's how the seed data and WriterAgent output
 * (Phase 6) both shape it. */
export function ScriptSectionsEditor({ initialSections, onSave, isSaving }: Props) {
  const [sections, setSections] = useState<Section[]>(() => {
    const list = sectionsToList(initialSections);
    return list.length > 0 ? list : [{ key: "hook", value: "" }];
  });
  const [error, setError] = useState<string>();

  const updateSection = (index: number, patch: Partial<Section>) => {
    setSections((prev) => prev.map((s, i) => (i === index ? { ...s, ...patch } : s)));
  };

  const removeSection = (index: number) => {
    setSections((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSave = () => {
    const keys = sections.map((s) => s.key.trim()).filter(Boolean);
    if (new Set(keys).size !== keys.length) {
      setError("Section names must be unique.");
      return;
    }
    setError(undefined);
    onSave(listToSections(sections));
  };

  return (
    <div className="flex flex-col gap-4">
      {sections.map((section, index) => (
        <div key={index} className="rounded-md border border-(--color-border) p-3 dark:border-(--color-border-dark)">
          <div className="mb-2 flex items-center gap-2">
            <Label htmlFor={`section-key-${index}`} className="mb-0 shrink-0">
              Name
            </Label>
            <Input
              id={`section-key-${index}`}
              value={section.key}
              onChange={(e) => updateSection(index, { key: e.target.value })}
              placeholder="hook / body / cta"
            />
            <Button variant="ghost" size="sm" onClick={() => removeSection(index)}>
              Remove
            </Button>
          </div>
          <Textarea
            value={section.value}
            onChange={(e) => updateSection(index, { value: e.target.value })}
            rows={4}
          />
        </div>
      ))}
      <FieldError>{error}</FieldError>
      <div className="flex justify-between">
        <Button variant="secondary" onClick={() => setSections((prev) => [...prev, { key: "", value: "" }])}>
          Add section
        </Button>
        <Button isLoading={isSaving} onClick={handleSave}>
          Save new version
        </Button>
      </div>
    </div>
  );
}
