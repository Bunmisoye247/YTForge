"use client";

import { useRouter } from "next/navigation";
import { useAuth, useLogoutMutation } from "@/lib/hooks/use-auth";
import { Button } from "@/components/ui/Button";

export function UserMenu() {
  const { user } = useAuth();
  const logout = useLogoutMutation();
  const router = useRouter();

  if (!user) return null;

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">{user.email}</span>
      <Button
        variant="secondary"
        size="sm"
        isLoading={logout.isPending}
        onClick={() => logout.mutate(undefined, { onSuccess: () => router.push("/login") })}
      >
        Log out
      </Button>
    </div>
  );
}
