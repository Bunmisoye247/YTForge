"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useLoginMutation, useRegisterMutation } from "@/lib/hooks/use-auth";
import { ApiError } from "@/lib/api/errors";
import { Button } from "@/components/ui/Button";
import { FieldError, Input, Label } from "@/components/ui/Input";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string>();
  const register = useRegisterMutation();
  const login = useLoginMutation();
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(undefined);
    register.mutate(
      { email, password, full_name: fullName },
      {
        onSuccess: () => {
          login.mutate({ email, password }, { onSuccess: () => router.push("/overview") });
        },
        onError: (err) => setError(err instanceof ApiError ? err.message : "Registration failed"),
      },
    );
  };

  const isLoading = register.isPending || login.isPending;

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <form onSubmit={handleSubmit} className="w-full max-w-sm rounded-lg border border-[--color-border] p-6 dark:border-[--color-border-dark]">
        <h1 className="mb-4 text-lg font-semibold text-[--color-text] dark:text-[--color-text-dark]">Create your account</h1>
        <div className="mb-3">
          <Label htmlFor="full_name">Full name</Label>
          <Input id="full_name" required value={fullName} onChange={(e) => setFullName(e.target.value)} />
        </div>
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
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <FieldError>{error}</FieldError>
        <Button type="submit" className="mt-2 w-full" isLoading={isLoading}>
          Register
        </Button>
        <p className="mt-4 text-center text-sm text-[--color-text-muted] dark:text-[--color-text-muted-dark]">
          Already have an account? <Link href="/login" className="text-[--color-accent] dark:text-[--color-accent-dark]">Log in</Link>
        </p>
      </form>
    </div>
  );
}
