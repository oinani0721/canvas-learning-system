/**
 * Canvas Learning System - Usage Statistics Section
 * Story 3.12: Token Tracking & Cost Statistics
 *
 * Displays LLM usage statistics: total calls, tokens, cost, latency,
 * success rate, and per-task-type breakdown. Supports period filtering
 * (Today / Week / Month).
 *
 * [Source: Story 3.12 Task 3 — Cost Tracker UI Component]
 * [Source: backend/app/api/v1/system.py — GET /api/v1/system/llm-stats]
 */

import { useCallback, useEffect, useState } from "react";
import {
  BarChart3,
  RefreshCw,
  Coins,
  Zap,
  CheckCircle2,
  Clock,
  Hash,
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
import type { LlmStatsResponse, TaskTypeStats } from "@/types/api";

/** Available time periods for stats filtering. */
const PERIODS = [
  { value: "today" as const, label: "Today" },
  { value: "week" as const, label: "Week" },
  { value: "month" as const, label: "Month" },
];

/** Task type display labels. */
const TASK_TYPE_LABELS: Record<string, string> = {
  conversation: "Conversation",
  scoring: "Scoring",
  extraction: "Extraction",
  indexing: "Indexing",
  qa_check: "QA Check",
  qaCheck: "QA Check",
};

/** Format a number with locale-aware separators. */
function formatNumber(n: number): string {
  return n.toLocaleString();
}

/** Format cost in USD with 4 decimal places. */
function formatCost(usd: number): string {
  return `$${usd.toFixed(4)}`;
}

/** Format latency in ms with 1 decimal place. */
function formatLatency(ms: number): string {
  return `${ms.toFixed(1)} ms`;
}

/** Format success rate as percentage. */
function formatRate(rate: number): string {
  return `${(rate * 100).toFixed(1)}%`;
}

export function UsageStatisticsSection() {
  const [stats, setStats] = useState<LlmStatsResponse | null>(null);
  const [period, setPeriod] = useState<"today" | "week" | "month">("today");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(
    async (selectedPeriod: "today" | "week" | "month") => {
      setLoading(true);
      setError(null);

      const client = getApiClient();
      const result = await client.getLlmStats(selectedPeriod);

      if (result) {
        setStats(result);
      } else {
        setError("Backend unreachable");
      }
      setLoading(false);
    },
    []
  );

  // Fetch on mount and when period changes
  useEffect(() => {
    fetchStats(period);
  }, [period, fetchStats]);

  const summary = stats?.data?.summary;
  const byTask = stats?.data?.byTask ?? [];

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-[var(--primary)]" />
            <CardTitle className="text-lg">Usage Statistics</CardTitle>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchStats(period)}
            disabled={loading}
          >
            <RefreshCw
              className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
        </div>
        <CardDescription>
          LLM token consumption and cost tracking
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Period selector */}
        <div className="flex gap-2">
          {PERIODS.map((p) => (
            <Button
              key={p.value}
              variant={period === p.value ? "default" : "outline"}
              size="sm"
              onClick={() => setPeriod(p.value)}
              disabled={loading}
            >
              {p.label}
            </Button>
          ))}
        </div>

        {/* Loading state */}
        {loading && (
          <div className="py-8 text-center text-sm text-[var(--muted-foreground)]">
            Loading statistics...
          </div>
        )}

        {/* Error state */}
        {error && !loading && (
          <div className="py-8 text-center text-sm text-[var(--destructive)]">
            {error}
          </div>
        )}

        {/* Summary cards */}
        {summary && !loading && (
          <>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {/* Total calls */}
              <div className="rounded-lg border border-[var(--border)] p-3">
                <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
                  <Hash className="h-3 w-3" />
                  Total Calls
                </div>
                <div className="mt-1 text-xl font-bold">
                  {formatNumber(summary.totalCalls)}
                </div>
              </div>

              {/* Total tokens */}
              <div className="rounded-lg border border-[var(--border)] p-3">
                <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
                  <Zap className="h-3 w-3" />
                  Total Tokens
                </div>
                <div className="mt-1 text-xl font-bold">
                  {formatNumber(summary.totalTokens)}
                </div>
                <div className="text-xs text-[var(--muted-foreground)]">
                  {formatNumber(summary.totalInputTokens)} in /{" "}
                  {formatNumber(summary.totalOutputTokens)} out
                </div>
              </div>

              {/* Total cost */}
              <div className="rounded-lg border border-[var(--border)] p-3">
                <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
                  <Coins className="h-3 w-3" />
                  Est. Cost
                </div>
                <div className="mt-1 text-xl font-bold">
                  {formatCost(summary.totalCostUsd)}
                </div>
              </div>

              {/* Average latency */}
              <div className="rounded-lg border border-[var(--border)] p-3">
                <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
                  <Clock className="h-3 w-3" />
                  Avg Latency
                </div>
                <div className="mt-1 text-xl font-bold">
                  {formatLatency(summary.avgLatencyMs)}
                </div>
              </div>

              {/* Success rate */}
              <div className="rounded-lg border border-[var(--border)] p-3">
                <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
                  <CheckCircle2 className="h-3 w-3" />
                  Success Rate
                </div>
                <div className="mt-1 text-xl font-bold">
                  {formatRate(summary.successRate)}
                </div>
              </div>
            </div>

            {/* Per-task breakdown */}
            {byTask.length > 0 && (
              <div className="space-y-2">
                <div className="text-sm font-medium">By Task Type</div>
                <div className="space-y-2">
                  {byTask.map((task: TaskTypeStats) => (
                    <div
                      key={task.taskType}
                      className="flex items-center justify-between rounded-lg border border-[var(--border)] px-4 py-2"
                    >
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">
                          {TASK_TYPE_LABELS[task.taskType] ?? task.taskType}
                        </Badge>
                      </div>
                      <div className="flex gap-4 text-xs text-[var(--muted-foreground)]">
                        <span>{formatNumber(task.calls)} calls</span>
                        <span>{formatNumber(task.tokens)} tokens</span>
                        <span>{formatCost(task.costUsd)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Empty state */}
            {summary.totalCalls === 0 && (
              <div className="py-4 text-center text-sm text-[var(--muted-foreground)]">
                No LLM calls recorded for this period.
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
