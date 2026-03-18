/**
 * Canvas Learning System - Data Management Section
 * Story 1.3 AC-1 / Task 8: Data management placeholder buttons
 *
 * Provides placeholder buttons for:
 *   - Manual Backup (full implementation in Story 1.8)
 *   - Rebuild Index (full implementation in Story 2.7)
 *
 * [Source: Story 1.3 Task 8 — data management area placeholder]
 */

import { useState } from "react";
import { FolderArchive, RefreshCcw, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function DataManagementSection() {
  const [backupNotice, setBackupNotice] = useState<string | null>(null);
  const [rebuildNotice, setRebuildNotice] = useState<string | null>(null);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <FolderArchive className="h-5 w-5 text-[var(--ctp-peach)]" />
          <CardTitle className="text-lg">Data Management</CardTitle>
        </div>
        <CardDescription>Backup and index management</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Manual Backup */}
        <div className="flex items-center justify-between rounded-lg border border-[var(--border)] px-4 py-3">
          <div>
            <div className="text-sm font-medium">Manual Backup</div>
            <div className="text-xs text-[var(--muted-foreground)]">
              Create a backup of all learning data
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setBackupNotice(
                "Backup functionality will be available in Story 1.8"
              );
              setTimeout(() => setBackupNotice(null), 4000);
            }}
          >
            Backup
          </Button>
        </div>
        {backupNotice && (
          <div className="flex items-center gap-2 rounded-md bg-[var(--muted)] px-3 py-2 text-xs text-[var(--muted-foreground)]">
            <Info className="h-3 w-3 shrink-0" />
            {backupNotice}
          </div>
        )}

        {/* Rebuild Index */}
        <div className="flex items-center justify-between rounded-lg border border-[var(--border)] px-4 py-3">
          <div>
            <div className="text-sm font-medium">Rebuild Index</div>
            <div className="text-xs text-[var(--muted-foreground)]">
              Re-index all canvas files for search
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setRebuildNotice(
                "Index rebuild will be available in Story 2.7"
              );
              setTimeout(() => setRebuildNotice(null), 4000);
            }}
          >
            <RefreshCcw className="h-4 w-4" />
            Rebuild
          </Button>
        </div>
        {rebuildNotice && (
          <div className="flex items-center gap-2 rounded-md bg-[var(--muted)] px-3 py-2 text-xs text-[var(--muted-foreground)]">
            <Info className="h-3 w-3 shrink-0" />
            {rebuildNotice}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
