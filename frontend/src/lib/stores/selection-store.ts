import { create } from "zustand";

/** Tracks which channel/project the dashboard is currently scoped to.
 * Most Phase-4 endpoints are channel- or project-scoped, so pages read
 * from here instead of each re-implementing a picker. */
type SelectionState = {
  channelId: string | null;
  projectId: string | null;
  setChannelId: (id: string | null) => void;
  setProjectId: (id: string | null) => void;
};

export const useSelectionStore = create<SelectionState>((set) => ({
  channelId: null,
  projectId: null,
  setChannelId: (id) => set({ channelId: id, projectId: null }),
  setProjectId: (id) => set({ projectId: id }),
}));
