"use client";

import { useState } from "react";
import { useAssets, useMarkAssetFailed, useMarkAssetReady, useRegisterAsset, useRequestAssetDeletion } from "@/lib/hooks/use-assets";
import { useToast } from "@/lib/stores/toast-store";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { Input, Label } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { AssetStatus, AssetType } from "@/types/enums";
import type { AssetRead } from "@/lib/api/schemas/assets";

type Props = {
  projectId: string;
  /** Restrict the gallery + register form to these asset types (e.g. the
   * Images page only shows AssetType.IMAGE/THUMBNAIL). */
  types: AssetType[];
};

export function AssetGallery({ projectId, types }: Props) {
  const { data: page, isLoading } = useAssets(projectId, { limit: 50 });
  const registerAsset = useRegisterAsset(projectId);
  const markReady = useMarkAssetReady(projectId);
  const markFailed = useMarkAssetFailed(projectId);
  const requestDeletion = useRequestAssetDeletion();
  const toast = useToast();

  const [open, setOpen] = useState(false);
  const [assetType, setAssetType] = useState<AssetType>(types[0]!);
  const [bucket, setBucket] = useState("raw-assets");
  const [objectKey, setObjectKey] = useState("");

  const assets = (page?.items ?? []).filter((a) => types.includes(a.asset_type));

  const handleRegister = () => {
    registerAsset.mutate(
      { asset_type: assetType, bucket, object_key: objectKey },
      {
        onSuccess: () => {
          toast.success("Asset registered");
          setObjectKey("");
          setOpen(false);
        },
        onError: () => toast.error("Failed to register asset"),
      },
    );
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-end">
        <Button onClick={() => setOpen(true)}>Register asset</Button>
      </div>

      {isLoading ? (
        <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">Loading…</p>
      ) : assets.length === 0 ? (
        <p className="text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">No assets yet.</p>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {assets.map((asset) => (
            <AssetCard
              key={asset.id}
              asset={asset}
              onMarkReady={() => markReady.mutate(asset.id, { onError: () => toast.error("Failed") })}
              onMarkFailed={() => markFailed.mutate(asset.id, { onError: () => toast.error("Failed") })}
              onRequestDeletion={() =>
                requestDeletion.mutate(asset.id, {
                  onSuccess: () => toast.success("Deletion approval requested"),
                  onError: () => toast.error("Failed to request deletion"),
                })
              }
            />
          ))}
        </div>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} title="Register asset">
        <div className="flex flex-col gap-3">
          <div>
            <Label htmlFor="asset-type">Type</Label>
            <Select id="asset-type" value={assetType} onChange={(e) => setAssetType(e.target.value as AssetType)}>
              {types.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="asset-bucket">Bucket</Label>
            <Input id="asset-bucket" value={bucket} onChange={(e) => setBucket(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="asset-key">Object key</Label>
            <Input id="asset-key" value={objectKey} onChange={(e) => setObjectKey(e.target.value)} placeholder="project/asset/file.png" />
          </div>
          <div className="flex justify-end">
            <Button isLoading={registerAsset.isPending} disabled={!objectKey} onClick={handleRegister}>
              Register
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}

function AssetCard({
  asset,
  onMarkReady,
  onMarkFailed,
  onRequestDeletion,
}: {
  asset: AssetRead;
  onMarkReady: () => void;
  onMarkFailed: () => void;
  onRequestDeletion: () => void;
}) {
  return (
    <Card>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-medium text-(--color-text) dark:text-(--color-text-dark)">{asset.asset_type}</span>
        <StatusBadge status={asset.status} />
      </div>
      <p className="mb-3 truncate text-xs text-(--color-text-muted) dark:text-(--color-text-muted-dark)" title={asset.object_key}>
        {asset.bucket}/{asset.object_key}
      </p>
      <div className="flex flex-wrap gap-2">
        {asset.status === AssetStatus.PENDING && (
          <>
            <Button size="sm" variant="secondary" onClick={onMarkReady}>
              Mark ready
            </Button>
            <Button size="sm" variant="secondary" onClick={onMarkFailed}>
              Mark failed
            </Button>
          </>
        )}
        {asset.status === AssetStatus.READY && (
          <Button size="sm" variant="danger" onClick={onRequestDeletion}>
            Request deletion
          </Button>
        )}
      </div>
    </Card>
  );
}
