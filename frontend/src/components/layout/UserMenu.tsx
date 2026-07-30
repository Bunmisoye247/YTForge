"use client";

import { useRouter } from "next/navigation";
import { useAuth, useLogoutMutation } from "@/lib/hooks/use-auth";
import { Button } from "@/components/ui/Button";

function initials(email: string): string {
  const local = email.split("@")[0] ?? "";
  const parts = local.split(/[._-]/).filter(Boolean);
  const chars = parts.length > 1 ? [parts[0]![0], parts[1]![0]] : [local[0], local[1]];
  return chars.filter(Boolean).join("").toUpperCase() || "?";
}

export function UserMenu() {
  const { user } = useAuth();
  const logout = useLogoutMutation();
  const router = useRouter();

  if (!user) return null;

  return (
    <div className="flex items-center gap-3">
      <span className="hidden text-sm text-(--color-text-muted) sm:inline dark:text-(--color-text-muted-dark)">
        {user.email}
      </span>
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-(--color-info) to-purple-500 text-xs font-semibold text-white dark:from-(--color-info-dark)">
        {initials(user.email)}
      </div>
      <Button
        variant="ghost"
        size="sm"
        isLoading={logout.isPending}
        onClick={() => logout.mutate(undefined, { onSuccess: () => router.push("/login") })}
      >
        Log out
      </Button>
    </div>
  );
}
