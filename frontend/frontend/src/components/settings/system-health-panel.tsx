/**
 * Canvas Learning System - System Health Panel
 * Story 1.3 AC-2: System health status panel (5 components)
 *
 * Displays status indicators for Docker, Backend API, Neo4j, LLM API, and LanceDB.
 * Each component shows green (healthy), yellow (starting), or red (unreachable).
 * Provides a "Refresh" button to re-check all statuses.
 *
 * [Source: Story 1.3 Task 2 — system health status area]
 * [Source: backend/app/api/v1/system.py — GET /api/v1/system/health]
 */

import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Server,
  Database,
  Brain,
  HardDrive,
  Container,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getApiClient } from "@/lib/api-client";
import type { ComponentStatus } from "@/types/api";

/** All 5 monitored system components. */
const SYSTEM_COMPONENTS = [
  "Docker",
  "Backend API",
  "Neo4j",
  "LLM API",
  "LanceDB",
] as const;

type SystemComponent = (typeof SYSTEM_COMPONENTS)[number];

interface ComponentHealth {
  name: SystemComponent;
  status: "healthy" | "unhealthy" | "unknown" | "checking";
  message: string;
}

/** Map component name to an icon. */
function ComponentIcon({ name }: { name: SystemComponent }) {
  const iconClass = "h-4 w-4";
  switch (name) {
    case "Docker":
      return <Container className={iconClass} />;
    case "Backend API":
      return <Server className={iconClass} />;
    case "Neo4j":
      return <Database className={iconClass} />;
    case "LLM API":
      return <Brain className={iconClass} />;
    case "LanceDB":
      return <HardDrive className={iconClass} />;
  }
}

/** Map status to a badge variant and icon. */
function StatusBadge({ status }: { status: ComponentHealth["status"] }) {
  switch (status) {
    case "healthy":
      return (
        <Badge variant="healthy" className="gap-1">
          <CheckCircle2 className="h-3 w-3" />
          Healthy
        </Badge>
      );
    case "unhealthy":
      return (
        <Badge variant="error" className="gap-1">
          <XCircle className="h-3 w-3" />
          Unreachable
        </Badge>
      );
    case "unknown":
      return (
        <Badge variant="warning" className="gap-1">
          <AlertCircle className="h-3 w-3" />
          Unknown
        </Badge>
      );
    case "checking":
      return (
        <Badge variant="secondary" className="gap-1">
          <RefreshCw className="h-3 w-3 animate-spin" />
          Checking...
        </Badge>
      );
  }
}

/** Create default "checking" state for all components. */
function createCheckingState(): ComponentHealth[] {
  return SYSTEM_COMPONENTS.map((name) => ({
    name,
    status: "checking" as const,
    message: "",
  }));
}

/** Create "all unreachable" state when backend is down. */
function createUnreachableState(): ComponentHealth[] {
  return SYSTEM_COMPONENTS.map((name) => ({
    name,
    status: "unhealthy" as const,
    message: "Backend unreachable",
  }));
}

export function SystemHealthPanel() {
  const [components, setComponents] =
    useState<ComponentHealth[]>(createCheckingState());
  const [refreshing, setRefreshing] = useState(false);

  const refreshHealth = useCallback(async () => {
    setRefreshing(true);
    setComponents(createCheckingState());

    const client = getApiClient();
    const health = await client.checkHealth();

    if (!health) {
      // Backend unreachable — all red (AC-2, Task 2.5)
      setComponents(createUnreachableState());
      setRefreshing(false);
      return;
    }

    // Backend is reachable => Docker and Backend API are healthy
    const componentMap = new Map<string, ComponentStatus>();
    for (const c of health.components) {
      componentMap.set(c.name, c);
    }

    const neo4j = componentMap.get("neo4j");
    const ollama = componentMap.get("ollama");
    const lancedb = componentMap.get("lancedb");

    const result: ComponentHealth[] = [
      {
        name: "Docker",
        status: "healthy",
        message: "Running",
      },
      {
        name: "Backend API",
        status: "healthy",
        message: "Connected",
      },
      {
        name: "Neo4j",
        status: (neo4j?.status as ComponentHealth["status"]) ?? "unknown",
        message: neo4j?.message ?? "",
      },
      {
        name: "LLM API",
        status: (ollama?.status as ComponentHealth["status"]) ?? "unknown",
        message: ollama?.message ?? "",
      },
      {
        name: "LanceDB",
        status: (lancedb?.status as ComponentHealth["status"]) ?? "unknown",
        message: lancedb?.message ?? "",
      },
    ];

    setComponents(result);
    setRefreshing(false);
  }, []);

  // Initial fetch on mount
  useEffect(() => {
    refreshHealth();
  }, [refreshHealth]);

  const overallHealthy = components.every((c) => c.status === "healthy");
  const anyUnhealthy = components.some((c) => c.status === "unhealthy");

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-[var(--primary)]" />
            <CardTitle className="text-lg">System Status</CardTitle>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={refreshHealth}
            disabled={refreshing}
          >
            <RefreshCw
              className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
        </div>
        <CardDescription>
          {overallHealthy
            ? "All systems operational"
            : anyUnhealthy
              ? "Some components are unreachable"
              : "Checking system status..."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {components.map((comp) => (
            <div
              key={comp.name}
              className="flex items-center justify-between rounded-lg border border-[var(--border)] px-4 py-3"
            >
              <div className="flex items-center gap-3">
                <ComponentIcon name={comp.name} />
                <div>
                  <div className="text-sm font-medium">{comp.name}</div>
                  {comp.message && (
                    <div className="text-xs text-[var(--muted-foreground)]">
                      {comp.message}
                    </div>
                  )}
                </div>
              </div>
              <StatusBadge status={comp.status} />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
