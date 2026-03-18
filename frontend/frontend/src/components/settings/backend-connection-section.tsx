/**
 * Canvas Learning System - Backend Connection Section
 * Story 1.3 AC-7: Backend connection configuration
 *
 * Allows the user to configure:
 *   - Backend API address (default http://localhost:8001)
 *   - Neo4j address (default bolt://localhost:7689)
 *
 * Changes are persisted locally and used on next startup.
 *
 * [Source: Story 1.3 Task 7 — backend connection config area]
 */

import { Server } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface BackendConnectionSectionProps {
  backendUrl: string;
  neo4jUrl: string;
  onBackendUrlChange: (value: string) => void;
  onNeo4jUrlChange: (value: string) => void;
}

export function BackendConnectionSection({
  backendUrl,
  neo4jUrl,
  onBackendUrlChange,
  onNeo4jUrlChange,
}: BackendConnectionSectionProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Server className="h-5 w-5 text-[var(--ctp-sapphire)]" />
          <CardTitle className="text-lg">Backend Connection</CardTitle>
        </div>
        <CardDescription>
          Configure backend service addresses
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="backend-url">Backend API Address</Label>
          <Input
            id="backend-url"
            placeholder="http://localhost:8001"
            value={backendUrl}
            onChange={(e) => onBackendUrlChange(e.target.value)}
          />
          <p className="text-xs text-[var(--muted-foreground)]">
            FastAPI backend URL
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="neo4j-url">Neo4j Address</Label>
          <Input
            id="neo4j-url"
            placeholder="bolt://localhost:7689"
            value={neo4jUrl}
            onChange={(e) => onNeo4jUrlChange(e.target.value)}
          />
          <p className="text-xs text-[var(--muted-foreground)]">
            Neo4j Bolt connection URI
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
