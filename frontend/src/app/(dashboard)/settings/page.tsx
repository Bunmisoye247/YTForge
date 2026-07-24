"use client";

import { useState } from "react";
import { useEffectiveSettings } from "@/lib/hooks/use-settings";
import { useModels, useRegisterModel, useUpdateModelStatus } from "@/lib/hooks/use-models";
import { usePromptTemplates } from "@/lib/hooks/use-prompts";
import { useToast } from "@/lib/stores/toast-store";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { Input, Label } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { PromptVersionEditor } from "@/components/editors/PromptVersionEditor";
import { ModelAvailability, ModelCapability } from "@/types/enums";

function EffectiveSettingsCard() {
  const { data } = useEffectiveSettings();
  if (!data) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Effective configuration</CardTitle>
      </CardHeader>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        <dt className="text-[--color-text-muted] dark:text-[--color-text-muted-dark]">Environment</dt>
        <dd className="text-[--color-text] dark:text-[--color-text-dark]">{data.app.env}</dd>
        <dt className="text-[--color-text-muted] dark:text-[--color-text-muted-dark]">Debug</dt>
        <dd className="text-[--color-text] dark:text-[--color-text-dark]">{String(data.app.debug)}</dd>
        <dt className="text-[--color-text-muted] dark:text-[--color-text-muted-dark]">Database host</dt>
        <dd className="text-[--color-text] dark:text-[--color-text-dark]">{data.database.host}:{data.database.port}</dd>
        <dt className="text-[--color-text-muted] dark:text-[--color-text-muted-dark]">Access token TTL</dt>
        <dd className="text-[--color-text] dark:text-[--color-text-dark]">{data.security.access_token_ttl_minutes} min</dd>
      </dl>
    </Card>
  );
}

function ModelRegistryCard() {
  const { data: models, isLoading } = useModels();
  const registerModel = useRegisterModel();
  const updateStatus = useUpdateModelStatus();
  const toast = useToast();

  const [open, setOpen] = useState(false);
  const [provider, setProvider] = useState("");
  const [modelName, setModelName] = useState("");
  const [capability, setCapability] = useState<ModelCapability>(ModelCapability.LLM);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Model registry</CardTitle>
        <Button size="sm" onClick={() => setOpen(true)}>
          Register model
        </Button>
      </CardHeader>
      {isLoading ? (
        <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">Loading…</p>
      ) : (
        <div className="flex flex-col gap-2">
          {models?.map((m) => (
            <div key={m.id} className="flex items-center justify-between text-sm">
              <span className="text-[--color-text] dark:text-[--color-text-dark]">
                {m.provider}/{m.model_name} <span className="text-[--color-text-muted] dark:text-[--color-text-muted-dark]">({m.capability})</span>
              </span>
              <button
                onClick={() =>
                  updateStatus.mutate({
                    entryId: m.id,
                    data: {
                      status:
                        m.status === ModelAvailability.AVAILABLE
                          ? ModelAvailability.UNAVAILABLE
                          : ModelAvailability.AVAILABLE,
                    },
                  })
                }
              >
                <StatusBadge status={m.status} />
              </button>
            </div>
          ))}
          {models?.length === 0 && (
            <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">No models registered yet.</p>
          )}
        </div>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} title="Register model">
        <div className="flex flex-col gap-3">
          <div>
            <Label htmlFor="model-provider">Provider</Label>
            <Input id="model-provider" value={provider} onChange={(e) => setProvider(e.target.value)} placeholder="anthropic" />
          </div>
          <div>
            <Label htmlFor="model-name">Model name</Label>
            <Input id="model-name" value={modelName} onChange={(e) => setModelName(e.target.value)} placeholder="claude-sonnet-4-6" />
          </div>
          <div>
            <Label htmlFor="model-capability">Capability</Label>
            <Select id="model-capability" value={capability} onChange={(e) => setCapability(e.target.value as ModelCapability)}>
              {Object.values(ModelCapability).map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex justify-end">
            <Button
              isLoading={registerModel.isPending}
              disabled={!provider || !modelName}
              onClick={() =>
                registerModel.mutate(
                  { provider, model_name: modelName, capability },
                  {
                    onSuccess: () => {
                      toast.success("Model registered");
                      setProvider("");
                      setModelName("");
                      setOpen(false);
                    },
                    onError: () => toast.error("Failed to register model"),
                  },
                )
              }
            >
              Register
            </Button>
          </div>
        </div>
      </Dialog>
    </Card>
  );
}

function PromptTemplatesCard() {
  const { data: templates, isLoading } = usePromptTemplates();
  return (
    <Card>
      <CardHeader>
        <CardTitle>Prompt templates</CardTitle>
      </CardHeader>
      {isLoading ? (
        <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">Loading…</p>
      ) : (
        <div className="mb-4 flex flex-col gap-1">
          {templates?.map((t) => (
            <div key={t.id} className="text-sm text-[--color-text] dark:text-[--color-text-dark]">
              {t.agent} / {t.name}
            </div>
          ))}
          {templates?.length === 0 && (
            <p className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">No prompt templates yet.</p>
          )}
        </div>
      )}
      <PromptVersionEditor />
    </Card>
  );
}

export default function SettingsPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold text-[--color-text] dark:text-[--color-text-dark]">Settings</h1>
      <EffectiveSettingsCard />
      <ModelRegistryCard />
      <PromptTemplatesCard />
    </div>
  );
}
