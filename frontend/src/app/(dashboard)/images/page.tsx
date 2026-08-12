"use client";

import { useSelectionStore } from "@/lib/stores/selection-store";
import { CreateImagePanel } from "@/components/editors/CreateImagePanel";
import { AssetGallery } from "@/components/editors/AssetGallery";
import { AssetType } from "@/types/enums";

export default function ImagesPage() {
  const { projectId } = useSelectionStore();

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold text-(--color-text) dark:text-(--color-text-dark)">Images</h1>
      {!projectId ? (
        <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">Select a project.</p>
      ) : (
        <>
          <CreateImagePanel projectId={projectId} />
          <AssetGallery projectId={projectId} types={[AssetType.IMAGE, AssetType.THUMBNAIL]} />
        </>
      )}
    </div>
  );
}
