/**
 * Canvas Learning System - Embedding Model Status (Read-only)
 * Story 1.3 AC-5: Embedding model read-only status display
 *
 * Shows the bge-m3 / Ollama embedding model status.
 * This is read-only — the user cannot modify the embedding model config.
 * Status is derived from the health check endpoint (Ollama component).
 *
 * [Source: Story 1.3 Task 5 — embedding model status area]
 */

import { useCallback, useEffect, useState } from "react";
import { Cpu, CheckCircle2, XCircle, RefreshCw } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getApiClient } from "@/lib/api-client";

type EmbeddingStatus = "healthy" | "unhealthy" | "checking";

export function EmbeddingStatusSection() {
  const [status, setStatus] = useState<EmbeddingStatus>("checking");

  const checkStatus = useCallback(async () => {
    setStatus("checking");
    const client = getApiClient();
    const health = await client.checkHealth();

    if (!health) {
      setStatus("unhealthy");
      return;
    }

    const ollama = health.components.find((c) => c.name === "ollama");
    setStatus(ollama?.status === "healthy" ? "healthy" : "unhealthy");
  }, []);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-[var(--ctp-teal)]" />
            <CardTitle className="text-lg">Embedding Model</CardTitle>
          </div>
          <Button variant="ghost" size="icon" onClick={checkStatus}>
            <RefreshCw
              className={`h-4 w-4 ${status === "checking" ? "animate-spin" : ""}`}
            />
          </Button>
        </div>
        <CardDescription>
          Fixed embedding model for vector indexing (read-only)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between rounded-lg border border-[var(--border)] px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="text-sm">
              <span className="font-medium">bge-m3</span>
              <span className="mx-2 text-[var(--muted-foreground)]">
                &middot;
              </span>
              <span className="text-[var(--muted-foreground)]">Ollama</span>
            </div>
          </div>
          {status === "checking" ? (
            <Badge variant="secondary" className="gap-1">
              <RefreshCw className="h-3 w-3 animate-spin" />
              Checking
            </Badge>
          ) : status === "healthy" ? (
            <Badge variant="healthy" className="gap-1">
              <CheckCircle2 className="h-3 w-3" />
              Ready
            </Badge>
          ) : (
            <Badge variant="error" className="gap-1">
              <XCircle className="h-3 w-3" />
              Not Ready
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
