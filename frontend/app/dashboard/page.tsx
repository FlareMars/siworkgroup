"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store/auth-store";
import { useClawsQuery } from "@/lib/hooks/use-claws";

export default function DashboardPage() {
  const router = useRouter();
  const { accessToken } = useAuthStore();
  const { data, isLoading, error } = useClawsQuery();

  useEffect(() => {
    if (!accessToken) {
      router.push("/login");
    }
  }, [accessToken, router]);

  if (!accessToken) return null;

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Manage your OpenClaw instances</p>
        </div>
        <button
          onClick={() => router.push("/claws/new")}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          + New Claw
        </button>
      </div>

      {isLoading && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-32 animate-pulse rounded-xl border bg-muted"
            />
          ))}
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
          Failed to load Claws. Please try again.
        </div>
      )}

      {data && data.items.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed py-20 text-center">
          <p className="text-2xl">🦾</p>
          <h3 className="mt-2 text-lg font-semibold">No Claws yet</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Create your first OpenClaw instance to get started
          </p>
          <button
            onClick={() => router.push("/claws/new")}
            className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Create Claw
          </button>
        </div>
      )}

      {data && data.items.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data.items.map((claw) => (
            <div
              key={claw.id}
              onClick={() => router.push(`/claws/${claw.id}/chat`)}
              className="cursor-pointer rounded-xl border bg-card p-5 shadow-sm transition-shadow hover:shadow-md"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold">{claw.name}</h3>
                  {claw.description && (
                    <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                      {claw.description}
                    </p>
                  )}
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    claw.status === "running"
                      ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                      : claw.status === "error"
                        ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                        : "bg-muted text-muted-foreground"
                  }`}
                >
                  {claw.status}
                </span>
              </div>
              <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                <span>Model: {claw.model}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}