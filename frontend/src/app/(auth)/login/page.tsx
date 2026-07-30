"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useLoginMutation } from "@/lib/hooks/use-auth";
import { ApiError } from "@/lib/api/errors";
import { Button } from "@/components/ui/Button";
import { FieldError, Input, Label } from "@/components/ui/Input";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string>();
  const login = useLoginMutation();
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(undefined);
    login.mutate(
      { email, password },
      {
        onSuccess: () => router.push("/overview"),
        onError: (err) => setError(err instanceof ApiError ? err.message : "Login failed"),
      },
    );
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <form onSubmit={handleSubmit} className="w-full max-w-sm rounded-lg border border-(--color-border) p-6 dark:border-(--color-border-dark)">
        <h1 className="mb-4 text-lg font-semibold text-(--color-text) dark:text-(--color-text-dark)">Log in to YTForge</h1>
        <div className="mb-3">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="mb-3">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <FieldError>{error}</FieldError>
        <Button type="submit" className="mt-2 w-full" isLoading={login.isPending}>
          Log in
        </Button>
        <p className="mt-4 text-center text-sm text-(--color-text-muted) dark:text-(--color-text-muted-dark)">
          No account? <Link href="/register" className="text-(--color-accent) dark:text-(--color-accent-dark)">Register</Link>
        </p>
      </form>
    </div>
  );
}
