// Centralized query-key factories so mutations know exactly what to
// invalidate without every hook file guessing at another's key shape.
export const queryKeys = {
  me: ["me"] as const,
  channels: {
    mine: ["channels", "mine"] as const,
  },
  projects: {
    list: (channelId: string) => ["projects", "list", channelId] as const,
  },
  trends: {
    list: (channelId: string) => ["trends", "list", channelId] as const,
  },
  research: {
    list: (projectId: string) => ["research", "list", projectId] as const,
  },
  scripts: {
    list: (projectId: string) => ["scripts", "list", projectId] as const,
    factChecks: (scriptId: string) => ["scripts", "fact-checks", scriptId] as const,
  },
  storyboards: {
    detail: (projectId: string) => ["storyboards", "detail", projectId] as const,
    scenes: (storyboardId: string) => ["storyboards", "scenes", storyboardId] as const,
  },
  assets: {
    list: (projectId: string) => ["assets", "list", projectId] as const,
  },
  voice: {
    profiles: (channelId: string) => ["voice", "profiles", channelId] as const,
    voiceovers: (projectId: string) => ["voice", "voiceovers", projectId] as const,
  },
  videos: {
    list: (projectId: string) => ["videos", "list", projectId] as const,
    analytics: (videoId: string) => ["videos", "analytics", videoId] as const,
    seo: (videoId: string) => ["videos", "seo", videoId] as const,
  },
  prompts: {
    templates: ["prompts", "templates"] as const,
    versions: (templateId: string) => ["prompts", "versions", templateId] as const,
  },
  approvals: {
    list: (status?: string) => ["approvals", "list", status ?? "all"] as const,
  },
  pipelines: {
    list: (projectId?: string) => ["pipelines", "list", projectId ?? "all"] as const,
    detail: (jobId: string) => ["pipelines", "detail", jobId] as const,
  },
  models: {
    list: ["models", "list"] as const,
  },
  settings: {
    effective: ["settings", "effective"] as const,
  },
};
